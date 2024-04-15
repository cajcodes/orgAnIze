import os
import time
from pdf2image import convert_from_path
import pytesseract
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from concurrent.futures import ThreadPoolExecutor
import cv2
import numpy as np
import shutil
import sqlite3
from openai import OpenAI
import json

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Specify the full path including the .db file for the new database
database_path = '/data/docs.db'

def create_database(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create a table for categories
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE
        )
    ''')

    # Create a table for documents with a reference to categories
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY,
            category_id INTEGER,
            file_path TEXT,
            ocr_text TEXT,
            summary TEXT DEFAULT '',
            filename TEXT DEFAULT '',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
    ''')
    conn.commit()
    conn.close()

# Create the new database and table
create_database(database_path)

# At the top of your main.py or a similar file
HARDCODED_CATEGORIES = ["Invoices", "Reports", "Letters", "Work Orders", "Receipts", "Contracts", "Manuals", "Marketing"]

def check_hardcoded_categories(document_text):
    category_keywords = {
        "Invoices": ["invoice", "bill", "payment due", "amount due", "invoice number"],
        "Reports": ["report", "analysis", "summary", "quarterly", "annual report"],
        "Letters": ["dear", "sincerely", "regards", "yours truly", "to whom it may concern"],
        "Work Orders": ["work order", "job order", "service order", "maintenance request", "order number"],
        "Receipts": ["receipt", "proof of purchase", "transaction", "total amount", "sales receipt"],
        "Contracts": ["contract", "agreement", "binding", "terms and conditions", "contractual"],
        "Manuals": ["manual", "instruction", "guide", "handbook", "how to"],
        "Marketing": ["marketing", "promotion", "advertise", "campaign", "branding"]
    }

    lower_text = document_text.lower()
    for category, keywords in category_keywords.items():
        if any(keyword in lower_text for keyword in keywords):
            return category

    return None

class Watcher:
    def __init__(self, directory_to_watch):
        self.observer = Observer()
        self.directory_to_watch = directory_to_watch

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.directory_to_watch, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            print("Observer Stopped")

        self.observer.join()


class Handler(FileSystemEventHandler):
    @staticmethod
    def on_any_event(event):
        if event.is_directory or not event.event_type == 'created':
            return None

        if event.src_path.endswith('.pdf'):
            print(f"Processing file: {event.src_path}")
            # Pass database_path here
            perform_ocr(database_path, event.src_path)

def preprocess_image(page):
    # Convert to grayscale for better accuracy
    gray = cv2.cvtColor(np.array(page), cv2.COLOR_BGR2GRAY)

    # Apply thresholding
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return thresh

def perform_ocr_on_page(page):
    preprocessed_page = preprocess_image(page)
    return pytesseract.image_to_string(preprocessed_page, config='--psm 1')

def categorize_document(text):
    lower_text = text.lower()
    if "invoice" in lower_text:
        return "Invoices"
    elif "work order" in lower_text:
        return "Work Orders"
    elif "ticket" in lower_text:
        return "Tickets"
    else:
        return "Uncategorized"

def move_file_to_category(path, category):
    organized_dir = '/documents/order'
    category_path = os.path.join(organized_dir, category)

    if not os.path.exists(category_path):
        os.makedirs(category_path)

    new_path = os.path.join(category_path, os.path.basename(path))
    shutil.move(path, new_path)
    return new_path  # Return the new file path

def insert_document_data(db_path, category_id, file_path, ocr_text, summary, filename):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO documents (category_id, file_path, ocr_text, summary, filename)
        VALUES (?, ?, ?, ?, ?)
    ''', (category_id, file_path, ocr_text, summary, filename))

    conn.commit()
    conn.close()

def get_gpt4_summary(document_text):
    client = OpenAI()

    completion = client.chat.completions.create(
        model="gpt-4-1106-preview",  # Adjust the model as necessary
        messages=[
            {"role": "system", "content": "You are a precise assistant."},
            {"role": "user", "content": f"Summarize this document:\n{document_text}"}
        ]
    )

    # Accessing the message content correctly
    if completion.choices and completion.choices[0].message:
        return completion.choices[0].message.content
    else:
        return "No summary available."

def get_gpt4_filename_suggestion(document_summary):
    client = OpenAI()

    completion = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {"role": "system", "content": "You are a precise and logical assistant skilled in summarizing and organizing information. Your task is to create concise yet descriptive filenames."},
            {"role": "user", "content": f"Given this summary, suggest a filename that is clear, concise, and no longer than 9 words: {document_summary}"}
        ]
    )

    if completion.choices and completion.choices[0].message:
        return completion.choices[0].message.content.strip().replace(' ', '_') + '.pdf'
    else:
        return "Unnamed_Document.pdf"

def rename_file(original_path, new_name):
    directory = os.path.dirname(original_path)
    new_path = os.path.join(directory, new_name)
    os.rename(original_path, new_path)
    return new_path

def get_gpt4_category_suggestion(document_text):
    client = OpenAI()

    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages = [
            {"role": "system", "content": "You are a precise, well-organized assistant. Your task is to suggest categories for organizing documents into folders. Each category should be broad enough to be reusable for similar future documents and intuitive enough to indicate the folder's contents. Examples of good categories: invoices, work orders, receipts, reports, promotional materials."},
            {"role": "user", "content": f"Based on the following document text, suggest a category. The category should be a maximum of 3 words and should not include any explanations:\n\n{document_text}"}
        ]

    )

    if response.choices and response.choices[0].message:
        return response.choices[0].message.content.strip()
    else:
        return "Uncategorized"
    
# Update the perform_ocr function
def perform_ocr(db_path, path):
    pages = convert_from_path(path, 500)
    full_text = ""
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = executor.map(perform_ocr_on_page, pages)
        for result in results:
            full_text += result + "\n"

    print(f"Full text: {full_text}")

    # Check against hardcoded categories first
    category_name = check_hardcoded_categories(full_text)

    if category_name is None:
        # If no hardcoded category fits, ask GPT-4 for a suggestion
        category_name = get_gpt4_category_suggestion(full_text)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if the category exists, and if not, insert it
    cursor.execute("SELECT id FROM categories WHERE name = ?", (category_name,))
    category = cursor.fetchone()
    if not category:
        cursor.execute("INSERT INTO categories (name) VALUES (?)", (category_name,))
        conn.commit()  # Commit after inserting new category
        category_id = cursor.lastrowid
    else:
        category_id = category[0]

    summary = get_gpt4_summary(full_text)
    filename_suggestion = get_gpt4_filename_suggestion(summary)
    new_file_path = move_file_to_category(path, category_name)  # Use category_name instead of category
    final_file_path = rename_file(new_file_path, filename_suggestion)

    # Insert document data with category_id
    insert_document_data(db_path, category_id, final_file_path, full_text, summary, filename_suggestion)
    print(f"Processed and moved '{path}' to '{category_name}' category")
    
    conn.close()

if __name__ == '__main__':
    w = Watcher('/documents/chaos')  # Set the directory you want to watch
    w.run()

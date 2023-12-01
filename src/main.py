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

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Specify the full path including the .db file for the new database
database_path = '/Users/christopher/Documents/CAJ DocumentAI/data/documents2.db'

def create_database(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create a new table with all necessary columns
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY,
            category TEXT,
            file_path TEXT,
            ocr_text TEXT,
            summary TEXT DEFAULT '',
            filename TEXT DEFAULT '',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Create the new database and table
create_database(database_path)

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
    organized_dir = '/Users/christopher/Documents/CAJ DocumentAI/order'
    category_path = os.path.join(organized_dir, category)

    if not os.path.exists(category_path):
        os.makedirs(category_path)

    new_path = os.path.join(category_path, os.path.basename(path))
    shutil.move(path, new_path)
    return new_path  # Return the new file path

def insert_document_data(db_path, category, file_path, ocr_text, summary, filename):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO documents (category, file_path, ocr_text, summary, filename)
        VALUES (?, ?, ?, ?, ?)
    ''', (category, file_path, ocr_text, summary, filename))

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
            {"role": "system", "content": "You are a precise assistant."},
            {"role": "user", "content": f"Suggest a filename (max 3 words, provide no explanation) for a document with this summary: {document_summary}"}
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

# Update the perform_ocr function
def perform_ocr(db_path, path):
    pages = convert_from_path(path, 500)
    full_text = ""
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = executor.map(perform_ocr_on_page, pages)
        for result in results:
            full_text += result + "\n"

    category = categorize_document(full_text)
    new_file_path = move_file_to_category(path, category)
    
    summary = get_gpt4_summary(full_text)
    filename_suggestion = get_gpt4_filename_suggestion(summary)
    final_file_path = rename_file(new_file_path, filename_suggestion)

    # Update database insertion to include the filename
    insert_document_data(db_path, category, path, full_text, summary, filename_suggestion)
    print(f"Processed and moved '{path}' to '{category}' category")

if __name__ == '__main__':
    w = Watcher('/Users/christopher/Documents/CAJ DocumentAI/chaos')  # Set the directory you want to watch
    w.run()

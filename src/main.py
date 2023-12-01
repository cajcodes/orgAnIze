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

# Specify the full path including the .db file
database_path = '/Users/christopher/Documents/CAJ DocumentAI/data/documents.db'

def create_database(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY,
            category TEXT,
            file_path TEXT,
            ocr_text TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

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

    shutil.move(path, os.path.join(category_path, os.path.basename(path)))

def insert_document_data(db_path, category, file_path, ocr_text):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO documents (category, file_path, ocr_text)
        VALUES (?, ?, ?)
    ''', (category, file_path, ocr_text))

    conn.commit()
    conn.close()

# Update the perform_ocr function
def perform_ocr(db_path, path):
    pages = convert_from_path(path, 500)
    full_text = ""
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = executor.map(perform_ocr_on_page, pages)
        for result in results:
            full_text += result + "\n"

    category = categorize_document(full_text)
    move_file_to_category(path, category)
    
    insert_document_data(db_path, category, path, full_text)
    print(f"Processed and moved '{path}' to '{category}' category")

if __name__ == '__main__':
    w = Watcher('/Users/christopher/Documents/CAJ DocumentAI/chaos')  # Set the directory you want to watch
    w.run()

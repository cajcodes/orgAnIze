import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pdf2image import convert_from_path
import pytesseract

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
        if event.is_directory:
            return None

        elif event.event_type == 'created':
            # Take any action here when a file is first created.
            print(f"Received created event - {event.src_path}.")
            perform_ocr(event.src_path)


def perform_ocr(path):
    if path.endswith('.pdf'):
        # If it's a PDF, convert to images and perform OCR
        pages = convert_from_path(path, 500)
        for page in pages:
            text = pytesseract.image_to_string(page)
            print(text)  # Placeholder for now, you can later save this text or process it
    else:
        # For other file types, you can add more conditions
        pass


if __name__ == '__main__':
    w = Watcher('/Users/christopher/Documents/CAJ DocumentAI/watched-files')  # Set the directory you want to watch
    w.run()

My project is a document management and organization web application designed to process, categorize, and summarize a variety of documents such as invoices, work orders, and tickets. It's developed in Python, utilizing the Flask web framework for the backend and HTML/CSS for a simple and modern front-end interface.

Here's a breakdown of the project's functionality:

Document Processing:
Monitors a specific directory for new PDF documents using the watchdog library.
Performs OCR on each document using Tesseract OCR to extract text.

Categorization and Summarization:
Utilizes GPT-4 to generate summaries of the documents.
Categorizes documents based on keywords found in the text into predefined categories like Invoices, Work Orders, and Tickets.
Suggests and assigns filenames based on the GPT-4 generated summary.

Database Integration:
Stores document details, including the category, original file path, OCR text, summary, and new filename, in an SQLite database.

Web Interface:
Presents a clean and modern UI where documents are displayed as cards, showing important details like the filename, timestamp, and summary.
Allows users to open documents directly by clicking on their respective cards.
Provides a search functionality, enabling users to search for documents by content or filter documents by category.
Features a search form with a category filter dropdown, populated with distinct categories from the database.

File System Interaction:
Moves processed documents to organized folders based on their categories.
Renames documents according to the filenames suggested by GPT-4.
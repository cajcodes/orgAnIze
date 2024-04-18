![orgAnIze logo](/static/orgAnIze-logo-small.svg)

# Document Management and Organization Web Application

This project is a document management and organization web application designed to process, categorize, and summarize a variety of documents such as invoices, work orders, and tickets. It is developed in Python, utilizing the Flask web framework for the backend and HTML/CSS for a simple and modern front-end interface.

![Redacted screenshot of dashboard](/static/orgAnIze-dashboard-screenshot-redacted.png)

## Key Features

* Monitors a specific directory for new PDF documents using the watchdog library.
* Performs OCR on each document using Tesseract OCR to extract text.
* Utilizes GPT-4 to generate summaries of the documents and categorize them based on keywords found in the text into predefined categories like Invoices, Work Orders, and Tickets.
* Suggests and assigns filenames based on the GPT-4 generated summary.
* Stores document details, including the category, original file path, OCR text, summary, and new filename, in an SQLite database.
* Presents a clean and modern UI where documents are displayed as cards, showing important details like the filename, timestamp, and summary.
* Allows users to open documents directly by clicking on their respective cards.
* Provides a search functionality, enabling users to search for documents by content or filter documents by category.
* Features a search form with a category filter dropdown, populated with distinct categories from the database.
* Moves processed documents to organized folders based on their categories.
* Renames documents according to the filenames suggested by GPT-4.

## Creative Prompting for Highly Accurate Responses

This project utilizes creative prompting techniques to elicit highly accurate responses from the GPT-4 model, including JSON mode. By carefully crafting the prompts, the model is able to generate summaries and categorizations that are accurate and relevant to the documents being processed.

## Local LLMs Support

This project works with local Language Learning Models (LLMs) easily using [LM Studio](https://lmstudio.ai). This allows the use of custom models for processing and categorizing documents, providing greater security, flexibility, and control over the application's behavior. Out of the models I've tested, Hermes-2-Pro-Mistral-7B.Q8_0.gguf and mixtral-8x7b-instruct-v0.1.Q2_K.gguf have worked best. They improve dramatically when you make the prompts much more repetitive. 

# Getting Started

To try out this project, follow these steps:

* Clone the repository to your local machine.
* Install the required dependencies using pip.
* Set up .env with GPT-4 API key or adjust [main-search.py](/src/main-search.py) to point to [LM Studio](https://lmstudio.ai).
* To start the backend, open a terminal window and navigate to the project directory. Run the command `python main-search.py` to start the backend process. This will automatically monitor the /documents/chaos directory for new PDF documents using the watchdog library. When a new document is added to this folder, the backend will perform OCR on the document, extract text, and categorize and summarize the document using GPT-4. The document details will be stored in an SQLite database, and the processed document will be moved to an organized folder based on its category in /documents/order.
* To start the frontend, navigate to the project directory and run the command `flask run` in the terminal. This will start the Flask development server and make the web application accessible at <http://localhost:5000> by default.
* View and search the processed documents in the web interface.
  

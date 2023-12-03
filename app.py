from flask import Flask, render_template, request, send_file, jsonify
import sqlite3
import os
from openai import OpenAI

app = Flask(__name__)

@app.route('/')
def index():
    db_path = '/Users/christopher/Documents/CAJ DocumentAI/data/docs.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Fetch categories for the dropdown
    cursor.execute("SELECT id, name FROM categories")
    categories = cursor.fetchall()

    # Join documents with categories to get category names
    cursor.execute("SELECT filename, categories.name, timestamp, summary FROM documents INNER JOIN categories ON documents.category_id = categories.id")
    documents = cursor.fetchall()

    conn.close()

    return render_template('index.html', documents=documents, categories=categories)

@app.route('/open/<category>/<filename>')
def open_file(category, filename):
    file_path = f'/Users/christopher/Documents/CAJ DocumentAI/order/{category}/{filename}'
    try:
        # Try to send the file for inline viewing if the browser supports it
        return send_file(file_path, as_attachment=False)
    except FileNotFoundError:
        return "File not found", 404

@app.route('/process_query', methods=['POST'])
def process_query():
    data = request.json
    query = data['query']
    response = handle_gpt4_query(query)
    return jsonify({'response': response})

def query_database_for_docs_or_categories(query):
    db_path = '/Users/christopher/Documents/CAJ DocumentAI/data/docs.db'  # Update with the correct path
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Query for matching documents
    cursor.execute("SELECT id, filename, file_path, summary FROM documents WHERE ocr_text LIKE ? OR summary LIKE ?", ('%'+query+'%', '%'+query+'%'))
    document_results = cursor.fetchall()

    # Query for matching categories
    cursor.execute("SELECT id, name FROM categories WHERE name LIKE ?", ('%'+query+'%',))
    category_results = cursor.fetchall()

    conn.close()
    return document_results, category_results

def handle_gpt4_query(query):
    document_results, _ = query_database_for_docs_or_categories(query)
    formatted_doc_results = format_for_gpt4(document_results)

    # GPT-4 interaction
    client = OpenAI()

    completion = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Use the provided document details to answer queries."},
            {"role": "user", "content": f"Query: {query}. Based on these documents: {formatted_doc_results}, what information can you provide?"}
        ]
    )

    if completion.choices and completion.choices[0].message:
        return completion.choices[0].message.content
    else:
        return "No results found."

def format_for_gpt4(document_results):
    # Simple format: filename, filepath, and summary
    formatted_results = []
    for _, filename, filepath, summary in document_results:
        formatted_result = f"Filename: {filename}, Filepath: {filepath}, Summary: {summary}"
        formatted_results.append(formatted_result)

    return ' | '.join(formatted_results) if formatted_results else "No relevant documents found."

@app.route('/search')
def search():
    query = request.args.get('query', '')
    selected_category_id = request.args.get('category', '')

    db_path = '/Users/christopher/Documents/CAJ DocumentAI/data/docs.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Fetch categories for the dropdown
    cursor.execute("SELECT id, name FROM categories")
    categories = cursor.fetchall()

    # Construct the SQL query with JOIN
    sql_query = "SELECT filename, categories.name, timestamp, summary FROM documents INNER JOIN categories ON documents.category_id = categories.id"
    sql_params = []

    if selected_category_id and query:
        sql_query += " WHERE categories.id = ? AND ocr_text LIKE ?"
        sql_params.extend([selected_category_id, f'%{query}%'])
    elif selected_category_id:
        sql_query += " WHERE categories.id = ?"
        sql_params.append(selected_category_id)
    elif query:
        sql_query += " WHERE ocr_text LIKE ?"
        sql_params.append(f'%{query}%')

    cursor.execute(sql_query, sql_params)
    documents = cursor.fetchall()

    conn.close()

    return render_template('index.html', documents=documents, categories=categories)

if __name__ == '__main__':
    app.run(debug=True)

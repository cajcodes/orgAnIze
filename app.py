from flask import Flask, render_template, request, send_file
import sqlite3
import os

app = Flask(__name__)

@app.route('/')
def index():
    db_path = '/Users/christopher/Documents/CAJ DocumentAI/data/documents2.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT category FROM documents")
    categories = cursor.fetchall()  # This will be a list of tuples

    cursor.execute("SELECT filename, category, timestamp, summary FROM documents")
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

@app.route('/search')
def search():
    query = request.args.get('query', '')  # Default to an empty string if no query is provided
    selected_category = request.args.get('category', '')  # Default to no category if none is selected

    db_path = '/Users/christopher/Documents/CAJ DocumentAI/data/documents2.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Fetch categories for the dropdown
    cursor.execute("SELECT DISTINCT category FROM documents")
    categories = cursor.fetchall()

    # Construct the SQL query based on the presence of a query and/or category
    sql_query = "SELECT filename, category, timestamp, summary FROM documents"
    sql_params = []

    if selected_category and query:
        sql_query += " WHERE category = ? AND ocr_text LIKE ?"
        sql_params.extend([selected_category, f'%{query}%'])
    elif selected_category:
        sql_query += " WHERE category = ?"
        sql_params.append(selected_category)
    elif query:
        sql_query += " WHERE ocr_text LIKE ?"
        sql_params.append(f'%{query}%')

    cursor.execute(sql_query, sql_params)
    documents = cursor.fetchall()

    conn.close()

    return render_template('index.html', documents=documents, categories=categories)

if __name__ == '__main__':
    app.run(debug=True)

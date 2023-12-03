from flask import Flask, render_template, request, send_file
import sqlite3
import os

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

    return render_template('index-search.html', documents=documents, categories=categories)

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

    return render_template('index-search.html', documents=documents, categories=categories)

if __name__ == '__main__':
    app.run(debug=True)

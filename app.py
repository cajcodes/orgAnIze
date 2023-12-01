from flask import Flask, render_template
import sqlite3
import os

app = Flask(__name__)

@app.route('/')
def index():
    db_path = '/Users/christopher/Documents/CAJ DocumentAI/data/documents2.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT filename, category, timestamp, summary FROM documents")
    documents = cursor.fetchall()
    conn.close()

    return render_template('index.html', documents=documents)

@app.route('/open/<category>/<filename>')
def open_file(category, filename):
    file_path = f'/Users/christopher/Documents/CAJ DocumentAI/order/{category}/{filename}'
    os.system(f'open "{file_path}"')  # 'open' for macOS, 'start' for Windows
    return '', 204

if __name__ == '__main__':
    app.run(debug=True)

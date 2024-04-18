import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from src.main_search import perform_ocr, database_path

# Define evaluation criteria
evaluation_criteria = {
    "Categorization Accuracy": defaultdict(int),
    "Summary Coherence": defaultdict(int),
    "Filename Relevance": defaultdict(int),
    "Category Relevance": defaultdict(int)
}

# Generate test data
test_documents = [
    {"name": "invoice.pdf", "content": "This is an invoice document."},
    {"name": "report.pdf", "content": "This is a quarterly report."},
    {"name": "letter.pdf", "content": "This is a formal letter."},
    {"name": "work_order.pdf", "content": "This is a work order document."},
    {"name": "receipt.pdf", "content": "This is a sales receipt."},
    {"name": "contract.pdf", "content": "This is a legal contract."},
    {"name": "manual.pdf", "content": "This is an instructional manual."},
    {"name": "marketing.pdf", "content": "This is a marketing brochure."}
]

# Create a temporary directory for test documents
temp_dir = tempfile.mkdtemp()
for doc in test_documents:
    with open(os.path.join(temp_dir, doc["name"]), "w") as f:
        f.write(doc["content"])

# Run the provided code on the test data
for doc_path in Path(temp_dir).glob("*.pdf"):
    perform_ocr(database_path, str(doc_path))

# Evaluate outputs
conn = sqlite3.connect(database_path)
cursor = conn.cursor()

for doc in test_documents:
    cursor.execute("SELECT category_id, ocr_text, summary, filename FROM documents WHERE file_path = ?", (str(Path(temp_dir) / doc["name"]),))
    result = cursor.fetchone()
    if result:
        category_id, ocr_text, summary, filename = result
        category = cursor.execute("SELECT name FROM categories WHERE id = ?", (category_id,)).fetchone()[0]

        # Evaluate categorization accuracy
        if category.lower() in doc["name"]:
            evaluation_criteria["Categorization Accuracy"]["Correct"] += 1
        else:
            evaluation_criteria["Categorization Accuracy"]["Incorrect"] += 1

        # Evaluate summary coherence
        if summary:
            evaluation_criteria["Summary Coherence"]["Present"] += 1
        else:
            evaluation_criteria["Summary Coherence"]["Absent"] += 1

        # Evaluate filename relevance
        if filename.lower().startswith(doc["name"].split(".")[0]):
            evaluation_criteria["Filename Relevance"]["Relevant"] += 1
        else:
            evaluation_criteria["Filename Relevance"]["Irrelevant"] += 1

        # Evaluate category relevance
        if category.lower() in ocr_text.lower():
            evaluation_criteria["Category Relevance"]["Relevant"] += 1
        else:
            evaluation_criteria["Category Relevance"]["Irrelevant"] += 1

# Print evaluation results
print("Evaluation Results:")
for criteria, values in evaluation_criteria.items():
    print(f"{criteria}:")
    for value, count in values.items():
        print(f" - {value}: {count}")
    print()

# Clean up temporary directory
shutil.rmtree(temp_dir)

from flask import Flask, render_template, request, jsonify
import requests
import logging

# Simple logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Example: I assume the BACKEND_URL is set via environment variable
# or you could hard-code "http://backend:8000"
import os
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/create-item", methods=["POST"])
def create_item():
    item_data = request.form.get("item_data")
    logger.info(f"Received item_data from client: {item_data}")

    # Call the backend to create an item in the DB
    response = requests.post(f"{BACKEND_URL}/items", json={"data": item_data})
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({"error": "Failed to create item"}), 500

@app.route("/list-items", methods=["GET"])
def list_items():
    # Call the backend to fetch items
    response = requests.get(f"{BACKEND_URL}/items")
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({"error": "Could not fetch items"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

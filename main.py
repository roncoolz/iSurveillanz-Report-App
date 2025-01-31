from flask import Flask, request, jsonify, send_from_directory
from pymongo import MongoClient
import os
import re
from flask_cors import CORS
from textblob import TextBlob
from transformers import pipeline

app = Flask(__name__)
CORS(app)

# Connect to MongoDB
client = MongoClient('mongodb://192.168.0.18:27017/')  # Update Mongo URI if needed
db = client['For_Test']
collection = db['AutoTextPopulations']
# Initialize the transformer model for grammar correction
grammar_corrector = pipeline("text2text-generation", model="t5-base", device=0)  # Use device=0 for GPU if available
corrector = pipeline("text2text-generation", model="t5-base", tokenizer="t5-base")


def autocorrect_sentence(sentence):
    # Use the T5 model to correct grammar and phrasing
    input_text = f"grammar: {sentence}"
    result = grammar_corrector(input_text)
    corrected_sentence = result[0]['generated_text']
    
    return corrected_sentence

@app.route('/')
def serve_index():
    return send_from_directory(os.getcwd(), 'index.html')

@app.route('/get_sentences', methods=['GET'])
def get_sentences():
    words = request.args.get('word', '').split()
    
    if not words:
        return jsonify([])

    queries = [{"sentence": {"$regex": f".*{re.escape(word)}.*", "$options": "i"}} for word in words]
    results = collection.find({"$and": queries})
    
    sentences = [result['sentence'] for result in results]
    
    return jsonify(sentences)


@app.route('/autocorrect_sentence', methods=['POST'])
def autocorrect_sentence_route():
    data = request.get_json()
    
    if 'sentence' not in data:
        return jsonify({"error": "No sentence provided"}), 400

    sentence = data['sentence']
    
    # Apply the autocorrection using T5 model
    corrected_sentence = corrector(f"correct grammar: {sentence}")[0]['generated_text']
    
    return jsonify({"corrected_sentence": corrected_sentence})

if __name__ == '__main__':
    app.run(debug=True)

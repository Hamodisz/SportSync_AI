from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv

load_dotenv()
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'runpod_api_key': RUNPOD_API_KEY})

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    # هنا ضع منطقك الخاص
    result = {'prediction': 'demo'}
    return jsonify(result)

if __name__ == '__main__':
    print(f"RUNPOD_API_KEY: {RUNPOD_API_KEY}")
    app.run(host='0.0.0.0', port=8080)

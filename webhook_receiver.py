"""
Visualping Webhook Receiver

Receives Visualping webhook notifications -> Runs AI analysis -> Sends alerts
"""

import os
from flask import Flask, request, jsonify
from datetime import datetime
from threading import Thread

# Import our alert pipeline
from alert_pipeline import process_alert

app = Flask(__name__)

# Config from environment
ALERT_EMAIL = os.getenv('ALERT_EMAIL', None)
CLIENT_NAME = os.getenv('CLIENT_NAME', 'AquaRegWatch User')

# Source name mapping (Visualping URL -> friendly name)
SOURCE_NAMES = {
    'fiskeridir.no': 'Fiskeridirektoratet',
    'mattilsynet.no': 'Mattilsynet',
    'miljodirektoratet.no': 'Miljødirektoratet',
    'lovdata.no': 'Lovdata',
    'regjeringen.no': 'Regjeringen',
}


def get_source_name(url: str) -> str:
    """Extract friendly source name from URL"""
    for domain, name in SOURCE_NAMES.items():
        if domain in url:
            return name
    return url.split('/')[2] if '/' in url else url


def process_in_background(url: str, source_name: str):
    """Run the alert pipeline in background thread"""
    try:
        print(f"[PIPELINE] Starting for {source_name}")
        result = process_alert(
            url=url,
            source_name=source_name,
            to_email=ALERT_EMAIL,
            client_name=CLIENT_NAME
        )
        print(f"[PIPELINE] Complete: {result['summary']['title']}")
    except Exception as e:
        print(f"[PIPELINE] Error: {e}")


@app.route('/webhook/visualping', methods=['POST'])
def visualping_webhook():
    """
    Receive Visualping webhook -> Trigger AI analysis -> Send alert
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No JSON data received'}), 400

        url = data.get('url', '')
        change_detected = data.get('change_detected', True)
        job_id = data.get('job_id', 'unknown')
        timestamp = datetime.utcnow().isoformat()

        print(f"\n{'='*50}")
        print(f"[{timestamp}] CHANGE DETECTED")
        print(f"  URL: {url}")
        print(f"  Job: {job_id}")
        print(f"{'='*50}")

        if change_detected and url:
            # Process in background so webhook returns quickly
            source_name = get_source_name(url)
            thread = Thread(target=process_in_background, args=(url, source_name))
            thread.start()

        return jsonify({
            'status': 'processing',
            'url': url,
            'message': 'Alert pipeline triggered'
        }), 200

    except Exception as e:
        print(f"[ERROR] Webhook failed: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({'status': 'healthy'}), 200


if __name__ == '__main__':
    # Run on port 5000 by default
    # Use 0.0.0.0 to accept external connections (needed for webhooks)
    app.run(host='0.0.0.0', port=5000, debug=True)

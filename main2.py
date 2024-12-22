import threading
from flask import Flask, jsonify, Response, render_template
from flask_cors import CORS
import json
import time
import psycopg2
from multiprocessing import Process, Manager, freeze_support
from fingerprint_handler import listen_for_fingerprint, initialize_fingerprint
from card_reader_handler import listen_for_card_swipe, initialize_card_reader

app = Flask(__name__)
CORS(app)  # This allows cross-origin requests

# Global variables to store the latest data
latest_fingerprint_data = None
latest_card_data = None

@app.route('/api/<data_type>', methods=['GET'])
def get_data(data_type):
    global latest_fingerprint_data, latest_card_data
    data_source = latest_fingerprint_data if data_type == 'fingerprint' else latest_card_data
    data = json.loads(data_source.value) if data_source else {}
    if data:
        return jsonify(data)
    else:
        return jsonify({"error": f"No {data_type} data available"}), 404

@app.route('/api/stream-readings')
def stream_readings():
    def generate():
        global latest_fingerprint_data, latest_card_data
        last_sent_fingerprint = None
        last_sent_card = None
        while True:
            fingerprint_data = latest_fingerprint_data.value if latest_fingerprint_data else None
            card_data = latest_card_data.value if latest_card_data else None
            
            if fingerprint_data != last_sent_fingerprint:
                last_sent_fingerprint = fingerprint_data
                try:
                    if isinstance(fingerprint_data, dict):
                        yield f"data: {json.dumps(fingerprint_data, default=str)}\n\n"
                    elif isinstance(fingerprint_data, (str, bytes)):
                        if isinstance(fingerprint_data, bytes):
                            fingerprint_data = fingerprint_data.decode('utf-8')
                        yield f"data: {fingerprint_data}\n\n"
                    else:
                        yield f"data: {json.dumps({'error': 'Invalid fingerprint data type'})}\n\n"
                except Exception as e:
                    yield f"data: {json.dumps({'error': f'Error processing fingerprint data: {str(e)}'})}\n\n"
                if latest_fingerprint_data:
                    latest_fingerprint_data.value = None  # Clear the data after sending
            
            if card_data != last_sent_card:
                last_sent_card = card_data
                try:
                    if isinstance(card_data, dict):
                        yield f"data: {json.dumps(card_data, default=str)}\n\n"
                    elif isinstance(card_data, (str, bytes)):
                        if isinstance(card_data, bytes):
                            card_data = card_data.decode('utf-8')
                        yield f"data: {card_data}\n\n"
                    else:
                        yield f"data: {json.dumps({'error': 'Invalid card data type'})}\n\n"
                except Exception as e:
                    yield f"data: {json.dumps({'error': f'Error processing card data: {str(e)}'})}\n\n"
                if latest_card_data:
                    latest_card_data.value = None  # Clear the data after sending
            
            time.sleep(0.5)  # Check for updates every 0.5 seconds

    return Response(generate(), mimetype='text/event-stream')


@app.route('/atco_check_page.html')
def home():
    return render_template('atco_check_page.html')

@app.route('/session_page.html')
def data():
    return render_template('session_page.html')

def run_flask():
    app.run(host='localhost', port=5000, threaded=True)

def web_server_thread():
    app.run(host='localhost', port=5000, threaded=True)

def fingerprint_process_function(db_connection_params, shared_data):
    finger = initialize_fingerprint()
    db_connection = psycopg2.connect(**db_connection_params)
    listen_for_fingerprint(finger, db_connection, shared_data)

def card_process_function(db_connection_params, shared_data):
    card_reader = initialize_card_reader()
    db_connection = psycopg2.connect(**db_connection_params)
    listen_for_card_swipe(card_reader, db_connection, shared_data)

def main():
    global latest_fingerprint_data, latest_card_data
    
    # Create a manager to handle shared memory
    manager = Manager()
    latest_fingerprint_data = manager.Value(str, '{}')
    latest_card_data = manager.Value(str, '{}')

    # Database connection parameters
    db_connection_params = {
        "dbname": "position_log",
        "user": "postgres",
        "password": "admin",
        "host": "localhost",
        "port": "5432"
    }

    # Start the Flask server in a separate thread
    web_thread = threading.Thread(target=web_server_thread)
    web_thread.daemon = True  # This ensures the thread will exit when the main program does
    web_thread.start()

    # Start listening for fingerprints in a separate process
    fingerprint_process = Process(target=fingerprint_process_function, 
                                  args=(db_connection_params, latest_fingerprint_data))
    fingerprint_process.start()

    # Start listening for card swipes in a separate process
    card_process = Process(target=card_process_function, 
                           args=(db_connection_params, latest_card_data))
    card_process.start()

    try:
        fingerprint_process.join()
        card_process.join()
    except KeyboardInterrupt:
        print("Stopping the application...")
    finally:
        fingerprint_process.terminate()
        card_process.terminate()

if __name__ == "__main__":
    freeze_support()  # This is necessary for Windows
    main()
import time
import serial
import adafruit_fingerprint
import psycopg2
from psycopg2 import sql
from datetime import datetime
import json

def datetime_to_iso(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

def get_fingerprint(finger):
    """Get a finger print image, template it, and see if it matches!"""
    while finger.get_image() != adafruit_fingerprint.OK:
        pass
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        return False
    if finger.finger_search() != adafruit_fingerprint.OK:
        return False
    return True

def listen_for_fingerprint(finger, db_connection, latest_fingerprint_data):
    print("Listening for fingerprints. Press Ctrl+C to exit.")
    try:
        while True:
            if get_fingerprint(finger):
                print(f"Fingerprint found! ID #{finger.finger_id} with confidence {finger.confidence}")

                cursor = db_connection.cursor()
                
                # Fetch user data from api_employee table
                cursor.execute("SELECT * FROM api_employee WHERE fingerprint_id = %s", (finger.finger_id,))
                user_data = cursor.fetchone()

                cursor.close()

                if user_data:
                    # Convert user_data to a dictionary for easier API response handling
                    columns = [desc[0] for desc in cursor.description]
                    user_dict = dict(zip(columns, user_data))
                    print("User data:", user_dict)
                    # Convert datetime objects to ISO format strings
                    latest_fingerprint_data.value = json.loads(json.dumps(user_dict, default=datetime_to_iso))

                    # Removed the wait time after sending data
                else:
                    print("User not found in the database")
                    latest_fingerprint_data.value = {"error": "User not found"}
            else:
                print("Fingerprint not found")
            time.sleep(1)  # Add a small delay to prevent excessive CPU usage
    except KeyboardInterrupt:
        print("\nFingerprint listening stopped.")
        latest_fingerprint_data.value = {"error": "Listening stopped"}

def initialize_fingerprint(port="COM7", baudrate=57600):
    uart = serial.Serial(port, baudrate=baudrate, timeout=1)
    finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

    if finger.read_templates() != adafruit_fingerprint.OK:
        raise RuntimeError("Failed to read templates")

    print("Fingerprint templates:", finger.templates)
    return finger
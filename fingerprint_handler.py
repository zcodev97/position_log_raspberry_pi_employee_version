import time
import serial
import adafruit_fingerprint
from datetime import datetime
import requests
from dotenv import load_dotenv
import os
load_dotenv()
API_BASE_URL = os.getenv('SERVER_URL')
FINGERPRINT_PORT = "COM5"
FINGERPRINT_BAUDRATE = 57600 


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

def get_employee_by_fingerprint(fingerprint_id):
    """Fetch employee data from API using fingerprint ID"""
    try:
        response = requests.get(f"{API_BASE_URL}/employee/get/fingerprint_id/{fingerprint_id}/")
        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException as e:
        print(f"API request failed: {str(e)}")
        return None

def listen_for_fingerprint(finger, latest_fingerprint_data):
    print("Listening for fingerprints. Press Ctrl+C to exit.")
    try:
        while True:
            if get_fingerprint(finger):
                print(f"Fingerprint found! ID #{finger.finger_id} with confidence {finger.confidence}")
                
                # Fetch user data from API instead of database
                user_data = get_employee_by_fingerprint(finger.finger_id)

                if user_data:

                    print("User data:", user_data)
                    latest_fingerprint_data.value = user_data
                    
                else:
                    print("User not found in the API")
                    latest_fingerprint_data.value = {"error": "User not found"}
            else:
                continue

            time.sleep(1)  # Add a small delay to prevent excessive CPU usage
    except KeyboardInterrupt:
        print("\nFingerprint listening stopped.")
        latest_fingerprint_data.value = {"error": "Listening stopped"}

def initialize_fingerprint(port=FINGERPRINT_PORT, baudrate=FINGERPRINT_BAUDRATE):
    """Initialize fingerprint sensor with infinite retry until connected"""
    while True:
        try:
            print(f"Attempting to connect to fingerprint sensor on {port}...")
            uart = serial.Serial(port, baudrate=baudrate, timeout=1)
            finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

            if finger.read_templates() != adafruit_fingerprint.OK:
                raise RuntimeError("Failed to read templates")

            print(f"Successfully connected to fingerprint sensor on {port}")
            print("Fingerprint templates:", finger.templates)
            return finger

        except (serial.SerialException, RuntimeError) as e:
            print(f"Failed to connect: {str(e)}")
            print("Waiting for fingerprint sensor to be connected...")
            time.sleep(2)  # Wait for 2 seconds before trying again
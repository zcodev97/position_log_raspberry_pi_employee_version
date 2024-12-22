import time
import serial
import adafruit_pn532.uart
import winsound
import psycopg2
import json
from datetime import datetime, timedelta
import serial
import requests

# NFC reader setup
CARD_READER_PORT = 'COM6'
CARD_READER_BAUDRATE = 115200


# Function to convert datetime objects to ISO format strings
def datetime_to_iso(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")



def setup_nfc_reader():
    while True:
        try:
            uart = serial.Serial(CARD_READER_PORT, baudrate=CARD_READER_BAUDRATE, timeout=1)
            pn532 = adafruit_pn532.uart.PN532_UART(uart, debug=False)
            
            ic, ver, rev, support = pn532.firmware_version
            print('Found PN532 with firmware version: {0}.{1}'.format(ver, rev))
            
            pn532.SAM_configuration()
            print('Card reader successfully connected on port', CARD_READER_PORT)
            print('Waiting for an ISO14443A Card...')
            return pn532
        except (serial.SerialException, OSError) as e:
            print(f"Unable to connect to card reader on port {CARD_READER_PORT}: {e}")
            print("Waiting for card reader to be connected...")
            time.sleep(2)  # Wait for 2 seconds before trying again

# Function to convert UID to string format
def uid_to_string(uid):
    return ''.join([format(i, '02X') for i in uid])

# Function to get user data from the API
def get_user_data(card_id):
    api_url = f"http://172.20.10.2:8000/employee/get/card_id/{card_id}/"
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            user_data = response.json()
            print("User data:", user_data)
            return user_data
        else:
            print(f"API request failed with status code: {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"Error making API request: {e}")
        return None



last_read_time = {}

def can_read_card(card_id):
    current_time = datetime.now()
    if card_id in last_read_time:
        time_since_last_read = current_time - last_read_time[card_id]
        if time_since_last_read < timedelta(seconds=5):
            return False
    last_read_time[card_id] = current_time
    return True

def initialize_card_reader():
    return setup_nfc_reader()

def listen_for_card_swipe(pn532, latest_card_data):
    print("Listening for card swipes. Press Ctrl+C to exit.")
    
    while True:
        try:
            uid = pn532.read_passive_target(timeout=0.5)
            if uid is not None:
                uid_string = uid_to_string(uid)
                print('Found card with UID:', uid_string)
                
                if can_read_card(uid_string):
                    user_data = get_user_data(uid_string)
                    
                    if user_data:
                        winsound.Beep(1000, 500)  # 1000 Hz for 500 milliseconds
                        
                        # Update the latest_card_data
                        latest_card_data.value = json.dumps(user_data).encode()
                    else:
                        print("Card not registered in the database")
                        winsound.Beep(500, 500)  # Lower pitch for unregistered card
                else:
                    print("Card read too soon, ignoring")
            
            time.sleep(0.1)  # Short delay to prevent excessive CPU usage
        
        except (serial.SerialException, OSError) as e:
            print(f"Error communicating with NFC reader: {e}")
            print("Waiting for card reader to reconnect...")
            pn532 = setup_nfc_reader()  # This will now wait until connection is restored

# Modify the main function to use the new listen_for_card_swipe function
def main():
    pn532 = initialize_card_reader()
    
    # Remove db_connection creation
    latest_card_data = type('obj', (object,), {'value': b''})()

    listen_for_card_swipe(pn532, latest_card_data)

if __name__ == "__main__":
    main()

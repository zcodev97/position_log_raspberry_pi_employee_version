import time
import serial
import adafruit_pn532.uart
import winsound
import psycopg2
import json
from datetime import datetime, timedelta

# Database connection function
def get_db_connection():
    return psycopg2.connect(
        dbname="position_log",
        user="postgres",
        password="admin",
        host="localhost",
        port="5432"
    )

# Function to convert datetime objects to ISO format strings
def datetime_to_iso(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

# NFC reader setup
serial_port = 'COM10'
baudrate = 115200

def setup_nfc_reader():
    uart = serial.Serial(serial_port, baudrate=baudrate, timeout=1)
    pn532 = adafruit_pn532.uart.PN532_UART(uart, debug=False)
    
    ic, ver, rev, support = pn532.firmware_version
    print('Found PN532 with firmware version: {0}.{1}'.format(ver, rev))
    
    pn532.SAM_configuration()
    print('Waiting for an ISO14443A Card...')
    return pn532

# Function to convert UID to string format
def uid_to_string(uid):
    return ''.join([format(i, '02X') for i in uid])

# Function to get user data from the database
def get_user_data(card_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Fetch user data from api_employee table
        cursor.execute("SELECT * FROM api_employee WHERE card_id = %s", (card_id,))
        user_data = cursor.fetchone()

        if user_data:
            # Convert user_data to a dictionary for easier API response handling
            columns = [desc[0] for desc in cursor.description]
            user_dict = dict(zip(columns, user_data))
            print("User data:", user_dict)
            # Convert datetime objects to ISO format strings
            return json.loads(json.dumps(user_dict, default=datetime_to_iso))
        else:
            print("User not found in the database")
            return None
    finally:
        cursor.close()
        conn.close()



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

def listen_for_card_swipe(pn532, db_connection, latest_card_data):
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
            print("Attempting to reconnect...")
            time.sleep(5)
            pn532 = setup_nfc_reader()

# Modify the main function to use the new listen_for_card_swipe function
def main():
    pn532 = initialize_card_reader()
    
    # Create a mock db_connection and latest_card_data for testing
    db_connection = get_db_connection()
    latest_card_data = type('obj', (object,), {'value': b''})()

    listen_for_card_swipe(pn532, db_connection, latest_card_data)

if __name__ == "__main__":
    main()

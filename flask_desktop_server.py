import sys
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QTabWidget, QPushButton, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QComboBox
from PyQt5.QtCore import QThread, pyqtSignal, Qt
import json
import time
import psycopg2
from multiprocessing import Process, Manager, freeze_support
from fingerprint_handler import listen_for_fingerprint, initialize_fingerprint, datetime_to_iso
from card_reader_handler import listen_for_card_swipe, initialize_card_reader
from datetime import datetime

# Global variables to store the latest data
latest_fingerprint_data = None
latest_card_data = None

class DataThread(QThread):
    update_signal = pyqtSignal(str)

    def run(self):
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
                        self.update_signal.emit(json.dumps(fingerprint_data, default=str))
                    elif isinstance(fingerprint_data, (str, bytes)):
                        if isinstance(fingerprint_data, bytes):
                            fingerprint_data = fingerprint_data.decode('utf-8')
                        self.update_signal.emit(fingerprint_data)
                    else:
                        self.update_signal.emit(json.dumps({'error': 'Invalid fingerprint data type'}))
                except Exception as e:
                    self.update_signal.emit(json.dumps({'error': f'Error processing fingerprint data: {str(e)}'}))
                if latest_fingerprint_data:
                    latest_fingerprint_data.value = None  # Clear the data after sending
            
            if card_data != last_sent_card:
                last_sent_card = card_data
                try:
                    if isinstance(card_data, dict):
                        self.update_signal.emit(json.dumps(card_data, default=str))
                    elif isinstance(card_data, (str, bytes)):
                        if isinstance(card_data, bytes):
                            card_data = card_data.decode('utf-8')
                        self.update_signal.emit(card_data)
                    else:
                        self.update_signal.emit(json.dumps({'error': 'Invalid card data type'}))
                except Exception as e:
                    self.update_signal.emit(json.dumps({'error': f'Error processing card data: {str(e)}'}))
                if latest_card_data:
                    latest_card_data.value = None  # Clear the data after sending
            
            time.sleep(0.5)  # Check for updates every 0.5 seconds

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fingerprint and Card Reader")
        self.setGeometry(100, 100, 800, 600)

        # Create a tab widget
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # Create and add the first tab (existing functionality)
        self.create_data_display_tab()

        # Create and add the second tab (check-in/check-out)
        self.create_checks_tab()

        self.data_thread = DataThread()
        self.data_thread.update_signal.connect(self.update_text)
        self.data_thread.start()

    def create_data_display_tab(self):
        data_display_widget = QWidget()
        layout = QVBoxLayout()
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)
        data_display_widget.setLayout(layout)
        self.tab_widget.addTab(data_display_widget, "Data Display")

    def create_checks_tab(self):
        checks_widget = QWidget()
        layout = QVBoxLayout()

        # Employee ID input
        id_layout = QHBoxLayout()
        id_label = QLabel("Employee ID:")
        self.id_input = QLineEdit()
        id_layout.addWidget(id_label)
        id_layout.addWidget(self.id_input)
        layout.addLayout(id_layout)

        # Check type selection
        check_type_layout = QHBoxLayout()
        check_type_label = QLabel("Check Type:")
        self.check_type_combo = QComboBox()
        self.check_type_combo.addItems(["Check In", "Check Out", "Break Start", "Break End"])
        check_type_layout.addWidget(check_type_label)
        check_type_layout.addWidget(self.check_type_combo)
        layout.addLayout(check_type_layout)

        # Submit button
        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.submit_check)
        layout.addWidget(self.submit_button)

        # Status display
        self.status_label = QLabel("Status: Ready")
        layout.addWidget(self.status_label)

        checks_widget.setLayout(layout)
        self.tab_widget.addTab(checks_widget, "Checks")

    def update_text(self, text):
        self.text_edit.append(text)

    def submit_check(self):
        employee_id = self.id_input.text()
        check_type = self.check_type_combo.currentText()

        if not employee_id:
            self.show_error("Please enter an employee ID")
            return

        try:
            # Connect to the database
            conn = psycopg2.connect(
                dbname="position_log",
                user="postgres",
                password="admin",
                host="localhost",
                port="5432"
            )
            cur = conn.cursor()

            # Get the current timestamp
            timestamp = datetime.now()

            # Insert the check record into the database
            cur.execute("""
                INSERT INTO checks (employee_id, check_type, timestamp)
                VALUES (%s, %s, %s)
            """, (employee_id, check_type, timestamp))

            conn.commit()
            self.status_label.setText(f"Status: {check_type} recorded for employee {employee_id}")

        except psycopg2.Error as e:
            self.show_error(f"Database error: {e}")

        finally:
            if conn:
                cur.close()
                conn.close()

    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)

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

    # Start listening for fingerprints in a separate process
    fingerprint_process = Process(target=fingerprint_process_function, 
                                  args=(db_connection_params, latest_fingerprint_data))
    fingerprint_process.start()

    # Start listening for card swipes in a separate process
    card_process = Process(target=card_process_function, 
                           args=(db_connection_params, latest_card_data))
    card_process.start()

    # Start the PyQt application
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    try:
        sys.exit(app.exec_())  # Note the underscore in exec_()
    except KeyboardInterrupt:
        print("Stopping the application...")
    finally:
        fingerprint_process.terminate()
        card_process.terminate()

if __name__ == "__main__":
    freeze_support()  # This is necessary for Windows
    main()
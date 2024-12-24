from PyQt5.QtWidgets import (QWidget, QPushButton, QVBoxLayout, QHBoxLayout, 
                           QTextEdit, QComboBox, QLabel, QMessageBox)
from PyQt5.QtCore import Qt
import serial
import requests
import adafruit_fingerprint
from utils.fingerprint_functions import get_fingerprint, enroll_finger
from utils.enroll_dialog import EnrollDialog

class AdminTab(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.finger = None
        self.enrolled_prints = set()
        self.api_base_url = "http://192.168.0.194:8000"
        
        # Create log attribute first
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        
        
        layout = QVBoxLayout(self)
        
        # Port selection
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Select Port:"))
        self.port_dropdown = QComboBox()
        self.update_port_list()
        port_layout.addWidget(self.port_dropdown)
        
        refresh_btn = QPushButton("Refresh Ports")
        refresh_btn.clicked.connect(self.update_port_list)
        port_layout.addWidget(refresh_btn)
        layout.addLayout(port_layout)
        
        # Connect button
        connect_btn = QPushButton("Connect")
        connect_btn.clicked.connect(self.connect_fingerprint)
        layout.addWidget(connect_btn)
        
        # Log area
        layout.addWidget(self.log)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        enroll_btn = QPushButton("Enroll Print")
        enroll_btn.clicked.connect(self.enroll_print)
        button_layout.addWidget(enroll_btn)
        
        find_btn = QPushButton("Find Print")
        find_btn.clicked.connect(self.find_print)
        button_layout.addWidget(find_btn)
        
        delete_btn = QPushButton("Delete Print")
        delete_btn.clicked.connect(self.delete_print)
        button_layout.addWidget(delete_btn)
        
        layout.addLayout(button_layout)
        
        # Load enrolled prints on initialization
        self.load_enrolled_prints()

    def update_port_list(self):
        self.port_dropdown.clear()
        ports = self.get_available_ports()
        if ports:
            self.port_dropdown.addItems(ports)
        else:
            self.log.append("No ports available. Please check your connections.")

    def get_available_ports(self):
        import serial.tools.list_ports
        return [port.device for port in serial.tools.list_ports.comports()]

    def connect_fingerprint(self):
        if not self.port_dropdown.currentText():
            self.log.append("No port selected. Please select a port.")
            return

        selected_port = self.port_dropdown.currentText()
        try:
            uart = serial.Serial(selected_port, baudrate=57600, timeout=1)
            self.finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)
            self.log.append(f"Connected to {selected_port}")
            self.update_templates()
        except serial.SerialException as e:
            self.log.append(f"Failed to connect: {str(e)}")
            self.log.append("Please check if the device is properly connected and not in use by another application.")
        except Exception as e:
            self.log.append(f"An unexpected error occurred: {str(e)}")

    def update_templates(self):
        if self.finger and self.finger.read_templates() == adafruit_fingerprint.OK:
            self.log.append(f"Fingerprint templates: {self.finger.templates}")
        else:
            self.log.append("Failed to read templates")

    def enroll_print(self):
        if not self.finger:
            self.log.append("Please connect to a fingerprint sensor first")
            return

        # Open custom dialog
        dialog = EnrollDialog(self)
        if dialog.exec():
            username, user_type, card_id = dialog.get_input()
            if not username:
                self.log.append("Enrollment cancelled: No username provided")
                return

            self.log.append(f"Enrolling print for {username} ({user_type})")
            self.log.append("Place finger on sensor...")

            # Find the next available location
            location = 1
            while location in self.enrolled_prints:
                location += 1
                if location > 127:
                    self.log.append("No available locations for new prints")
                    return

            if enroll_finger(self.finger, location):
                print(location)
                # Send data to API endpoint
                try:
                    print(location)
                    print(username)
                    print(user_type)
                    
                    payload = {
                        "username": username,
                        "fingerprint_id": location,
                        "user_type": user_type,
                        "card_id": card_id
                    }
                    response = requests.post(f"{self.api_base_url}/employee/add/", json=payload)
                    response.raise_for_status()
                    self.log.append(f"User {username} added to system with fingerprint ID {location}")

                    self.log.append(f"Enrollment successful at location {location}")
                    self.enrolled_prints.add(location)
                    self.save_enrolled_prints()
                except requests.exceptions.RequestException as e:
                    print(e)
                    self.log.append(f"API error: {str(e)}")
                
                self.update_templates()
            else:
                self.log.append("Enrollment failed")
        else:
            self.log.append("Enrollment cancelled")

    def find_print(self):
        if not self.finger:
            self.log.append("Please connect to a fingerprint sensor first")
            return

        self.log.append("Searching for fingerprint...")
        if get_fingerprint(self.finger):
            fingerprint_id = self.finger.finger_id
            self.log.append(f"Detected #{fingerprint_id} with confidence {self.finger.confidence}")
            
            # Check fingerprint against API
            try:
                response = requests.get(f"{self.api_base_url}/employee/get/fingerprint_id/{fingerprint_id}/")
                response.raise_for_status()
                user_data = response.json()
                self.log.append(f"Found user: {user_data['username']} ({user_data['user_type']})")
            except requests.exceptions.RequestException as e:
                self.log.append(f"API error: {str(e)}")
        else:
            self.log.append("Finger not found")

    def save_enrolled_prints(self):
        import json
        with open("enrolled_prints.json", "w") as f:
            json.dump(list(self.enrolled_prints), f)
        self.update_port_list()

    def load_enrolled_prints(self):
        import json
        try:
            with open("enrolled_prints.json", "r") as f:
                self.enrolled_prints = set(json.load(f))
            self.update_port_list()
        except FileNotFoundError:
            self.enrolled_prints = set()

    def delete_print(self):
        if not self.finger:
            self.log.append("Please connect to a fingerprint sensor first")
            return

        self.log.append("Place finger to delete...")
        if get_fingerprint(self.finger):
            fingerprint_id = self.finger.finger_id
            
            # Confirm deletion
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setText(f"Are you sure you want to delete fingerprint #{fingerprint_id}?")
            msg.setWindowTitle("Confirm Deletion")
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if msg.exec() == QMessageBox.StandardButton.Yes:
                try:
                    # Delete from sensor
                    if self.finger.delete_model(fingerprint_id) == adafruit_fingerprint.OK:
                        # Delete from API
                        response = requests.delete(f"{self.api_base_url}/employee/delete/fingerprint_id/{fingerprint_id}/")
                        response.raise_for_status()
                        
                        self.log.append(f"Successfully deleted fingerprint #{fingerprint_id}")
                        self.enrolled_prints.discard(fingerprint_id)
                        self.save_enrolled_prints()
                        self.update_templates()
                    else:
                        self.log.append(f"Failed to delete fingerprint #{fingerprint_id} from sensor")
                except requests.exceptions.RequestException as e:
                    self.log.append(f"API error while deleting: {str(e)}")
        else:
            self.log.append("Finger not found")

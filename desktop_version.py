import sys
import json
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import QTimer, Qt, QUrl
from PyQt5.QtGui import QPixmap
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest

class EmployeeLogApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Employee Log")
        self.setGeometry(100, 100, 400, 600)

        self.current_user = None
        self.start_time = None
        self.is_checked_in = False

        self.init_ui()
        self.init_network()
        self.start_sse_connection()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.status_label = QLabel("Waiting for user data...")
        layout.addWidget(self.status_label)

        self.user_image = QLabel()
        self.user_image.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.user_image)

        self.user_info = QLabel()
        self.user_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.user_info)

        time_layout = QHBoxLayout()
        self.utc_time = QLabel("UTC Time: ")
        self.duration = QLabel("Duration: 00:00:00")
        self.local_time = QLabel("Local Time: ")
        time_layout.addWidget(self.utc_time)
        time_layout.addWidget(self.duration)
        time_layout.addWidget(self.local_time)
        layout.addLayout(time_layout)

        self.session_button = QPushButton("Go to Sessions")
        self.session_button.clicked.connect(self.go_to_sessions)
        layout.addWidget(self.session_button)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time_counters)
        self.timer.start(1000)

    def init_network(self):
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.handle_network_response)

    def start_sse_connection(self):
        self.sse_url = "http://localhost:5000/api/stream-readings"
        self.sse_request = QNetworkRequest(QUrl(self.sse_url))
        self.sse_reply = self.network_manager.get(self.sse_request)
        self.sse_reply.readyRead.connect(self.handle_sse_data)

    def handle_sse_data(self):
        data = self.sse_reply.readAll().data().decode()
        for line in data.split('\n'):
            if line.startswith('data:'):
                self.process_fingerprint_data(json.loads(line[5:]))

    def process_fingerprint_data(self, data):
        if data['user_type'].lower() == 'trainee':
            print("Trainee detected. No action taken.")
            return

        self.status_label.setText("Fingerprint data received!")

        user_id = data['id']
        image_value = data['image']

        # Remove unnecessary fields
        del data['id'], data['card_id'], data['fingerprint_id'], data['created_at'], data['image'], data['user_type']

        # Format and display user info
        formatted_data = f"<b>{data['username']}</b><br>" + "<br>".join(f"{key}: {value}" for key, value in data.items() if key != 'name')
        self.user_info.setText(formatted_data)

        # Load and display user image
        image_url = f"http://127.0.0.1:8000/media/{image_value}"
        self.network_manager.get(QNetworkRequest(QUrl(image_url)))

        # Handle check-in and check-out
        if self.current_user == user_id:
            self.check_out(user_id)
            self.current_user = None
            self.status_label.setText("User checked out.")
            self.duration.setText("Duration: 00:00:00")
        else:
            if self.current_user:
                self.check_out(self.current_user)
            self.check_in(user_id)
            self.current_user = user_id
            self.status_label.setText("User checked in.")

    def check_in(self, user_id):
        url = "http://localhost:8000/atco/check-in/"
        data = {
            "user": user_id,
            "check_in_date": datetime.now().isoformat(),
            "check_type": "fingerprint"
        }
        self.network_manager.post(QNetworkRequest(QUrl(url)), json.dumps(data).encode())

    def check_out(self, user_id):
        url = "http://localhost:8000/atco/check-out/"
        data = {"user": user_id}
        self.network_manager.sendCustomRequest(QNetworkRequest(QUrl(url)), b"PATCH", json.dumps(data).encode())

    def handle_network_response(self, reply):
        if reply.error():
            print(f"Network error: {reply.errorString()}")
        else:
            content_type = reply.header(QNetworkRequest.ContentTypeHeader)
            if content_type.startswith('image/'):
                pixmap = QPixmap()
                pixmap.loadFromData(reply.readAll())
                scaled_pixmap = pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.user_image.setPixmap(scaled_pixmap)
            else:
                print(f"Response: {reply.readAll().data().decode()}")

    def update_time_counters(self):
        now = datetime.now()
        utc_now = now.utcnow()

        self.utc_time.setText(f"UTC Time: {utc_now.strftime('%H:%M:%S')}")
        self.local_time.setText(f"Local Time: {now.strftime('%H:%M:%S')}")

        if self.start_time and self.is_checked_in:
            duration = now - self.start_time
            hours, remainder = divmod(duration.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.duration.setText(f"Duration: {hours:02d}:{minutes:02d}:{seconds:02d}")

    def go_to_sessions(self):
        if self.current_user:
            self.check_out(self.current_user)
            self.current_user = None
        print("Navigating to sessions page...")
        # Here you would typically open a new window or change the current view
        # For this example, we'll just print a message

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = EmployeeLogApp()
    window.show()
    sys.exit(app.exec_())
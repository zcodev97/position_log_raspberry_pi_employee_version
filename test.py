import sys
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QDialog, QLineEdit, QLabel, QMessageBox
from PyQt5.QtWebEngineWidgets import QWebEngineView

class PasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Password Confirmation")
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Enter password to close:"))
        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)
        
        self.submit_button = QPushButton("Submit", self)
        self.submit_button.clicked.connect(self.accept)
        layout.addWidget(self.submit_button)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Web View Desktop App")
        self.setFixedSize(1024, 600)  # Set fixed window size

        # Create a central widget and layout
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        # Create and add the web view
        self.web_view = QWebEngineView()
        self.web_view.setUrl(QUrl("http://127.0.0.1:5000/atco_check_page.html"))
        layout.addWidget(self.web_view)
        
        # Create a horizontal layout for buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()  # Add spacing from left
        
        # Create and add the refresh button
        self.refresh_button = QPushButton("Refresh", self)
        self.refresh_button.clicked.connect(self.refresh_page)
        self.refresh_button.setFixedSize(120, 40)  # Match close button size
        button_layout.addWidget(self.refresh_button)
        
        button_layout.addSpacing(20)  # Add 20px spacing between buttons
        
        # Create and add the close button
        self.close_button = QPushButton("Close")
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: #ff4c4c;
                color: white; 
                font-weight: bold; 
                font-size: 18px;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #ff1a1a;
            }
        """)
        self.close_button.setFixedSize(120, 40)
        self.close_button.clicked.connect(self.close_application)
        button_layout.addWidget(self.close_button)
        
        button_layout.addStretch()  # Add spacing from right
        
        # Add the button layout to the main layout
        layout.addLayout(button_layout)
        
        self.setCentralWidget(central_widget)
        
        # Clear cache on initialization
        self.clear_web_view_cache()  # {{ edit_6 }}

    def clear_web_view_cache(self):  # {{ edit_6 }}
        profile = self.web_view.page().profile()  # Get the profile of the web view
        profile.clearHttpCache()  # Clear the HTTP cache

    def refresh_page(self):  # {{ edit_1 }}
        self.web_view.reload()  # Reload the web view

    def close_application(self):
        dialog = PasswordDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            if dialog.password_input.text() == "12345":
                QApplication.quit()  # This will close the entire application
            else:
                QMessageBox.warning(self, "Incorrect Password", "The password you entered is incorrect.")

    def closeEvent(self, event):
        event.ignore()  # Ignore the close event
        self.close_application()  # Call our custom close method

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
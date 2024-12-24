from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton)

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
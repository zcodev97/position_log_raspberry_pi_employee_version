from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QComboBox
    
class EnrollDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enroll New User")
        self.layout = QVBoxLayout()

        # Initial input field
        username_layout = QHBoxLayout()
        username_layout.addWidget(QLabel("Initial:"))
        self.username_input = QLineEdit()
        username_layout.addWidget(self.username_input)
        self.layout.addLayout(username_layout)

        # Card ID input field
        card_id_layout = QHBoxLayout()
        card_id_layout.addWidget(QLabel("Card ID:"))
        self.card_id_input = QLineEdit()
        card_id_layout.addWidget(self.card_id_input)
        self.layout.addLayout(card_id_layout)

        # User type dropdown
        user_type_layout = QHBoxLayout()
        user_type_layout.addWidget(QLabel("User Type:"))
        self.user_type_dropdown = QComboBox()
        USER_TYPE = [
            'Trainee',
            'Trainer',
            'LCE',
            'Examiner',
            'ATCO',
        ]
        self.user_type_dropdown.addItems(USER_TYPE)
        user_type_layout.addWidget(self.user_type_dropdown)
        self.layout.addLayout(user_type_layout)

        # OK and Cancel buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        self.layout.addLayout(button_layout)

        self.setLayout(self.layout)

    def get_input(self):
        return self.username_input.text(), self.user_type_dropdown.currentText(), self.card_id_input.text()
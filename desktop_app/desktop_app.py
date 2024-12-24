import sys
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
    QHBoxLayout, QWidget, QDialog, QLineEdit, QLabel, QMessageBox, QTabWidget)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from tabs.system_tab import SystemTab
from tabs.admin_tab import AdminTab
from utils.password_dialog import PasswordDialog
 

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Web View Desktop App")
        self.setFixedSize(1024, 600)

        # Create a central widget and layout
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
   
        self.system_tab = SystemTab()
        self.admin_tab = AdminTab()
        self.tab_widget.addTab(self.system_tab, "System")
        self.tab_widget.addTab(self.admin_tab, "Admin")

   
        
        # Add tab widget to main layout
        layout.addWidget(self.tab_widget)
        
        # Create button layout (rest of the button code remains the same)
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
        self.system_tab.clear_web_view_cache()

        # Add tab change event handler
        self.tab_widget.currentChanged.connect(self.handle_tab_change)
        self.last_tab_index = 0  # Keep track of the last selected tab

    def refresh_page(self):
        self.system_tab.refresh_page()

    def close_application(self):
        dialog = PasswordDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            if dialog.password_input.text() == "12345":
                QApplication.quit()
            else:
                QMessageBox.warning(self, "Incorrect Password", "The password you entered is incorrect.")

    def closeEvent(self, event):
        event.ignore()
        self.close_application()

    def handle_tab_change(self, index):
        if index == 1:  # Admin tab index
            dialog = PasswordDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                if dialog.password_input.text() == "12345":
                    self.last_tab_index = index
                    return
                else:
                    QMessageBox.warning(self, "Incorrect Password", "The password you entered is incorrect.")
            # If dialog is rejected or password is incorrect, switch back to the previous tab
            self.tab_widget.setCurrentIndex(self.last_tab_index)
        else:
            self.last_tab_index = index

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
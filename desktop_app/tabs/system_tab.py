from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView

class SystemTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create layout for the tab
        web_layout = QVBoxLayout(self)
        
        # Create and add the web view
        self.web_view = QWebEngineView()
        self.web_view.setUrl(QUrl("http://127.0.0.1:5000/atco_check_page.html"))
        web_layout.addWidget(self.web_view)
        
    def refresh_page(self):
        self.web_view.reload()
        
    def clear_web_view_cache(self):
        profile = self.web_view.page().profile()
        profile.clearHttpCache()
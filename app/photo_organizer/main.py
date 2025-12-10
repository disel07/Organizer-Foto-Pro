import sys
import os

# Ensure the package root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.ui.main_window import MainWindow, QApplication
from src.ui.styles import DARK_THEME

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Apply Theme
    app.setStyle("Fusion")
    
    # Apply Standard Font
    font = app.font()
    font.setPointSize(10)
    app.setFont(font)
    
    # Apply Dark Stylesheet
    app.setStyleSheet(DARK_THEME)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

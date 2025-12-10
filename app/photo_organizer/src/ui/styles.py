
DARK_THEME = """
/* Global Config */
QWidget {
    background-color: #2b2b2b;
    color: #e0e0e0;
    font-family: 'Segoe UI', 'Roboto', sans-serif;
    font-size: 14px;
}

/* Main Window */
QMainWindow {
    background-color: #2b2b2b;
}

/* Buttons */
QPushButton {
    background-color: #3d3d3d;
    color: #ffffff;
    border: 1px solid #555555;
    border-radius: 6px;
    padding: 8px 16px;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #4a4a4a;
    border-color: #666666;
}

QPushButton:pressed {
    background-color: #2a2a2a;
}

QPushButton:disabled {
    background-color: #2b2b2b;
    color: #666666;
    border-color: #444444;
}

/* Primary Action Button (Blue) */
QPushButton#primary {
    background-color: #3d8ec9;
    border: 1px solid #3d8ec9;
    font-weight: bold;
}

QPushButton#primary:hover {
    background-color: #4da3e0;
}

/* Success Action Button (Green) */
QPushButton#success {
    background-color: #4caf50;
    border: 1px solid #4caf50;
    font-weight: bold;
}

QPushButton#success:hover {
    background-color: #5fbd63;
}

/* Tree & Table Views */
QTreeWidget, QTableWidget {
    background-color: #333333;
    alternate-background-color: #3a3a3a;
    border: 1px solid #444444;
    border-radius: 4px;
    gridline-color: #444444;
}

QHeaderView::section {
    background-color: #252525;
    color: #b0b0b0;
    padding: 6px;
    border: none;
    border-right: 1px solid #444444;
    border-bottom: 1px solid #444444;
}

QTreeWidget::item, QTableWidget::item {
    padding: 4px;
}

QTreeWidget::item:selected, QTableWidget::item:selected {
    background-color: #3d8ec9;
    color: white;
}

/* Input Fields */
QLineEdit, QTextEdit {
    background-color: #333333;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 6px;
    color: #ffffff;
}

QLineEdit:focus {
    border: 1px solid #3d8ec9;
}

/* Progress Bar */
QProgressBar {
    border: 1px solid #444444;
    border-radius: 6px;
    text-align: center;
    background-color: #333333;
    height: 24px;
}

QProgressBar::chunk {
    background-color: #4caf50;
    border-radius: 5px;
}

/* GroupBox */
QGroupBox {
    border: 1px solid #555555;
    border-radius: 6px;
    margin-top: 24px;
    font-weight: bold;
    color: #b0b0b0;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 10px;
    left: 10px;
}
"""

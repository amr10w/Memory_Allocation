# ui/styles.py

HOVER_ONLY_BUTTON_STYLE = """
    QPushButton {
        background-color: transparent;
        color: #555;
        border: 1px solid #ccc;
        border-radius: 4px;
        padding: 5px 14px;
        font-size: 12px;
    }
    QPushButton:hover {
        background-color: #2D8CFF;
        color: white;
        border: 1px solid #2D8CFF;
    }
"""

GLOBAL_STYLE = """
    QMainWindow {
        background-color: #F5F7FA;
    }
    QLabel {
        font-size: 13px;
    }
    QGroupBox {
        font-weight: bold;
        font-size: 13px;
        border: 1px solid #ccc;
        border-radius: 6px;
        margin-top: 10px;
        padding-top: 14px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
    }
    QPushButton {
        background-color: #2D8CFF;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 6px 16px;
        font-size: 13px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #1A6FDD;
    }
    QPushButton:pressed {
        background-color: #155CBB;
    }
    QLineEdit, QComboBox {
        border: 1px solid #ccc;
        border-radius: 4px;
        padding: 5px 8px;
        font-size: 13px;
        background-color: white;
    }
    QLineEdit:focus, QComboBox:focus {
        border: 1px solid #2D8CFF;
    }
    QListWidget {
        border: 1px solid #ddd;
        border-radius: 4px;
        font-size: 12px;
        background-color: white;
    }
"""
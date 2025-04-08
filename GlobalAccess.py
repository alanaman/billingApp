from PyQt6.QtCore import QObject, pyqtSignal, QDateTime

class GlobalData(QObject):
    status_msg = pyqtSignal(str)  # Signal carrying an error message

    _instance = None  # Singleton instance

    @classmethod
    def I(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self, parent = None):
        super().__init__(parent)
        self.username = None
        self.elevation = None

        # create log file if not exists
        self.log_file = open("log.txt", "a")

    def SetUser(self, username, elevation):
        self.username = username
        self.elevation = elevation

    def Log(self, message: str):
        self.status_msg.emit(message)
        # add to log file with timestamp
        timestamp = QDateTime.currentDateTime().toString()
        self.log_file.write(f"{timestamp} : {message}\n")
        self.log_file.flush()

def LogMsg(message:str):
    GlobalData.I().Log(message)

def GetElevation():
    return GlobalData.I().elevation

def GetUser():
    return GlobalData.I().username

import os
import sys
from pathlib import Path


def resource_path(relative_path):
    """Get the absolute path to the resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # If we are still in dev mode, make our paths start from the folder this file is in
        base_path = Path(__file__).parent

    return os.path.join(base_path, relative_path)
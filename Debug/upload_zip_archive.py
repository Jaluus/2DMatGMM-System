"""
This is a debug file, only run it if you know what you are doing.
"""
import os
import requests

SERVER_URL = "http://localhost:4999/upload"
SCAN_DIRECTORY = "C:/Path/To/Scan/Directory"
SCAN_NAME = "SCAN_NAME.zip"

scan_directory = os.path.join(SCAN_DIRECTORY, SCAN_NAME)
with open(scan_directory, "rb") as f:
    requests.post(SERVER_URL, files={"zip": f})

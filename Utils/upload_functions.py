import shutil
import requests


def upload_directory(scan_dir: str, url: str) -> None:
    """
    Generates a zip file of a directory and uploads it to a server\n
    Sends a POST request to the server with the zip file as a file

    Args:
        scan_dir (str): The directory to upload
        url (str): The url to upload to
    """
    shutil.make_archive(scan_dir, "zip", scan_dir)

    with open(scan_dir + ".zip", "rb") as f:
        requests.post(url, files={"zip": f})

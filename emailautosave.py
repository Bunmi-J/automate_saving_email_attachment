import imaplib
import email
import io
import os
import configparser

# Create a ConfigParser object
config = configparser.ConfigParser()

# Read the configuration file
config.read('config.py')

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from config import EMAIL_HOST, EMAIL_USER, EMAIL_PASS, TRUSTED_SENDER, DRIVE_FOLDER_ID

print(EMAIL_HOST, EMAIL_USER, EMAIL_PASS, TRUSTED_SENDER, DRIVE_FOLDER_ID)




# --- Gmail Login ---
def login_email():
    mail = imaplib.IMAP4_SSL(EMAIL_HOST)
    mail.login(EMAIL_USER, EMAIL_PASS)
    mail.select("inbox")
    return mail

# --- Check Email and Get Attachment ---
def fetch_attachment(mail):
    typ, data = mail.search(None, f'(FROM "{TRUSTED_SENDER}")')
    for num in data[0].split():
        typ, msg_data = mail.fetch(num, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])
        for part in msg.walk():
            if part.get_content_maintype() == "multipart":
                continue
            if part.get("Content-Disposition"):
                filename = part.get_filename()
                if filename and (filename.endswith(".csv") or filename.endswith(".xlsx")):
                    file_data = part.get_payload(decode=True)
                    return filename, io.BytesIO(file_data)
    return None, None

# --- Google Drive Upload ---
def upload_to_drive(filename, file_stream):
    creds = Credentials.from_authorized_user_file("token.json", ["https://www.googleapis.com/auth/drive"])
    drive_service = build("drive", "v3", credentials=creds)
    file_metadata = {"name": filename, "parents": [DRIVE_FOLDER_ID]}
    media = MediaIoBaseUpload(file_stream, mimetype="application/octet-stream")
    drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()

# --- Main Workflow ---
def automate_email_to_drive():
    mail = login_email()
    filename, file_stream = fetch_attachment(mail)
    if filename:
        upload_to_drive(filename, file_stream)
        print(f"{filename} uploaded successfully.")
    else:
        print("No new file from trusted sender.")

automate_email_to_drive()
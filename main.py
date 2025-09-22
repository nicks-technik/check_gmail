import os
import time
from collections import defaultdict
import logging
import coloredlogs
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv

from dateutil import parser

load_dotenv()

# Set up logging
log_file = "gmail_check.log"
log_level = logging.INFO
log_format = "%(asctime)s - %(levelname)s - %(message)s"

# Use coloredlogs for console logging
coloredlogs.install(level=log_level, fmt=log_format)

# Create a logger instance
logger = logging.getLogger(__name__)

# Create a file handler
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(log_level)
file_handler.setFormatter(logging.Formatter(log_format))

# Add the file handler to the logger
logger.addHandler(file_handler)

# If modifying these SCOPES, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def get_gmail_service():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    service = build("gmail", "v1", credentials=creds)
    return service


def main():
    """
    Fetches emails from the user's Gmail account, identifies duplicates based on
    subject and timestamp, and logs them.
    """
    service = get_gmail_service()

    # Call the Gmail API
    messages = []
    next_page_token = None
    page_count = 0
    while True:
        page_count += 1
        logger.info(f"Fetching page {page_count} of emails...")
        results = (
            service.users()
            .messages()
            .list(userId="me", pageToken=next_page_token)
            .execute()
        )
        messages.extend(results.get("messages", []))
        logger.info(
            f"Total emails fetched so far: {len(messages)} / {results.get('resultSizeEstimate')}"
        )
        next_page_token = results.get("nextPageToken")
        if not next_page_token:
            break
        time.sleep(1)  # Add a pause to avoid hitting rate limits

    if not messages:
        logger.info("No messages found.")
        return

    logger.info(f"Processing {len(messages)} emails...")

    emails = defaultdict(list)
    for i, message in enumerate(messages):
        if (i + 1) % 10 == 0:
            logger.info(f"Processing email {i + 1}/{len(messages)}...")
        msg = service.users().messages().get(userId="me", id=message["id"]).execute()
        headers = msg["payload"]["headers"]
        subject = next(
            (header["value"] for header in headers if header["name"] == "Subject"),
            "(No Subject)",
        )
        date_str = next(
            (header["value"] for header in headers if header["name"] == "Date"), None
        )
        if not date_str:
            logger.warning(f"Could not find date for message {message['id']}")
            continue
        # Parse the date string
        try:
            date_obj = parser.parse(date_str)
        except ValueError:
            logger.warning(f"Could not parse date: {date_str}")
            continue

        size = msg["sizeEstimate"]
        emails[(subject, date_obj.date(), date_obj.hour, date_obj.minute)].append(size)
        time.sleep(0.1)  # Add a small pause between each email

    logger.info(f"Found {len(emails)} unique email groups.")
    duplicate_count = 0
    for (subject, date, hour, minute), sizes in emails.items():
        if len(sizes) > 1 and len(set(sizes)) > 1:
            duplicate_count += 1
            logger.info("Duplicate email found with different sizes:")
            logger.info(f"  Subject: {subject}")
            logger.info(f"  Date: {date}")
            logger.info(f"  Time: {hour:02d}:{minute:02d}")

    logger.info(f"Found {duplicate_count} duplicate email groups.")
    logger.info("Script finished.")


if __name__ == "__main__":
    logger.info("Starting script...")
    main()

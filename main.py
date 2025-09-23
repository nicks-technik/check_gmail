import logging
import os
import time
from collections import defaultdict

import coloredlogs
from dateutil import parser
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()

# Configuration
# Load configuration from environment variables or use default values.
LOG_FILE = os.getenv("LOG_FILE", "gmail_check.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
CONSOLE_LOG_LEVEL = os.getenv("CONSOLE_LOG_LEVEL", "INFO")
SCOPES = os.getenv("SCOPES", "https://www.googleapis.com/auth/gmail.readonly").split(
    ","
)
FETCH_SLEEP = float(os.getenv("FETCH_SLEEP", 1))
PROCESS_SLEEP = float(os.getenv("PROCESS_SLEEP", 0.1))


def setup_logging(log_file, file_log_level, console_log_level):
    """Sets up logging to both console (with colors) and a file."""
    # Define the format for log messages.
    log_format = "%(asctime)s - %(levelname)s - %(message)s"

    # Install coloredlogs for console logging. This automatically adds a handler to the root logger.
    coloredlogs.install(level=console_log_level, fmt=log_format)

    # Get the root logger. All log messages will pass through this logger.
    root_logger = logging.getLogger()
    # Set the overall minimum logging level for the root logger.
    root_logger.setLevel(
        logging.DEBUG
    )  # Set to DEBUG to capture all messages, then filter by handler.

    # Create a file handler to write logs to a specified file.
    file_handler = logging.FileHandler(log_file)
    # Set the logging level for the file handler.
    file_handler.setLevel(file_log_level)
    # Set the formatter for the file handler.
    file_handler.setFormatter(logging.Formatter(log_format))

    # Add the file handler to the root logger.
    # This ensures that messages are written to the file in addition to the console.
    root_logger.addHandler(file_handler)


# Set up logging based on configuration.
setup_logging(LOG_FILE, LOG_LEVEL, CONSOLE_LOG_LEVEL)
# Get a module-specific logger instance. This is good practice for larger applications.
logger = logging.getLogger(__name__)


def get_gmail_service():
    """Authenticates with the Gmail API and returns a service object.

    The function handles OAuth2 authentication flow, including refreshing tokens
    and saving credentials for future use.
    """
    creds = None
    # Check if a token.json file exists, which stores user's access and refresh tokens.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If no valid credentials exist, or if they are expired, initiate the OAuth flow.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Refresh the token if it's expired and a refresh token is available.
            creds.refresh(Request())
        else:
            # Start the OAuth flow to get new credentials.
            # The client_secrets.json file (renamed to credentials.json) is required here.
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            # Run a local server to handle the OAuth redirect.
            creds = flow.run_local_server(port=0)
        # Save the newly obtained credentials for the next run.
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    # Build and return the Gmail API service object.
    service = build("gmail", "v1", credentials=creds)
    return service


def fetch_all_messages(service) -> list:
    """Fetches all email messages from the user's Gmail account, handling pagination.

    Args:
        service: The authenticated Gmail API service object.

    Returns:
        A list of all fetched email messages (each containing at least an 'id').
    """
    messages = []
    next_page_token = None
    page_count = 0
    # Loop to fetch all pages of messages until no more pages are available.
    while True:
        page_count += 1
        logger.info(f"Fetching page {page_count} of emails...")
        # Make an API request to list messages.
        # 'pageToken' is used for pagination.
        # 'fields' is used to limit the data returned, improving performance.
        results = (
            service.users()
            .messages()
            .list(
                userId="me",
                pageToken=next_page_token,
                # pageToken=next_page_token,
                # fields="nextPageToken,messages(id)",
            )
            .execute()
        )
        # Extend the messages list with messages from the current page.
        messages.extend(results.get("messages", []))
        # Log the current progress of fetched emails.
        logger.info(
            f"Total emails fetched so far: {len(messages)} / {results.get('resultSizeEstimate')}"
        )
        # Get the token for the next page.
        next_page_token = results.get("nextPageToken")
        # If no next page token, break the loop.
        if not next_page_token:
            break
        # Pause to avoid hitting Gmail API rate limits.
        time.sleep(FETCH_SLEEP)
    return messages


def get_email_details(service, message):
    """Fetches full details for a single email message and extracts subject, date, and size.

    Args:
        service: The authenticated Gmail API service object.
        message: A dictionary containing at least the 'id' of the email message.

    Returns:
        A tuple containing (subject, date_object, size) or (None, None, None) if
        details cannot be extracted.
    """
    # Fetch the full message details.
    msg = service.users().messages().get(userId="me", id=message["id"]).execute()
    logger.debug(f"Fetching details for message {message['id']}...")
    logger.debug(f"msg: {msg}")
    headers = msg["payload"]["headers"]

    # Extract the subject from headers. Defaults to "(No Subject)" if not found.
    subject = next(
        (header["value"] for header in headers if header["name"] == "Subject"),
        "(No Subject)",
    )
    # Extract the date string from headers. Defaults to None if not found.
    date_str = next(
        (header["value"] for header in headers if header["name"] == "Date"), None
    )

    # If date string is not found, log a warning and return None for date-related values.
    if not date_str:
        logger.warning(f"Could not find date for message {message['id']}")
        return None, None, None

    # Parse the date string into a datetime object.
    try:
        date_obj = parser.parse(date_str)
    except ValueError:
        # If date parsing fails, log a warning and return None for date-related values.
        logger.warning(f"Could not parse date: {date_str}")
        return None, None, None

    # Extract the estimated size of the message.
    size = msg["sizeEstimate"]
    return subject, date_obj, size


def process_messages(service, messages):
    """Processes a list of messages to group them by subject and timestamp.

    Args:
        service: The authenticated Gmail API service object.
        messages: A list of email messages (each containing at least an 'id').

    Returns:
        A defaultdict where keys are (subject, date, hour, minute) tuples and
        values are lists of email sizes for that group.
    """
    if not messages:
        logger.info("No messages found to process.")
        return None

    logger.info(f"Processing {len(messages)} emails...")

    # defaultdict to store emails grouped by subject and timestamp.
    # The value is a list of sizes, allowing us to detect different attachments.
    emails = defaultdict(list)
    for i, message in enumerate(messages):
        # Log progress every 10 emails.
        if (i + 1) % 10 == 0:
            logger.info(f"Processing email {i + 1}/{len(messages)}...")

        # Get detailed information for the current email.
        subject, date_obj, size = get_email_details(service, message)
        # Skip processing if essential details (subject, date, size) are missing.
        if subject is None or date_obj is None or size is None:
            continue

        # Group emails by subject, date (day), hour, and minute.
        # This forms the basis for identifying potential duplicates.
        emails[(subject, date_obj.date(), date_obj.hour, date_obj.minute)].append(size)
        # Pause to avoid hitting Gmail API rate limits when fetching individual message details.
        time.sleep(PROCESS_SLEEP)
    return emails


def find_and_log_duplicates(emails):
    """Identifies and logs duplicate emails with different sizes.

    Args:
        emails: A defaultdict containing grouped email information.
    """
    if not emails:
        return

    logger.info(f"Found {len(emails)} unique email groups.")
    duplicate_count = 0
    # Iterate through the grouped emails.
    for (subject, date, hour, minute), sizes in emails.items():
        # A duplicate is identified if there's more than one email in the group
        # AND they have different sizes (implying different attachments).
        if len(sizes) > 1 and len(set(sizes)) > 1:
            duplicate_count += 1
            logger.info("Duplicate email found with different sizes:")
            logger.info(f"  Subject:\t{subject}")
            logger.info(f"  Date:\t{date}")
            logger.info(f"  Time:\t{hour:02d}:{minute:02d}")
            logger.info(f"  Sizes:\t{', '.join(map(str, sizes))}")

    logger.info(f"Found {duplicate_count} duplicate email groups.")


def main():
    """
    Main function to run the Gmail duplicate checker.
    Orchestrates fetching, processing, and logging of duplicate emails.
    """
    service = get_gmail_service()
    messages = fetch_all_messages(service)
    emails = process_messages(service, messages)
    find_and_log_duplicates(emails)


if __name__ == "__main__":
    logger.info("Starting script...")
    main()
    logger.info("Script finished.")

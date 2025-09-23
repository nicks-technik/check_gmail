# Check Gmail for Duplicate Emails

This program uses the Gmail API to identify duplicate emails with the same subject and timestamp but different sizes (due to varying attachments).


**Set up Gmail API credentials:**

    - Follow the instructions in the [Google Cloud documentation](https://developers.google.com/gmail/api/quickstart/python) to create a new project, enable the Gmail API, and download your `credentials.json` file.
    - Place the `credentials.json` file in the root of this project.

**Configuration (Optional):**

    You can configure the script's behavior by creating a `.env` file in the project root. Copy the `.env.example` file and modify the values:

    ```bash
    cp .env.example .env
    ```

    Available options:

    - `LOG_FILE`: Path to the log file (default: `gmail_check.log`)
    - `LOG_LEVEL`: Logging level for the log file (e.g., `INFO`, `DEBUG`, `WARNING`, `ERROR`) (default: `INFO`)
    - `CONSOLE_LOG_LEVEL`: Logging level for the console (e.g., `INFO`, `DEBUG`, `WARNING`, `ERROR`) (default: `INFO`)
    - `SCOPES`: Comma-separated Gmail API scopes (default: `https://www.googleapis.com/auth/gmail.readonly`)
    - `FETCH_SLEEP`: Sleep duration in seconds between fetching email pages (default: `1`)
    - `PROCESS_SLEEP`: Sleep duration in seconds between processing individual emails (default: `0.1`)

## Usage

Run the program from the command line:

```bash
uv run main.py
```

The program will then:

1.  Authenticate with the Gmail API.
2.  Fetch your emails.
3.  Check for duplicates based on subject and time.
4.  Log the subject and date/time of any duplicates found.

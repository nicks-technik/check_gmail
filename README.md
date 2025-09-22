# Check Gmail for Duplicate Emails

This program uses the Gmail API to identify duplicate emails with the same subject and timestamp but different sizes (due to varying attachments).

## Setup

1.  **Install `uv`:**

    ```bash
    pip install uv
    ```

2.  **Create a virtual environment:**

    ```bash
    uv venv
    ```

3.  **Activate the virtual environment:**

    ```bash
    source .venv/bin/activate
    ```

4.  **Install dependencies:**

    ```bash
    uv pip install .
    ```

5.  **Set up Gmail API credentials:**

    - Follow the instructions in the [Google Cloud documentation](https://developers.google.com/gmail/api/quickstart/python) to create a new project, enable the Gmail API, and download your `credentials.json` file.
    - Place the `credentials.json` file in the root of this project.

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

# Gemini Best Practices

This document outlines best practices for interacting with Gemini, the AI assistant, to ensure efficient and effective collaboration on this project.

## Project Initialization

- Start by providing a clear and concise overview of the project goals.
- Specify the desired technology stack, including programming languages, frameworks, and key libraries.
- Outline the desired project structure and any existing conventions.

## Development Workflow

- **Be specific in your requests:** Instead of "write some code," say "create a Python function that takes a user's email and returns their profile from the database."
- **Provide context:** When asking for code changes, reference the relevant files and functions.
- **One task at a time:** Focus on a single, well-defined task in each prompt to avoid ambiguity.
- **Review and verify:** After Gemini makes changes, review the code and run tests to ensure it meets your expectations.

## Tool Usage

- **`uv` for project management:** Use `uv` to manage dependencies and run scripts. For example, use `uv run` to execute scripts.
- **`dotenv` for environment variables:** Store sensitive information like API keys in a `.env` file. Also, use it to configure script behavior (e.g., `FETCH_SLEEP`, `PROCESS_SLEEP`, `LOG_LEVEL`).

## Communication

- **Use Markdown for formatting:** Format code blocks, lists, and headings to improve readability.
- **Be patient:** Complex tasks may take some time for Gemini to process.
- **Provide feedback:** If Gemini's output is not what you expected, provide clear and constructive feedback.

By following these best practices, you can help Gemini understand your needs and provide you with the best possible assistance.
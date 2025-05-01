# AIContextBuilder
Quickly bundles text files, images, and PDFs from a directory into a single output (clipboard text, .txt file, or consolidated PDF). Ideal for packaging project context for AI prompts or creating simple content digests.

A Python script to quickly consolidate content from a directory (text files, images, PDFs) into a single output (clipboard, .txt, or .pdf). Primarily designed to streamline gathering project context (code, config, logs) for easy pasting into Large Language Models (LLMs) or other AI tools, eliminating tedious manual copy-pasting. Supports text extraction, image embedding (in PDF), and PDF merging.

## The Problem

When interacting with AI assistants (like ChatGPT, Claude, Copilot, etc.) for coding help, debugging, or documentation, you often need to provide context from multiple files in your project (source code, configuration files, error logs, documentation snippets). Manually opening each file, copying the relevant content, and pasting it into the prompt is time-consuming and error-prone.

## The Solution

`AIContextBuilder` automates this process. Point it at a directory, choose your desired output format, and it will bundle the content for you:

*   **Clipboard:** Copies all text content directly to your clipboard, ready to paste.
*   **Text File (.txt):** Saves all text content into a single, well-formatted text file.
*   **PDF File (.pdf):** Creates a comprehensive PDF document containing:
    *   Extracted text from supported text files.
    *   Embedded images (requires Pillow).
    *   Merged content from existing PDF files found in the directory (requires pypdf).

This makes providing extensive context to AI tools significantly faster and easier.

## Features

*   Processes files within a specified directory.
*   Reads common text-based files (e.g., `.py`, `.js`, `.txt`, `.md`, `.json`, `.yaml`, `.log` - configurable).
*   Handles UTF-8 and Latin-1 encodings for text files.
*   Skips text files larger than a configurable size limit (default: 1MB) to avoid excessive output.
*   Outputs consolidated text content to the **Clipboard** (requires `pyperclip`).
*   Saves consolidated text content to a **.txt file**.
*   Generates a consolidated **.pdf file** (requires `fpdf2`):
    *   Includes a title page with directory information.
    *   Adds text content from files, formatted for readability.
    *   Embeds common image types (e.g., `.png`, `.jpg`, `.gif` - requires `Pillow`).
    *   Appends existing PDF files found in the directory to the end of the generated report (requires `pypdf`).
*   Provides informative console output during processing.
*   Generates sensible default output filenames including timestamps.
*   Cross-platform (tested on Windows, should work on macOS/Linux).

## Requirements

*   Python 3.7+
*   `pip` (Python package installer)

## Installation

1.  **Clone the repository (or download the script):**
    ```bash
    git clone https://github.com/Sinnero/AIContextBuilder.git
    cd AIContextBuilder
    ```
    *Or just download `run.py`.*

2.  **Install required libraries:**
    It's highly recommended to use a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```
    Then install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```
    or
    ```bash
    pip install fpdf2 Pillow pypdf pyperclip
    ```

## Usage

1.  **Run the script from your terminal:**
    ```bash
    python run.py
    ```

2.  **Follow the prompts:**
    *   **Enter the directory path:** Provide the full or relative path to the directory you want to process.
    *   **Choose an output format:** Enter `1` for Clipboard, `2` for .txt File, or `3` for PDF File.
    *   **(If saving to file):** Enter a desired filename or press Enter to accept the default suggested filename.

3.  **Check the output:**
    *   If you chose Clipboard, the text content should now be ready to paste. Be aware of potential clipboard size limitations for very large outputs.
    *   If you chose .txt or .pdf, the file will be saved in the location where you ran the script (or according to the path you provided in the filename prompt).

## Configuration (Optional)

You can modify the script's behavior by changing the constants defined near the top of `run.py`:

*   `MAX_SIZE_FOR_TEXT_OUTPUT`: Maximum size (in bytes) for individual text files to be included.
*   `TEXT_EXTENSIONS`: Set of file extensions treated as text files.
*   `IMAGE_EXTENSIONS`: Set of file extensions treated as images (for PDF embedding).
*   `CLIPBOARD_WARN_THRESHOLD`: Character count above which a warning is shown for clipboard output.

## Contributing

Contributions are welcome! If you have suggestions for improvements or find a bug, please feel free to:

1.  Open an issue to discuss the change.
2.  Submit a pull request with your proposed changes.

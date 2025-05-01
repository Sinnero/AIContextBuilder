import os
import sys
import time
import traceback
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from PIL import Image
from pypdf import PdfWriter, PdfReader
from pypdf.errors import PdfReadError
import pyperclip

# --- Constants ---
MAX_SIZE_FOR_TEXT_OUTPUT = 1 * 1024 * 1024  # 1 MB
TEXT_EXTENSIONS = {'.txt', '.py', '.js', '.html', '.css', '.md', '.json', '.xml', '.yaml', '.yml', '.csv', '.log', '.sh', '.bat', '.java', '.c', '.cpp', '.h', '.hpp', '.rb', '.php'}
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'}
PDF_EXTENSION = '.pdf'
CLIPBOARD_WARN_THRESHOLD = 100000 # Warn if text string exceeds this for clipboard (Note: this specific warning remains as it's about data size, not import availability)

# --- Function: Get Text String ---
def get_files_content_string(directory_path):
    """
    Reads text files (up to size limit) in directory, returns formatted string.
    """
    if not os.path.isdir(directory_path):
        print(f"Error: The path '{directory_path}' is not a valid directory.", file=sys.stderr)
        return None
    file_data_list = []
    processed_files_count = 0
    skipped_files_count = 0
    skipped_large_files_count = 0
    try:
        all_items = os.listdir(directory_path)
        print(f"Scanning directory for text files (max {MAX_SIZE_FOR_TEXT_OUTPUT / 1024 / 1024:.1f} MB each)...")
        for item_name in all_items:
            full_path = os.path.join(directory_path, item_name)
            if os.path.isfile(full_path):
                try:
                    file_size = os.path.getsize(full_path)
                    _, ext = os.path.splitext(item_name)
                    is_likely_text = ext.lower() in TEXT_EXTENSIONS or not ext
                    if is_likely_text and file_size <= MAX_SIZE_FOR_TEXT_OUTPUT:
                        file_content = None
                        try:
                            with open(full_path, 'r', encoding='utf-8') as f: file_content = f.read()
                        except UnicodeDecodeError:
                            try:
                                with open(full_path, 'r', encoding='latin-1') as f: file_content = f.read()
                            except Exception as e_fallback:
                                print(f"  - Warning: Read error (fallback) '{item_name}': {e_fallback}", file=sys.stderr); skipped_files_count += 1
                        except (IOError, PermissionError) as e_read:
                            print(f"  - Warning: Read error '{item_name}': {e_read}", file=sys.stderr); skipped_files_count += 1
                        except Exception as e_other:
                            print(f"  - Warning: Unexpected read error '{item_name}': {e_other}", file=sys.stderr); skipped_files_count += 1
                        if file_content is not None:
                            escaped_content = file_content.replace("'", "\\'")
                            file_data_list.append(f"{item_name} '{escaped_content}'")
                            processed_files_count += 1
                    elif file_size > MAX_SIZE_FOR_TEXT_OUTPUT and is_likely_text:
                         skipped_large_files_count += 1
                except OSError as e_stat:
                     print(f"  - Warning: Stat error '{item_name}': {e_stat}", file=sys.stderr); skipped_files_count += 1
    except OSError as e:
        print(f"Error accessing directory '{directory_path}': {e}", file=sys.stderr); return None
    print(f"Text String Output: Processed {processed_files_count} files.")
    if skipped_large_files_count > 0: print(f"Text String Output: Skipped {skipped_large_files_count} large files.")
    if skipped_files_count > 0: print(f"Text String Output: Skipped {skipped_files_count} files due to errors.")
    return "\n".join(file_data_list)

# --- Function: Create PDF ---
def create_consolidated_pdf(directory_path, output_filename):
    """
    Creates a single PDF containing content of files in the directory.
    Requires fpdf2, Pillow, and pypdf to be installed.
    """
    if not os.path.isdir(directory_path):
        print(f"Error: The path '{directory_path}' is not a valid directory.", file=sys.stderr)
        return False

    print(f"\nStarting PDF generation for directory: {directory_path}")
    print(f"Output file: {output_filename}")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(15, 15, 15)
    base_font = "Helvetica"
    base_font_size = 10
    pdf.set_font(base_font, size=base_font_size)

    original_pdf_files = []
    processed_files_count = 0; skipped_files_count = 0; unsupported_files_count = 0

    pdf.add_page()
    pdf.set_font(base_font, 'B', 16)
    pdf.cell(0, 10, f"Consolidated Content Report", border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(5)
    pdf.set_font(base_font, '', 12)
    pdf.multi_cell(0, 6, f"Source Directory: {os.path.abspath(directory_path)}", border=0, align='L')
    pdf.ln(10)

    try:
        all_items = sorted(os.listdir(directory_path))
        print(f"Found {len(all_items)} items. Processing for PDF content...")
        for item_name in all_items:
            full_path = os.path.join(directory_path, item_name)
            if not os.path.isfile(full_path): continue
            processed_files_count += 1
            print(f"  - Processing: {item_name}")
            _, ext = os.path.splitext(item_name); ext = ext.lower()
            pdf.add_page()
            pdf.set_font(base_font, 'B', 12)
            pdf.cell(0, 8, f"--- File: {item_name} ---", border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
            pdf.ln(4)
            pdf.set_font(base_font, size=base_font_size)
            try:
                if ext in TEXT_EXTENSIONS:
                    content = "[Error reading file]"
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f: content = f.read()
                    except UnicodeDecodeError:
                        try:
                            with open(full_path, 'r', encoding='latin-1') as f: content = f.read()
                        except Exception as e_read: content = f"[Read Error Latin1: {e_read}]"
                    except Exception as e_read: content = f"[Read Error UTF8: {e_read}]"
                    try:
                        content_cleaned = content.replace('\r\n', '\n').replace('\r', '\n')
                        # Encode to latin-1 replacing unknown characters, then decode back.
                        # This ensures fpdf (which expects latin-1 by default) doesn't crash.
                        pdf.multi_cell(0, 5, content_cleaned.encode('latin-1', 'replace').decode('latin-1'))
                    except Exception as e_pdf_text:
                        print(f"    Warn: PDF Text Add Fail '{item_name}': {e_pdf_text}", file=sys.stderr)
                        pdf.multi_cell(0, 5, "[Error adding text to PDF]")
                elif ext in IMAGE_EXTENSIONS:
                     # Assumes Pillow is installed, otherwise Image.open will fail
                    try:
                        img = Image.open(full_path); img_w, img_h = img.size; img.close()
                        available_width = pdf.w - pdf.l_margin - pdf.r_margin
                        if img_w <= 0: raise ValueError("Invalid image width")
                        aspect_ratio = img_h / img_w
                        display_width = min(img_w, available_width); display_height = display_width * aspect_ratio
                        current_y = pdf.get_y(); available_height = pdf.h - pdf.t_margin - pdf.b_margin - current_y
                        # Check if image needs shrink to fit remaining page height
                        if display_height > available_height and available_height > 20: # Need some space to be worth resizing
                             display_height = available_height
                             display_width = display_height / aspect_ratio
                        if display_width > 0 and display_height > 0:
                           pdf.image(full_path, w=display_width, h=display_height)
                        else: raise ValueError(f"Invalid calculated display dimensions ({display_width}x{display_height})")
                    except Exception as e_img:
                        print(f"    Warn: Image Fail '{item_name}': {e_img}", file=sys.stderr)
                        pdf.set_font(base_font, 'I', base_font_size); pdf.multi_cell(0, 5, f"[Error processing/adding image: {e_img}]"); pdf.set_font(base_font, size=base_font_size)
                elif ext == PDF_EXTENSION:
                    # Assumes pypdf is installed
                    pdf_path = full_path
                    original_pdf_files.append(pdf_path)
                    pdf.set_font(base_font, 'I', base_font_size); pdf.multi_cell(0, 5, f"[Note: Merging '{os.path.basename(pdf_path)}' at end.]"); pdf.set_font(base_font, size=base_font_size)
                else:
                    unsupported_files_count += 1
                    msg = "Unsupported file type"
                    pdf.set_font(base_font, 'I', base_font_size); pdf.multi_cell(0, 5, f"[{msg}. Cannot embed.]"); pdf.set_font(base_font, size=base_font_size)
            except Exception as e_file_proc:
                skipped_files_count += 1
                print(f"    ERROR Processing File '{item_name}': {e_file_proc}", file=sys.stderr); traceback.print_exc(file=sys.stderr)
                pdf.set_font('helvetica', 'B', 10); pdf.set_text_color(255, 0, 0); pdf.multi_cell(0, 5, f"[!!! CRITICAL FILE ERROR: {e_file_proc} !!!]"); pdf.set_text_color(0, 0, 0); pdf.set_font(base_font, size=base_font_size)

        temp_pdf_filename = f"__temp_pdf_content_{time.strftime('%Y%m%d_%H%M%S')}.pdf"
        try:
            pdf.output(temp_pdf_filename)
            print(f"\nGenerated base PDF content to temporary file: {temp_pdf_filename}")
        except Exception as e_save_temp:
            print(f"ERROR saving temp PDF: {e_save_temp}", file=sys.stderr); traceback.print_exc(file=sys.stderr)
            if os.path.exists(temp_pdf_filename):
                try: os.remove(temp_pdf_filename)
                except OSError: pass
            return False

        final_pdf_path = os.path.abspath(output_filename)
        # Assumes pypdf is available for PdfWriter
        merger = PdfWriter(); success = False
        try:
            print(f"Appending generated content from temp file...")
            try: merger.append(temp_pdf_filename)
            except Exception as e_append_temp: print(f"ERROR appending temp PDF: {e_append_temp}", file=sys.stderr); raise

            if original_pdf_files:
                print(f"Appending content from {len(original_pdf_files)} original PDF file(s)...")
                for pdf_path in original_pdf_files:
                    base_pdf_name = os.path.basename(pdf_path); print(f"  - Appending: {base_pdf_name}")
                    try:
                        # Appending the original PDF file content
                        merger.append(pdf_path)
                    except PdfReadError as e_read_pdf:
                        print(f"    Warn: Skip unreadable PDF '{base_pdf_name}': {e_read_pdf}", file=sys.stderr)
                    except Exception as e_append_pdf:
                        print(f"    Warn: Skip append error PDF '{base_pdf_name}': {e_append_pdf}", file=sys.stderr)
                        # traceback.print_exc(file=sys.stderr) # Uncomment for more detail on append errors

            print(f"Writing final merged PDF to: {final_pdf_path}")
            with open(final_pdf_path, "wb") as f_out: merger.write(f_out)
            success = True; print("PDF generation successful.")

        except Exception as e_merge:
            print(f"ERROR during PDF merge/write: {e_merge}", file=sys.stderr); traceback.print_exc(file=sys.stderr); success = False
        finally:
            print("Cleaning up...");
            try: merger.close()
            except Exception as e_close: print(f"  Warn: Error closing PDF merger: {e_close}", file=sys.stderr)
            if os.path.exists(temp_pdf_filename):
                try: os.remove(temp_pdf_filename); print(f"  - Removed temp file: {temp_pdf_filename}")
                except OSError as e_del:
                    print(f"  Warn: Could not delete temp file '{temp_pdf_filename}': {e_del}", file=sys.stderr)

        print(f"\nPDF Generation Summary:"); print(f"  Processed {processed_files_count} files.")
        if original_pdf_files: print(f"  Merged {len(original_pdf_files)} original PDFs."); # Or attempted to merge
        if unsupported_files_count > 0: print(f"  {unsupported_files_count} unsupported file types.");
        if skipped_files_count > 0: print(f"  {skipped_files_count} skipped files (errors).")
        return success

    except OSError as e_list: print(f"Error listing dir for PDF: {e_list}", file=sys.stderr); return False
    except Exception as e_main_pdf: print(f"Unexpected PDF generation error: {e_main_pdf}", file=sys.stderr); traceback.print_exc(file=sys.stderr); return False

# --- Function: Save String to File ---
def save_string_to_file(content, default_filename="output.txt"):
    """Prompts user and saves the given string content to a file."""
    print("-" * 20) # Separator before asking
    filename_input = input(f"Enter filename to save text string as (default: {default_filename}): ").strip()
    filename = filename_input if filename_input else default_filename
    if '.' not in os.path.basename(filename): filename += ".txt"
    full_save_path = os.path.abspath(filename)
    print(f"Attempting to save text string to: {full_save_path}")
    try:
        with open(full_save_path, 'w', encoding='utf-8') as f: f.write(content)
        print(f"Text string successfully saved.")
        return True
    except (IOError, OSError) as e:
        print(f"Error saving text file '{full_save_path}': {e}", file=sys.stderr)
    except Exception as e_other:
        print(f"An unexpected error occurred during text file saving: {e_other}", file=sys.stderr)
    return False

# --- Main Execution ---
if __name__ == "__main__":
    print("Directory Content Processor")
    print("=" * 25)

    # Removed initial library availability checks/warnings

    dir_input = input("Enter the directory path: ")
    dir_input = dir_input.strip('"\' ')

    if not os.path.isdir(dir_input):
        print(f"\nERROR: The provided path is not a valid directory: '{dir_input}'", file=sys.stderr)
        sys.exit(1)

    print("\nChoose an output format:")
    print("  1. Clipboard (Raw text string of file contents)")
    print("  2. .txt File (Raw text string of file contents)")
    print("  3. PDF File (Embeds text, images; merges existing PDFs)")

    while True:
        choice = input("Enter your choice (1, 2, or 3): ").strip()
        if choice in ['1', '2', '3']:
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

    print("-" * 25)

    if choice == '1':
        print("Processing for Clipboard...")
        # Assumes pyperclip is installed. If not, get_files_content_string will run,
        # but the pyperclip.copy call below will raise an error.
        result_string = get_files_content_string(dir_input)
        if result_string is not None:
            string_length = len(result_string)
            print(f"\nText String Summary:")
            print(f"  Length: {string_length} characters")
            print(f"  Est. AI Tokens: ~{round(string_length / 4)}")
            if string_length > 0:
                if string_length > CLIPBOARD_WARN_THRESHOLD:
                    print(f"\nWarning: Text is very long ({string_length} chars)!")
                    print("         It might not copy correctly due to clipboard limits.")
                try:
                    # This will raise NameError if pyperclip failed to import
                    pyperclip.copy(result_string)
                    print("\nAttempted to copy text string to clipboard.")
                    print("(Verify content if it was very long)")
                except Exception as e_clip:
                    print(f"\nError copying to clipboard: {e_clip}", file=sys.stderr)
            else:
                print("\nGenerated text string is empty, nothing to copy.")
        else:
            print("\nFailed to generate text string for clipboard.")

    elif choice == '2':
        print("Processing for .txt file...")
        result_string = get_files_content_string(dir_input)
        if result_string is not None:
            string_length = len(result_string)
            print(f"\nText String Summary:")
            print(f"  Length: {string_length} characters")
            print(f"  Est. AI Tokens: ~{round(string_length / 4)}")

            if string_length > 0:
                 base_dir_name = os.path.basename(os.path.normpath(dir_input))
                 default_txt_name = f"text_content_{base_dir_name}_{time.strftime('%Y%m%d_%H%M%S')}.txt"
                 save_string_to_file(result_string, default_filename=default_txt_name)
            else:
                 print("\nGenerated text string is empty, no file saved.")
        else:
            print("\nFailed to generate text string for .txt file.")

    elif choice == '3':
        print("Processing for PDF file...")
        # Assumes fpdf2, Pillow, pypdf are installed. If not, create_consolidated_pdf
        # will likely raise an error when it tries to use them.
        base_dir_name = os.path.basename(os.path.normpath(dir_input))
        default_pdf_name = f"{base_dir_name}_{time.strftime('%Y%m%d_%H%M')}.pdf"
        pdf_filename_input = input(f"Enter filename for the PDF (default: {default_pdf_name}): ").strip()
        pdf_filename = pdf_filename_input if pdf_filename_input else default_pdf_name
        if not pdf_filename.lower().endswith('.pdf'): pdf_filename += ".pdf"

        # Call the function directly. It will handle internal errors or raise them.
        pdf_success = create_consolidated_pdf(dir_input, pdf_filename)

        if pdf_success:
             print(f"\nConsolidated PDF saved as: {os.path.abspath(pdf_filename)}")
        else:
             print(f"\nPDF generation failed or was incomplete. Check console messages.")

    print("\nScript finished.")

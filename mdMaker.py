import os
import re
import json
import logging
from datetime import datetime
from redlines import Redlines
import textwrap

# ----------------------------- Initialization ----------------------------- #

def initialize_script():
    """
    Initializes the script by prompting the user for the TPO number and class name,
    retrieving the current date, defining fixed components, and setting up logging.
    
    Returns:
        dict: A dictionary containing initialization variables.
    """
    # Prompt the user for the TPO number
    tpo_input = input("Enter the TPO number (e.g., TPO40): ").strip()
    if not tpo_input:
        print("TPO number cannot be empty. Exiting.")
        exit(1)
    
    # Strip 'TPO' prefix if present to avoid duplication
    if tpo_input.upper().startswith("TPO"):
        tpo_number = tpo_input[3:]
    else:
        tpo_number = tpo_input
    
    # Prompt the user for the Class name
    class_name = input("Enter the class name (e.g., class2027): ").strip()
    if not class_name:
        print("Class name cannot be empty. Exiting.")
        exit(1)
    
    # Retrieve the current date
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # Define fixed components
    esl = "ESL"
    keyword = "Speaking"
    
    # Set up logging
    logging.basicConfig(
        filename='markdown_generator.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logging.info("Script initialized.")
    
    return {
        'tpo_number': tpo_number,
        'date_str': date_str,
        'esl': esl,
        'keyword': keyword,
        'class_name': class_name
    }

# -------------------------- Task Detection -------------------------- #

def detect_available_tasks():
    """
    Detects available tasks (1 to 4) by checking the existence of required files.
    
    Returns:
        tuple: A tuple containing a list of available task numbers and a dictionary of missing files.
    """
    available_tasks = []
    missing_files_report = {}
    
    for task_num in range(1, 5):  # Tasks 1 to 4
        required_files = [f"task{task_num}_question.txt"]
        
        if task_num in [2, 3]:
            required_files.extend([
                f"task{task_num}_reading.txt",
                f"task{task_num}_listening.txt"
            ])
        elif task_num == 4:
            required_files.append(f"task{task_num}_listening.txt")  # Task 4 has listening, no reading
        
        # Check existence of all required files
        missing_files = [f for f in required_files if not os.path.exists(f)]
        
        if not missing_files:
            available_tasks.append(task_num)
        else:
            missing_files_report[task_num] = missing_files
            logging.error(f"Task {task_num}: Missing files: {', '.join(missing_files)}")
            print(f"Task {task_num}: Missing files: {', '.join(missing_files)}")
    
    return available_tasks, missing_files_report

# ------------------------- Content Extraction ------------------------- #

def read_content(task_num, content_type):
    """
    Reads the content from a specified .txt file for a given task.
    
    Args:
        task_num (int): The task number.
        content_type (str): The type of content ('question', 'reading', 'listening').
    
    Returns:
        str: The content read from the file, or None if file is missing.
    """
    filename = f"task{task_num}_{content_type}.txt"
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            logging.info(f"Task {task_num}: Successfully read {filename}.")
            return content
    except FileNotFoundError:
        logging.error(f"Task {task_num}: File {filename} not found.")
        print(f"Task {task_num}: File {filename} not found.")
        return None
    except Exception as e:
        logging.error(f"Task {task_num}: Error reading {filename}: {e}")
        print(f"Task {task_num}: Error reading {filename}: {e}")
        return None

def get_task_content(task_num):
    """
    Retrieves the content for a specific task based on its number.
    
    Args:
        task_num (int): The task number.
    
    Returns:
        dict: A dictionary containing the content sections.
    """
    content = {}
    content['question'] = read_content(task_num, 'question')
    
    if task_num in [2, 3]:
        content['reading'] = read_content(task_num, 'reading')
        content['listening'] = read_content(task_num, 'listening')
    elif task_num == 4:
        content['reading'] = None  # Task 4 has no reading
        content['listening'] = read_content(task_num, 'listening')
    elif task_num == 1:
        content['reading'] = None
        content['listening'] = None  # Task 1 has only question
    
    return content

# ------------------------- Highlight Differences ------------------------- #

def clean_text(text):
    """
    Cleans the input text by stripping whitespace and removing leading/trailing quotes.
    
    Args:
        text (str): The text to clean.
    
    Returns:
        str: The cleaned text.
    """
    text = text.strip()
    text = re.sub(r'^"+|"+$', '', text)
    return text

def highlight_differences(original, revised):
    """
    Highlights differences between the original and revised texts using Redlines.
    
    Args:
        original (str): The original text.
        revised (str): The revised text.
    
    Returns:
        str: HTML string with highlighted differences.
    """
    original_clean = clean_text(original)
    revised_clean = clean_text(revised)
    
    differ = Redlines(original_clean, revised_clean)
    highlighted = differ.output_markdown
    
    return highlighted

def generate_highlighted_html(task_num, class_name):
    """
    Generates highlighted HTML for student responses for a given task.
    
    Args:
        task_num (int): The task number.
        class_name (str): The name of the class.
    
    Returns:
        str: HTML string containing all highlighted student responses within a single <details> block.
    """
    json_file = f"task{task_num}_responses.json"
    if not os.path.exists(json_file):
        logging.error(f"Task {task_num}: JSON file {json_file} not found.")
        print(f"Task {task_num}: JSON file {json_file} not found.")
        return ""
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            responses = json.load(f)
        logging.info(f"Task {task_num}: Successfully loaded {json_file}.")
    except json.JSONDecodeError as e:
        logging.error(f"Task {task_num}: JSON decode error in {json_file}: {e}")
        print(f"Task {task_num}: JSON decode error in {json_file}: {e}")
        return ""
    except Exception as e:
        logging.error(f"Task {task_num}: Error loading {json_file}: {e}")
        print(f"Task {task_num}: Error loading {json_file}: {e}")
        return ""
    
    highlighted_changes = []
    
    for student_name, response_data in responses.items():
        original_response = response_data.get("original_response", "").strip()
        raw_feedback = response_data.get("feedback", "").strip()
        
        # Extract revised text using regex
        revised_text_match = re.search(r"\*\*Revised Version:\*\*\s*(.*)", raw_feedback, re.DOTALL)
        if not revised_text_match:
            logging.warning(f"Task {task_num}: Revised text not found for {student_name}.")
            print(f"Task {task_num}: Revised text not found for {student_name}.")
            continue
        
        revised_text = revised_text_match.group(1).strip()
        
        if original_response and revised_text:
            highlighted_revised_text = highlight_differences(original_response, revised_text)
            highlighted_changes.append((student_name, highlighted_revised_text))
            logging.info(f"Task {task_num}: Highlighted differences for {student_name}.")
        else:
            logging.warning(f"Task {task_num}: Missing original or revised text for {student_name}.")
            print(f"Task {task_num}: Missing original or revised text for {student_name}.")
    
    if not highlighted_changes:
        logging.warning(f"Task {task_num}: No valid highlighted responses found.")
        print(f"Task {task_num}: No valid highlighted responses found.")
        return ""
    
    # Assemble HTML with a single <details> block
    highlighted_html = f"""<details>
<summary>{class_name}修改文稿点这里</summary>

"""
    for name, highlighted_text in highlighted_changes:
        highlighted_html += f"<p><strong>{name}</strong></p>\n<p>{highlighted_text}</p>\n<hr>\n"
    
    highlighted_html += "</details>"
    
    return highlighted_html

# ------------------------- Markdown Assembly ------------------------- #

def assemble_markdown(tpo_number, date_str, esl, keyword, task_num, content, highlighted_html, vocab_html_content):
    """
    Assembles the Markdown content based on the provided data.
    
    Args:
        tpo_number (str): The TPO number.
        date_str (str): The current date string.
        esl (str): Fixed component 'ESL'.
        keyword (str): Fixed component 'Speaking'.
        task_num (int): The task number.
        content (dict): The content sections for the task.
        highlighted_html (str): The HTML block with highlighted responses.
        vocab_html_content (str): The HTML content of the vocabulary list.
    
    Returns:
        str: The complete Markdown content.
    """
    title = f"TPO{tpo_number} Task{task_num}"
    
    # Define sections based on task number
    question_section = f"## {content.get('question')}\n\n" if content.get('question') else ""
    reading_section = f"## Reading\n\n{content.get('reading')}\n\n" if content.get('reading') else ""
    listening_section = f"## Listening\n\n{content.get('listening')}\n\n" if content.get('listening') else ""


    
    # Insert the vocabulary HTML content right before the <details> tag
    # Use textwrap.dedent to remove any unintended indentation
    # Ensure the triple-quoted strings start at the leftmost column
    if vocab_html_content:
        content_to_dedent = f"""\
---
title: "{title}"
mathjax: true
layout: post
categories: media
---

# Task{task_num}
{question_section}
{reading_section}{listening_section}
{vocab_html_content}
{highlighted_html}
"""
    else:
        content_to_dedent = f"""\
---
title: "{title}"
mathjax: true
layout: post
categories: media
---

# Task{task_num}
{question_section}
{reading_section}{listening_section}
{highlighted_html}
"""

    markdown_content = textwrap.dedent(content_to_dedent)
    return markdown_content

# ------------------------- Saving Markdown ------------------------- #

def define_filename(date_str, esl, keyword, tpo_number, task_num):
    """
    Defines the filename for the Markdown file based on the provided parameters.
    
    Args:
        date_str (str): The current date string.
        esl (str): Fixed component 'ESL'.
        keyword (str): Fixed component 'Speaking'.
        tpo_number (str): The TPO number.
        task_num (int): The task number.
    
    Returns:
        str: The filename for the Markdown file.
    """
    return f"{date_str}-{esl}-{keyword}-TPO{tpo_number}-Task{task_num}.md"

def save_markdown(filename, content):
    """
    Saves the Markdown content to a file.
    
    Args:
        filename (str): The filename for the Markdown file.
        content (str): The Markdown content to save.
    
    Returns:
        bool: True if saved successfully, False otherwise.
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        logging.info(f"Markdown file {filename} created successfully.")
        print(f"Markdown file {filename} created successfully.")
        return True
    except Exception as e:
        logging.error(f"Failed to write Markdown file {filename}: {e}")
        print(f"Failed to write Markdown file {filename}: {e}")
        return False

# ------------------------- Main Processing ------------------------- #

def process_task(task_num, init_vars):
    """
    Processes a single task by extracting content, generating highlights,
    assembling Markdown, and saving the file.
    
    Args:
        task_num (int): The task number.
        init_vars (dict): Initialization variables containing TPO number, date, class name, etc.
    
    Returns:
        bool: True if processed successfully, False otherwise.
    """
    logging.info(f"Processing Task {task_num}...")
    print(f"\nProcessing Task {task_num}...")
    
    # Extract Content
    content = get_task_content(task_num)
    if not content.get('question'):
        logging.error(f"Task {task_num}: Missing question content.")
        print(f"Task {task_num}: Missing question content.")
        return False
    
    # Process Student Responses and Generate Highlighted HTML
    highlighted_html = generate_highlighted_html(task_num, init_vars['class_name'])
    if not highlighted_html.strip():
        logging.warning(f"Task {task_num}: No highlighted responses generated.")
        print(f"Task {task_num}: No highlighted responses generated.")
    
    # Read Vocabulary List HTML Content
    vocab_html_file = f"task{task_num}_vocabulary_list.html"
    if os.path.exists(vocab_html_file):
        try:
            with open(vocab_html_file, 'r', encoding='utf-8') as f:
                vocab_html_content = f.read()
            logging.info(f"Task {task_num}: Successfully read {vocab_html_file}.")
        except Exception as e:
            logging.error(f"Task {task_num}: Error reading {vocab_html_file}: {e}")
            print(f"Task {task_num}: Error reading {vocab_html_file}: {e}")
            vocab_html_content = ""
    else:
        logging.warning(f"Task {task_num}: Vocabulary HTML file {vocab_html_file} not found.")
        print(f"Task {task_num}: Vocabulary HTML file {vocab_html_file} not found.")
        vocab_html_content = ""
    
    # Assemble Markdown Content
    markdown_content = assemble_markdown(
        tpo_number=init_vars['tpo_number'],
        date_str=init_vars['date_str'],
        esl=init_vars['esl'],
        keyword=init_vars['keyword'],
        task_num=task_num,
        content=content,
        highlighted_html=highlighted_html,
        vocab_html_content=vocab_html_content
    )
    
    # Define Filename
    filename = define_filename(
        date_str=init_vars['date_str'],
        esl=init_vars['esl'],
        keyword=init_vars['keyword'],
        tpo_number=init_vars['tpo_number'],
        task_num=task_num
    )
    
    # Save Markdown File
    success = save_markdown(filename, markdown_content)
    return success

# ------------------------- Summary Report ------------------------- #

def generate_summary(processed_tasks, missing_files_report):
    """
    Generates and prints a summary report of the processing.
    
    Args:
        processed_tasks (list): List of successfully processed task numbers.
        missing_files_report (dict): Dictionary of task numbers and their corresponding missing files.
    """
    print("\n=== Processing Summary ===")
    logging.info("\n=== Processing Summary ===")
    
    if processed_tasks:
        success_str = ', '.join(map(str, processed_tasks))
        print(f"Successfully processed tasks: {success_str}")
        logging.info(f"Successfully processed tasks: {success_str}")
    else:
        print("No tasks were processed successfully.")
        logging.info("No tasks were processed successfully.")
    
    if missing_files_report:
        print("\nErrors encountered:")
        logging.info("\nErrors encountered:")
        for task, missing_files in missing_files_report.items():
            error_message = f"Missing files: {', '.join(missing_files)}"
            print(f" - Task {task}: {error_message}")
            logging.error(f"Task {task}: {error_message}")
    else:
        print("\nNo errors encountered.")
        logging.info("No errors encountered.")

# ------------------------- Main Function ------------------------- #

def main():
    """
    The main function orchestrates the entire Markdown generation process.
    """
    # Initialize the script
    init_vars = initialize_script()
    
    # Detect available tasks
    available_tasks, missing_files_report = detect_available_tasks()
    
    if not available_tasks:
        print("No available tasks to process. Exiting.")
        logging.info("No available tasks to process. Exiting.")
        exit(1)
    
    processed_tasks = []
    errors = {}
    
    for task_num in available_tasks:
        success = process_task(task_num, init_vars)
        if success:
            processed_tasks.append(task_num)
        else:
            errors[task_num] = ["Failed to process the task due to previous errors."]
    
    # Handle tasks that were missing files initially
    if missing_files_report:
        for task_num, missing_files in missing_files_report.items():
            if task_num not in errors:
                errors[task_num] = [f"Missing files: {', '.join(missing_files)}"]
    
    # Generate Summary Report
    generate_summary(processed_tasks, missing_files_report)
    logging.info("Script execution completed.")

# ------------------------- Entry Point ------------------------- #

if __name__ == "__main__":
    main()

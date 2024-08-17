import os
import re
import json
import pandas as pd
import openpyxl
from redlines import Redlines

def highlight_differences(original, revised):
    differ = Redlines(original, revised)
    return differ.output_markdown

def process_responses(task_number):
    # Load the JSON responses
    json_file = f"task{task_number}_responses.json"
    if not os.path.exists(json_file):
        print(f"JSON file {json_file} not found.")
        return
    
    with open(json_file, 'r') as f:
        responses = json.load(f)

    # Create an empty DataFrame for storing results
    df = pd.DataFrame(columns=["Student's name", 'Language Use', 'Topic Development', 'Overall Score', 'Original Text', 'Revised Text'])
    highlighted_changes = []

    print("\nProcessing student responses...")  # Initial log

    for student_name, response_data in responses.items():
        original_response = response_data.get("original_response", "").strip()
        raw_feedback = response_data.get("feedback", "").strip()

        # Extract scores and revised text using regex
        language_use_score_match = re.search(r"\*\*Score for Language Use:\*\* (\d\.\d)", raw_feedback)
        topic_development_score_match = re.search(r"\*\*Score for Topic Development:\*\* (\d\.\d)", raw_feedback)
        revised_text_match = re.search(r"\*\*Revised Version:\*\*\s*(.*)", raw_feedback, re.DOTALL)

        if not (language_use_score_match and revised_text_match and topic_development_score_match):
            print(f"Failed to parse feedback for {student_name}")
            continue

        language_use_score = float(language_use_score_match.group(1))
        topic_development_score = float(topic_development_score_match.group(1))
        revised_text = revised_text_match.group(1).strip()

        average_score = (language_use_score + topic_development_score) / 2.0

        # Store results in DataFrame
        df.loc[len(df)] = [student_name, language_use_score, topic_development_score, average_score, original_response, revised_text]

        # Highlight changes and store them
        if original_response:
            highlighted_revised_text = highlight_differences(original_response, revised_text)
            highlighted_changes.append((student_name, highlighted_revised_text))

    # Save results to a separate Excel file for each task
    excel_filename = f'StudentFeedback_Task{task_number}.xlsx'
    with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
        print(f"\nSaving results to {excel_filename}...")
        df.to_excel(writer, sheet_name=f'Task{task_number} Feedback', index=False)
        worksheet = writer.sheets[f'Task{task_number} Feedback']

        # Set the text to wrap for certain columns
        wrap_alignment = openpyxl.styles.Alignment(wrapText=True, vertical='top')
        for row in worksheet.iter_rows():
            for cell in row:
                cell.alignment = wrap_alignment

        # Set row height for rows with data
        for idx, row in enumerate(worksheet, start=1):
            if idx > 1:  # assuming the first row is header
                worksheet.row_dimensions[idx].height = 60  # adjust this value based on your needs

    # Save results to CSV
    csv_filename = f'StudentFeedback_Task{task_number}.csv'
    df.to_csv(csv_filename, index=False)
    print(f"\nData saved successfully to {csv_filename}.")

    # Save highlighted changes to a separate HTML file
    highlighted_filename = f'HighlightedChanges_Task{task_number}.html'
    with open(highlighted_filename, 'w') as file:
        file.write("<html><body>")
        for student_name, highlighted_text in highlighted_changes:
            file.write(f"<h2>{student_name}</h2>")
            file.write(f"<p>{highlighted_text}</p>")
            file.write("<hr>")
        file.write("</body></html>")
    
    print(f"\nHighlighted changes saved to {highlighted_filename}.")
    print("Processing complete.")

def main():
    task_number = input("Select the task number to process responses (1, 2, 3, or 4), or type any other input to quit:").strip()
    if task_number not in ['1', '2', '3', '4']:
        print("Invalid input. Exiting the program.")
        return

    process_responses(task_number)

if __name__ == "__main__":
    main()

import os
import json
import pandas as pd
import re


def read_scores_from_json(task_file):
    with open(task_file, 'r') as f:
        data = json.load(f)

    task_scores = {}
    for student_name, feedback_data in data.items():
        try:
            # Extract scores using regex
            language_use_score_match = re.search(r"\*\*Score for Language Use:\*\* (\d\.\d)", feedback_data["feedback"])
            topic_development_score_match = re.search(r"\*\*Score for Topic Development:\*\* (\d\.\d)", feedback_data["feedback"])
            
            if language_use_score_match and topic_development_score_match:
                language_use_score = float(language_use_score_match.group(1))
                topic_development_score = float(topic_development_score_match.group(1))
                overall_score = (language_use_score + topic_development_score) / 2.0
                task_scores[student_name] = overall_score
            else:
                print(f"Could not find both scores for student: {student_name}")
        except Exception as e:
            print(f"Failed to parse scores for student: {student_name} due to error: {e}")
            continue

    return task_scores


def calculate_total_raw_and_toefl_scores(task_files):
    total_scores = {}
    
    for task_file in task_files:
        task_scores = read_scores_from_json(task_file)
        for student_name, score in task_scores.items():
            if student_name not in total_scores:
                total_scores[student_name] = []
            total_scores[student_name].append(score)

    raw_scores = {student_name: sum(scores) for student_name, scores in total_scores.items()}
    toefl_scores = {student_name: convert_raw_to_toefl(raw_score) for student_name, raw_score in raw_scores.items()}
    
    return raw_scores, toefl_scores

def convert_raw_to_toefl(raw_score):
    # Conversion table from raw score to scaled TOEFL score
    conversion_table = {
        0: 0, 1: 2, 2: 4, 3: 6, 4: 8, 5: 9,
        6: 11, 7: 13, 8: 15, 9: 17, 10: 19,
        11: 21, 12: 23, 13: 24, 14: 26, 15: 28, 16: 30
    }
    
    if raw_score in conversion_table:
        return conversion_table[raw_score]
    
    # Handle decimal values (e.g., 6.5 -> 12)
    lower = int(raw_score)
    upper = lower + 1
    if lower in conversion_table and upper in conversion_table:
        return (conversion_table[lower] + conversion_table[upper]) / 2.0
    
    return None  # Default return if something goes wrong

def save_scores_to_files(raw_scores, toefl_scores, output_filename):
    df = pd.DataFrame({
        "Student Name": list(raw_scores.keys()),
        "TOEFL Score": [int(score) for score in toefl_scores.values()],  # Convert TOEFL scores to integers
        "Total Raw Score": list(raw_scores.values())
    })

    # Save to CSV
    df.to_csv(f'{output_filename}.csv', index=False)

    # Save to Excel
    df.to_excel(f'{output_filename}.xlsx', index=False)

def main():
    task_files = [f'task{i}_responses.json' for i in range(1, 5)]
    
    raw_scores, toefl_scores = calculate_total_raw_and_toefl_scores(task_files)
    
    save_scores_to_files(raw_scores, toefl_scores, "Student_TOEFL_Scores")

if __name__ == "__main__":
    main()

# import os
# import re
# import json
# from pathlib import Path
# from openai import OpenAI
# from dotenv import load_dotenv
# from tqdm import tqdm

# # Load OpenAI API key
# load_dotenv()
# client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# def load_json_file(filename):
#     try:
#         with open(filename, 'r', encoding='utf-8') as file:
#             return json.load(file)
#     except FileNotFoundError:
#         print(f"File {filename} not found.")
#         return None
#     except json.JSONDecodeError:
#         print(f"Error decoding JSON from {filename}.")
#         return None

# def extract_modified_response(feedback):
#     try:
#         # Extract the modified response using regex
#         match = re.search(r"\*\*Revised Version:\*\*\s*(.*)", feedback, re.DOTALL)
#         if match:
#             return match.group(1).strip()
#     except Exception as e:
#         print(f"Error extracting modified response: {e}")
#     return None

# def generate_audio_for_response(text, voice, task_number, student_name):
#     try:
#         speech_file_path = Path(f"task{task_number}_modified_audios") / f"task{task_number}_{student_name}_shadowing.wav"
#         speech_file_path.parent.mkdir(parents=True, exist_ok=True)

#         response = client.audio.speech.create(
#             model="tts-1",
#             voice=voice,
#             input=text
#         )

#         response.stream_to_file(speech_file_path)
#         print(f"Generated audio for {student_name} at {speech_file_path}")

#     except Exception as e:
#         print(f"Error generating audio for {student_name}: {e}")

# def main():
#     while True:
#         print("Enter task number to process (1-4) or 'q' to quit:")
#         task_number = input().strip()

#         if task_number not in ['1', '2', '3', '4']:
#             print("Exiting the program.")
#             break

#         task_file = f"task{task_number}_responses.json"
#         gender_file = "student_gender_map.json"

#         # Load JSON data
#         task_data = load_json_file(task_file)
#         gender_data = load_json_file(gender_file)

#         if not task_data or not gender_data:
#             continue

#         for student_name, feedback_data in tqdm(task_data.items(), desc=f"Processing Task {task_number}"):
#             modified_response = extract_modified_response(feedback_data["feedback"])
#             if not modified_response:
#                 print(f"No modified response found for {student_name}")
#                 continue

#             # Get the student's gender and select the appropriate voice
#             gender = gender_data.get(student_name, "unknown").lower()
#             if gender == "male":
#                 voice = "alloy"
#             elif gender == "female":
#                 voice = "nova"
#             else:
#                 print(f"Gender unknown for {student_name}, skipping...")
#                 continue

#             # Generate the audio
#             generate_audio_for_response(modified_response, voice, task_number, student_name)

# if __name__ == "__main__":
#     main()


import os
import re
import json
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm

# Load OpenAI API key
load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def load_json_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"File {filename} not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding JSON from {filename}.")
        return None

def extract_modified_response(feedback):
    try:
        # Extract the modified response using regex
        match = re.search(r"\*\*Revised Version:\*\*\s*(.*)", feedback, re.DOTALL)
        if match:
            return match.group(1).strip()
    except Exception as e:
        print(f"Error extracting modified response: {e}")
    return None

def generate_audio_for_response(text, voice, task_number, student_name):
    try:
        speech_file_path = Path(f"task{task_number}_modified_audios") / f"task{task_number}_{student_name}_shadowing.wav"
        speech_file_path.parent.mkdir(parents=True, exist_ok=True)

        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )

        response.stream_to_file(speech_file_path)
        print(f"Generated audio for {student_name} at {speech_file_path}")

    except Exception as e:
        print(f"Error generating audio for {student_name}: {e}")

def process_responses(task_number):
    task_file = f"task{task_number}_responses.json"
    gender_file = "student_gender_map.json"

    # Load JSON data
    task_data = load_json_file(task_file)
    gender_data = load_json_file(gender_file)

    if not task_data or not gender_data:
        return

    for student_name, feedback_data in tqdm(task_data.items(), desc=f"Processing Task {task_number}"):
        modified_response = extract_modified_response(feedback_data["feedback"])
        if not modified_response:
            print(f"No modified response found for {student_name}")
            continue

        # Get the student's gender and select the appropriate voice
        gender = gender_data.get(student_name, "unknown").lower()
        if gender == "male":
            voice = "alloy"
        elif gender == "female":
            voice = "nova"
        else:
            print(f"Gender unknown for {student_name}, skipping...")
            continue

        # Generate the audio
        generate_audio_for_response(modified_response, voice, task_number, student_name)

def main():
    while True:
        task_number = input("Select the task number to process responses (1, 2, 3, or 4), or type any other input to quit:").strip()
        if task_number not in ['1', '2', '3', '4']:
            print("Exiting the program.")
            break

        process_responses(task_number)

if __name__ == "__main__":
    main()


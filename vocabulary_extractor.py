# vocabulary_extractor.py

import os
import requests
import spacy
from dotenv import load_dotenv
import sys
import openai
import textwrap

# Load environment variables from .env file
load_dotenv()
MW_LEARNER_KEY = os.getenv('MW_LEARNER_KEY')  # Merriam-Webster Learner's Dictionary API Key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')  # OpenAI API Key

# Initialize OpenAI API
openai.api_key = OPENAI_API_KEY

# Initialize spaCy English model
try:
    nlp = spacy.load('en_core_web_sm')
except OSError:
    print("spaCy English model not found. Downloading...")
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load('en_core_web_sm')

def load_word_list(filepath):
    """
    Load words from a .txt file into a set.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            words = set(line.strip().lower() for line in file if line.strip())
        return words
    except FileNotFoundError:
        print(f"Error: The file {filepath} was not found.")
        return set()

def get_task_number():
    """
    Prompt the user to input the task number (1-4) or exit.
    """
    while True:
        task_number = input("Select the task number to extract new words for (1, 2, 3, or 4), or type any other key to quit: ").strip()
        if task_number in ['1', '2', '3', '4']:
            return int(task_number)
        else:
            print("Exiting the program.")
            return None

def read_task_files(task_number):
    """
    Read the listening, question, and reading files for the given task number.
    Handles different file structures based on the task.
    """
    possible_files = {
        1: [f"task{task_number}_question.txt"],
        2: [f"task{task_number}_listening.txt", f"task{task_number}_question.txt", f"task{task_number}_reading.txt"],
        3: [f"task{task_number}_listening.txt", f"task{task_number}_question.txt", f"task{task_number}_reading.txt"],
        4: [f"task{task_number}_listening.txt", f"task{task_number}_question.txt"]
    }

    filenames = possible_files.get(task_number, [])

    combined_text = ""
    for filename in filenames:
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                content = file.read()
                combined_text += " " + content
        except FileNotFoundError:
            print(f"Warning: The file {filename} was not found and will be skipped.")
    if not combined_text.strip():
        print("Error: No content found in the specified task files.")
        return None
    return combined_text

def extract_lemmatized_words(text):
    """
    Use spaCy to tokenize and lemmatize the text, extracting relevant parts of speech.
    """
    doc = nlp(text.lower())
    words = set()
    for token in doc:
        if token.is_alpha and token.pos_ in {'NOUN', 'VERB', 'ADJ', 'ADV'}:
            words.add(token.lemma_)
    return words

def fetch_mw_audio(word):
    """
    Fetch the audio pronunciation URL from Merriam-Webster's API for the given word.
    """
    api_key = MW_LEARNER_KEY  # Using Learner's Dictionary API for audio
    url = f"https://www.dictionaryapi.com/api/v3/references/learners/json/{word}?key={api_key}"

    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error: Failed to fetch audio for '{word}'. Status Code: {response.status_code}")
        return None

    data = response.json()
    if not data:
        print(f"No data found for '{word}'.")
        return None

    # Handle suggestions (when word not found)
    if isinstance(data[0], str):
        print(f"'{word}' not found in dictionary. Suggestions: {data}")
        return None

    # Extract audio pronunciation
    audio_url = None
    for entry in data:
        if 'hwi' in entry and 'prs' in entry['hwi']:
            for prs in entry['hwi']['prs']:
                if 'sound' in prs and 'audio' in prs['sound']:
                    audio_code = prs['sound']['audio']
                    # Construct the audio URL based on the audio code
                    if audio_code.startswith('bix'):
                        audio_url = f"https://media.merriam-webster.com/audio/prons/en/us/mp3/b/bix/{audio_code}.mp3"
                    elif audio_code.startswith('gg'):
                        audio_url = f"https://media.merriam-webster.com/audio/prons/en/us/mp3/g/gg/{audio_code}.mp3"
                    else:
                        audio_url = f"https://media.merriam-webster.com/audio/prons/en/us/mp3/{audio_code[0]}/{audio_code}.mp3"
                    break
        if audio_url:
            break

    if not audio_url:
        print(f"No audio pronunciation found for '{word}'.")
        return None

    return audio_url

def get_chatgpt_completion(prompt, model="gpt-4o-mini"):
    """
    Get completion from ChatGPT.
    """
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        print(f"Error with OpenAI API: {e}")
        return ""

def find_context_sentences(word, text):
    """
    Extract all sentences containing the word.
    """
    doc = nlp(text.lower())
    sentences = [sent.text.strip() for sent in doc.sents if word in sent.text.lower()]
    return sentences


def create_html_table(vocab_data):
    """
    Create an HTML table from the vocabulary data.
    Includes speaker icons that play audio pronunciations inline.
    The generated HTML has line breaks but no leading indentation.
    The play button inherits text color and adapts to dark and light themes.
    """
    # Define the HTML template without leading indentation
    html_template = textwrap.dedent("""\
        <html lang="en">
        <head>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 20px;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                }
                th, td {
                    border: 1px solid #dddddd;
                    text-align: left;
                    padding: 8px;
                }
                th {
                    background-color: #f2f2f2;
                }
                .speaker {
                    cursor: pointer;
                    font-size: 16px;
                    color: inherit;  /* Inherit text color for dynamic theming */
                }
                /* Dark Mode Styles */
                @media (prefers-color-scheme: dark) {
                    body {
                        background-color: #121212;
                        color: #e0e0e0;
                    }
                    table {
                        border: 1px solid #444444;
                    }
                    th {
                        background-color: #1e1e1e;
                        color: #e0e0e0;
                    }
                    td {
                        border: 1px solid #444444;
                    }
                    .speaker {
                        color: inherit;  /* Inherit text color in dark mode */
                    }
                }
                /* Light Mode Styles */
                @media (prefers-color-scheme: light) {
                    body {
                        background-color: #ffffff;
                        color: #000000;
                    }
                    th {
                        background-color: #f2f2f2;
                        color: #333333;
                    }
                    .speaker {
                        color: inherit;  /* Inherit text color in light mode */
                    }
                }
                /* Smooth transition for theme changes */
                @media (prefers-color-scheme: dark), (prefers-color-scheme: light) {
                    body, table, th, td, .speaker {
                        transition: background-color 0.3s, color 0.3s;
                    }
                }
            </style>
        </head>
        <body>
            <table>
                <tr>
                    <th>New Word</th>
                    <th>Pronunciation</th>
                    <th>Part of Speech</th>
                    <th>English Explanation</th>
                    <th>Chinese Explanation</th>
                    <th>Example Sentence</th>
                </tr>
    """)

    # Initialize html_content with the template (line breaks preserved, no leading spaces)
    html_content = html_template

    # Iterate over each vocabulary entry and append table rows without leading indentation
    for word in vocab_data:
        # Prepare the speaker icon and audio elements
        speaker_html = (
            f'<span class="speaker" onclick="document.getElementById(\'audio_{word["New Word"]}\').play();">&#9658;</span>'
            f'<audio id="audio_{word["New Word"]}"><source src="{word["Audio"]}" type="audio/mpeg"></audio>'
        )

        # Construct the table row with line breaks and internal indentation
        row = textwrap.dedent(f"""\
            <tr>
                <td>{word['New Word']}</td>
                <td>{speaker_html}</td>
                <td>{word['Part of Speech']}</td>
                <td>{word['English Explanation']}</td>
                <td>{word['Chinese Explanation']}</td>
                <td>{word['Example Sentence']}</td>
            </tr>
        """)

        # Append the row to the html_content
        html_content += row

    # Append the closing tags with line breaks
    closing_tags = textwrap.dedent("""\
            </table>
        </body>
        </html>
    """)
    html_content += closing_tags

    return html_content


def confirm_words(difficult_words):
    """
    Print the difficult words and allow the user to exclude any.
    """
    print("\nDifficult Words:")
    for word in sorted(difficult_words):
        print(f"- {word}")

    exclude = input("\nDo you want to exclude any words? (y/n): ").strip().lower()
    if exclude == 'y':
        words_to_exclude = input("Enter the words you want to exclude, separated by commas: ")
        words_to_exclude = set(word.strip().lower() for word in words_to_exclude.split(','))
        excluded = difficult_words.intersection(words_to_exclude)
        if excluded:
            print(f"\nExcluding the following words: {', '.join(excluded)}")
            return excluded
        else:
            print("No matching words found to exclude.")
            return set()
    else:
        return set()

def add_words_to_basic(excluded_words, basic_words_file='basic_words.txt'):
    """
    Add excluded words to the start of the basic_words.txt file.
    """
    if excluded_words:
        try:
            # Read existing words
            if os.path.exists(basic_words_file):
                with open(basic_words_file, 'r', encoding='utf-8') as file:
                    existing_words = file.read()
            else:
                existing_words = ""

            # Prepend excluded words
            with open(basic_words_file, 'w', encoding='utf-8') as file:
                for word in excluded_words:
                    file.write(f"{word}\n")
                file.write(existing_words)

            print(f"Excluded words have been added to the start of '{basic_words_file}'.")
        except Exception as e:
            print(f"Error writing to '{basic_words_file}': {e}")

def chunk_list(lst, chunk_size):
    """
    Split a list into chunks of a specified size.
    """
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

def main():
    """
    Main function to run the vocabulary extractor in a loop until the user decides to exit.
    """
    # Load word lists
    basic_words = load_word_list('basic_words.txt')
    toefl_words = load_word_list('toefl_words.txt')

    if not basic_words:
        print("Basic words list is empty or not loaded. Exiting.")
        return
    if not toefl_words:
        print("TOEFL words list is empty or not loaded. Exiting.")
        return

    while True:
        # Get user input for task number
        task_number = get_task_number()
        if task_number is None:
            break

        # Read and combine task files
        combined_text = read_task_files(task_number)
        if combined_text is None:
            print("Error reading task files. Please check the files and try again.\n")
            continue

        # Extract lemmatized words
        extracted_words = extract_lemmatized_words(combined_text)

        # Identify difficult words
        difficult_words = extracted_words - basic_words
        difficult_words = difficult_words.intersection(toefl_words)

        if not difficult_words:
            print("No difficult words found based on the provided lists.\n")
            continue

        print(f"\nFound {len(difficult_words)} difficult words.")

        # Confirm words to exclude
        excluded_words = confirm_words(difficult_words)
        # Remove excluded words from difficult_words
        difficult_words = difficult_words - excluded_words
        # Add excluded words to basic_words.txt at the start
        add_words_to_basic(excluded_words)

        if not difficult_words:
            print("No difficult words left to process after exclusion.\n")
            continue

        print(f"\nProcessing {len(difficult_words)} words...")

        # Initialize vocab_data
        vocab_data = []

        # Prepare word_data_list
        word_data_list = []

        for word in sorted(difficult_words):
            # Fetch audio pronunciation from Merriam-Webster
            audio_url = fetch_mw_audio(word)
            if not audio_url:
                print(f"Skipping '{word}' due to missing audio pronunciation.\n")
                continue

            # Find context sentences
            context_sentences = find_context_sentences(word, combined_text)
            context_sentence = context_sentences[0] if context_sentences else ""

            word_entry = {
                'word': word,
                'audio_url': audio_url,
                'context_sentence': context_sentence,
            }

            word_data_list.append(word_entry)

        if not word_data_list:
            print("No words to process.\n")
            continue

        # Process word_data_list in batches
        batch_size = 10

        for word_batch in chunk_list(word_data_list, batch_size):
            # Build the prompt
            prompt = """
You are a bilingual dictionary expert. For each of the following words and their context sentences, please provide:

1. The part of speech of the word.

2. An English explanation of the word, using definitions from Oxford or Longman dictionaries, **selecting the most relevant meaning based on the provided context**.

3. A **Chinese explanation** of the word that uses the most **direct, common, and natural Chinese word or term** to match the meaning in context. Avoid literal translations of the English definition and instead use the most familiar or concise equivalent term from Chinese dictionaries (e.g., 牛津高阶双解词典).

4. An example sentence that fits the context, written in **everyday conversational American English**.

**Important:** 
- Focus strictly on the meaning of the word in the context of the given sentence.
- Ensure that the English explanation and Chinese definition are both accurately reflects the meaning of the word as used in the context sentence provided.

Here are the words and context sentences:
"""

            for idx, word_entry in enumerate(word_batch):
                word = word_entry['word']
                context_sentence = word_entry['context_sentence']
                prompt += f"\n{idx+1}. Word: {word}\n"
                prompt += f"   Context Sentence: \"{context_sentence}\"\n"

            prompt += """

Please format your response as follows:

For each word:

Word: {word}

Part of Speech: {part of speech}

English Explanation: [Your English explanation here]

Chinese Explanation: [Your Chinese explanation here]

Example Sentence: [Your example sentence here]

**Example:**

Word: Outlet

Part of Speech: Noun

English Explanation: An electrical socket that provides power for devices.

Chinese Explanation: 电源插座。

Example Sentence: "I always sit by the outlet in class so I can keep my laptop plugged in."
"""

            # Send the prompt to ChatGPT
            chatgpt_response = get_chatgpt_completion(prompt)
            if not chatgpt_response:
                print("Skipping batch due to ChatGPT response failure.\n")
                continue

            # Parse the response
            responses = chatgpt_response.split('Word:')[1:]

            for resp in responses:
                # resp starts with the word, followed by the explanations
                lines = resp.strip().split('\n')
                word_line = lines[0]
                word = word_line.strip()

                part_of_speech = "N/A"
                english_explanation = "No definition available."
                chinese_explanation = "翻译不可用"
                example_sentence = "No example provided."

                for line in lines[1:]:
                    if line.lower().startswith("part of speech:"):
                        part_of_speech = line.split("Part of Speech:")[1].strip()
                    elif line.lower().startswith("english explanation:"):
                        english_explanation = line.split("English Explanation:")[1].strip()
                    elif line.lower().startswith("chinese explanation:"):
                        chinese_explanation = line.split("Chinese Explanation:")[1].strip()
                    elif line.lower().startswith("example sentence:"):
                        example_sentence = line.split("Example Sentence:")[1].strip()

                # Find the word_entry in word_batch corresponding to this word
                word_entry = next((w for w in word_batch if w['word'].lower() == word.lower()), None)
                if not word_entry:
                    print(f"Warning: Could not find word data for '{word}'.")
                    continue

                # Fetch audio_url
                audio_url = word_entry['audio_url']

                # Prepare vocabulary entry
                vocab_entry = {
                    'New Word': word.capitalize(),
                    'Pronunciation': "",  # To be filled with speaker icon and audio
                    'Part of Speech': part_of_speech,
                    'English Explanation': english_explanation,
                    'Chinese Explanation': chinese_explanation,
                    'Example Sentence': example_sentence,
                    'Audio': audio_url
                }

                # Add vocab_entry to vocab_data
                vocab_data.append(vocab_entry)

        if not vocab_data:
            print("No vocabulary data to generate.\n")
            continue

        # Create HTML table
        html_table = create_html_table(vocab_data)

        # Save to HTML file
        output_filename = f"task{task_number}_vocabulary_list.html"
        try:
            with open(output_filename, 'w', encoding='utf-8') as html_file:
                html_file.write(html_table)
                html_file.write("\n")
            print(f"Vocabulary list generated successfully and saved to '{output_filename}'.\n")
        except Exception as e:
            print(f"Error writing to '{output_filename}': {e}\n")
            continue

if __name__ == "__main__":
    main()

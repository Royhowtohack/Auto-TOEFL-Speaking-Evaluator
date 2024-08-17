import os
import openai
import json
from glob import glob
from dotenv import load_dotenv

# Load OpenAI API key
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

def get_completion(prompt, model="gpt-4o-mini"):
    messages = [{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0.5,
    )
    return response.choices[0].message["content"]

def evaluate_student_response(question, student_response, language_use_rubric, topic_development_rubric=None, reading_transcript=None, listening_transcript=None):
    if not student_response.strip():  # Check if the response is empty
        return "No response provided. Unable to evaluate language use or topic development."

    language_use_rubric_str = "\n".join([f"{score}: {desc}" for score, desc in language_use_rubric.items()])
    
    if topic_development_rubric:
        topic_development_rubric_str = "\n".join([f"{score}: {desc}" for score, desc in topic_development_rubric.items()])
    else:
        topic_development_rubric_str = None

    if topic_development_rubric_str:
        prompt = f"""
        Evaluate the student's spoken response using the provided rubrics, focusing on language use and topic development:

        Language Use Rubric:
        {language_use_rubric_str}

        Topic Development Rubric:
        {topic_development_rubric_str}

        Please provide the feedback in the following format, using ** for bold text:

        **Score for Language Use:** [Rate between 0.0 and 4.0]
        **Score for Topic Development:** [Rate between 0.0 and 4.0]
        **Feedback:** [Detailed feedback here]
        **Revised Version:** [Revised text here, maintaining the structure and content of the original]

        Keep in mind, this was an oral speaking assignment. While grammar and word usage should be refined, the tone should remain informal and conversational.

        {f'Reading Transcript: {reading_transcript}' if reading_transcript else ''}
        {f'Listening Transcript: {listening_transcript}' if listening_transcript else ''}

        Question Given to Student: 
        \"{question}\"

        Student's Spoken Response: 
        \"{student_response}\"
        """
    else:
        prompt = f"""
        Evaluate the student's spoken response using the provided rubric, focusing on language use:

        Language Use Rubric:
        {language_use_rubric_str}

        Please provide the feedback in the following format, using ** for bold text:

        **Score for Language Use:** [Rate between 0.0 and 4.0]
        **Feedback:** [Detailed feedback here]
        **Revised Version:** [Revised text here, maintaining the structure and content of the original]

        Keep in mind, this was an oral speaking assignment. While grammar and word usage should be refined, the tone should remain informal and conversational.

        {f'Reading Transcript: {reading_transcript}' if reading_transcript else ''}
        {f'Listening Transcript: {listening_transcript}' if listening_transcript else ''}

        Student's Spoken Response: 
        \"{student_response}\"
        """
    
    feedback = get_completion(prompt)
    return feedback


def grade_task(task_number):
    # Language Use Rubric (Applies to both independent and integrated tasks)
    language_use_rubric = {
        4.0: "The response demonstrates effective use of grammar and vocabulary. It exhibits a fairly high degree of automaticity with good control of basic and complex structures (as appropriate). Some minor (or systematic) errors are noticeable but do not obscure meaning.",
        3.0: "The response demonstrates fairly automatic and effective use of grammar and vocabulary, and fairly coherent expression of relevant ideas. Response may exhibit some imprecise or inaccurate use of vocabulary or grammatical structures or be somewhat limited in the range of structures used. This may affect overall fluency, but it does not seriously interfere with the communication of the message.",
        2.0: "The response demonstrates limited range and control of grammar and vocabulary. These limitations often prevent full expression of ideas. For the most part, only basic sentence structures are used successfully and spoken with fluidity. Structures and vocabulary may express mainly simple (short) and/or general propositions, with simple or unclear connections made among them (serial listing, conjunction, juxtaposition).",
        1.0: "Range and control of grammar and vocabulary severely limit or prevent expression of ideas and connections among ideas. Some low-level responses may rely heavily on practiced or formulaic expressions.",
        0.0: "Speaker makes no attempt to respond OR response is unrelated to the topic.",
    }

    # Topic Development Rubric for Independent Tasks (Task 1)
    if task_number == '1':
        topic_development_rubric = {
            4.0: "Response is sustained and sufficient to the task. It is generally well developed and coherent; relationships between ideas are clear (or there is a clear progression of ideas).",
            3.0: "Response is mostly coherent and sustained and conveys relevant ideas/information. Overall development is somewhat limited, usually lacks elaboration or specificity. Relationships between ideas may at times not be immediately clear.",
            2.0: "The response is connected to the task, though the number of ideas presented or the development of ideas is limited. Mostly basic ideas are expressed with limited elaboration (details and support). At times relevant substance may be vaguely expressed or repetitious. Connections of ideas may be unclear.",
            1.0: "Limited relevant content is expressed. The response generally lacks substance beyond expression of very basic ideas. Speaker may be unable to sustain speech to complete the task and may rely heavily on repetition of the prompt.",
            0.0: "Speaker makes no attempt to respond OR response is unrelated to the topic.",
        }
    else:  # Topic Development Rubric for Integrated Tasks (Tasks 2, 3, and 4)
        topic_development_rubric = {
            4.0: "The response presents a clear progression of ideas and conveys the relevant information required by the task. It includes appropriate detail, though it may have minor errors or minor omissions.",
            3.0: "The response is sustained and conveys relevant information required by the task. However, it exhibits some incompleteness, inaccuracy, lack of specificity with respect to content, or choppiness in the progression of ideas.",
            2.0: "The response conveys some relevant information but is clearly incomplete or inaccurate. It is incomplete if it omits key ideas, makes vague reference to key ideas, or demonstrates limited development of important information. An inaccurate response demonstrates misunderstanding of key ideas from the stimulus. Typically, ideas expressed may not be well-connected or cohesive so that familiarity with the stimulus is necessary to follow what is being discussed.",
            1.0: "The response fails to provide much relevant content. Ideas that are expressed are often inaccurate, limited to vague utterances, or repetitions (including repetition of prompt).",
            0.0: "Speaker makes no attempt to respond OR response is unrelated to the topic.",
        }

    question_file = f"task{task_number}_question.txt"
    reading_file = f"task{task_number}_reading.txt" if task_number in ['2', '3'] else None
    listening_file = f"task{task_number}_listening.txt"

    with open(question_file, 'r') as file:
        question = file.read().strip()

    reading_transcript = None
    if reading_file and os.path.exists(reading_file):
        with open(reading_file, 'r') as file:
            reading_transcript = file.read().strip()

    listening_transcript = None
    if listening_file and os.path.exists(listening_file):
        with open(listening_file, 'r') as file:
            listening_transcript = file.read().strip()

    text_dir = f"task{task_number}_txt"
    student_files = glob(f"{text_dir}/*_task{task_number}.txt")
    if not student_files:
        print(f"No student files found in {text_dir}. Please check the directory.")
        return

    responses = {}

    for student_file in student_files:
        with open(student_file, 'r') as f:
            student_response = f.read().strip()

        student_name = os.path.basename(student_file).split('_')[0]
        print(f"Evaluating response for student: {student_name}")

        raw_feedback = evaluate_student_response(
            question, 
            student_response, 
            language_use_rubric, 
            topic_development_rubric, 
            reading_transcript if task_number in ['2', '3'] else None, 
            listening_transcript if task_number in ['2', '3', '4'] else None
        )

        responses[student_name] = {
            "original_response": student_response,
            "feedback": raw_feedback
        }

    with open(f'task{task_number}_responses.json', 'w') as f:
        json.dump(responses, f, indent=4, ensure_ascii=False)

def main():
    while True:
        print("Select the task number to grade (1, 2, 3, or 4), or type any other input to quit:")
        task_number = input().strip()

        if task_number not in ['1', '2', '3', '4']:
            print("Exiting the program.")
            break

        grade_task(task_number)

if __name__ == "__main__":
    main()




import os
os.sys.path.append("../..")
import fitz  # PyMuPDF
import json
import openai
import tiktoken  # Assume this is a tokenizer you have access to
from webagent.config import config
from webagent.utils.openai import get_llm_response, get_llm_chat_completion, cal_cost_by_tokens
from webagent.utils.openai import clean_json
from webagent.algorithm.info_extract import *  # Import the info_extract module
from concurrent.futures import ThreadPoolExecutor, as_completed

client = OpenAI(
    api_key=config.gpt.api_key,
    base_url=config.gpt.base_url
)

# Function to extract all text from a PDF file
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# Split text into chunks, similar to your create_chunks function
def split_text_chunks(text, chunk_size, tokenizer):
    tokens = tokenizer.encode(text)
    chunks = []
    i = 0
    while i < len(tokens):
        j = min(i + chunk_size, len(tokens))
        chunks.append(tokenizer.decode(tokens[i:j]))
        i = j
    return chunks

# Function to analyze a chunk and extract academic insights
def analyze_chunk(chunk, model_name='gpt-4'):
    """
    Analyzes the academic quality of a given text chunk using the specified language model.

    Args:
        chunk (str): The text chunk to analyze.
        model_name (str, optional): The name of the language model to use. Defaults to 'gpt-4'.

    Returns:
        dict: A dictionary containing the academic score and explanation.
    """
    # Prepare the chat messages for the model
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"Please rank the academic quality of the following text on a scale of 1 to 10, provide the score and explanation with a split sperator , limit explanation to 10 words  \n\n{chunk}"}
    ]

    # Get the response from the model
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=0.5,
    )
    # Extract the text from the last response
    score_explanation = response.choices[0].message.content.strip()
    # Try to parse the score and explanation
    try:
        score = int(score_explanation.split()[0])  # The first word should be the score
        explanation = ' '.join(score_explanation.split()[1:])  # The rest is the explanation
    except (ValueError, IndexError):
        # Default values if parsing fails
        score = 0
        explanation = 'Unable to parse score'

    return {"academic_score": score, "explanation": explanation}
# Combine results and calculate the overall academic value
def calculate_academic_value(results):
    # Filter out results where the academic_score is 0
    valid_results = [result for result in results if result["academic_score"] != 0]
    print(valid_results)  # Print valid results to verify filtering
    
    # Calculate the total score using the filtered list
    total_score = sum(result["academic_score"] for result in valid_results)
    
    # Calculate the average score. If there are no valid results, set average_score to 0.
    if len(valid_results) > 0:
        average_score = total_score / len(valid_results)
    else:
        average_score = 0

    return average_score


def analyze_pdf(pdf_path, model_name, chunk_size, tokenizer):
    text = extract_text_from_pdf(pdf_path)
    chunks = split_text_chunks(text, chunk_size, tokenizer)
    results = []

    # Set up threading for parallel requests
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_chunk = {executor.submit(analyze_chunk, chunk, model_name): chunk for chunk in chunks}

        for future in as_completed(future_to_chunk):
            chunk = future_to_chunk[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as exc:
                print(f'Generated an exception for {chunk}: {exc}')
    
    academic_value = calculate_academic_value(results)
    return academic_value

def main():
    pdf_directory = '.'
    model_name = 'gpt-4-0125-preview'
    chunk_size = 1024  # Adjust based on your needs and model limitations

    # Initialise tokenizer and OpenAI client
    tokenizer = tiktoken.get_encoding("cl100k_base")

    # Get a list of all PDF files in the directory
    pdf_files = [file for file in os.listdir(pdf_directory) if file.endswith('.pdf')]

    # Analyze each PDF and store the results
    pdf_scores = []
    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_directory, pdf_file)
        academic_value = analyze_pdf(pdf_path, model_name, chunk_size, tokenizer)
        pdf_scores.append((pdf_file, academic_value))

    # Sort the PDF files based on their academic value
    sorted_pdfs = sorted(pdf_scores, key=lambda x: x[1], reverse=True)

    # Print the sorted list of PDF names
    print("PDF files sorted by academic quality:")
    for pdf, score in sorted_pdfs:
        print(f"{pdf}: {score}")

if __name__ == "__main__":
    main()
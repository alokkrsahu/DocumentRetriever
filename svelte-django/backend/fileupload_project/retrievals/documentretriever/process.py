import os
import json
import argparse
import logging
import pdfplumber
from docx import Document
from odf.opendocument import load
from odf.text import P

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_paragraphs_from_pdf(file_path):
    paragraphs = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    # Improved paragraph splitting
                    page_paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
                    paragraphs.extend(page_paragraphs)
        logging.info(f"Successfully extracted {len(paragraphs)} paragraphs from PDF: {file_path}")
    except Exception as e:
        logging.error(f"Error reading .pdf file '{file_path}': {e}")
    return paragraphs

def extract_paragraphs_from_docx(file_path):
    paragraphs = []
    try:
        doc = Document(file_path)
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():  # Only add non-empty paragraphs
                paragraphs.append(paragraph.text.strip())
        logging.info(f"Successfully extracted {len(paragraphs)} paragraphs from DOCX: {file_path}")
    except Exception as e:
        logging.error(f"Error reading .docx file '{file_path}': {e}")
    return paragraphs

def extract_paragraphs_from_odt(file_path):
    paragraphs = []
    try:
        odt_file = load(file_path)
        paragraphs_elements = odt_file.getElementsByType(P)
        for paragraph in paragraphs_elements:
            text = paragraph.textContent.strip()
            if text:  # Only add non-empty paragraphs
                paragraphs.append(text)
        logging.info(f"Successfully extracted {len(paragraphs)} paragraphs from ODT: {file_path}")
    except Exception as e:
        logging.error(f"Error reading .odt file '{file_path}': {e}")
    return paragraphs

def merge_short_paragraphs(paragraphs, min_words=20):
    merged_paragraphs = []
    current_paragraph = ""
    
    for paragraph in paragraphs:
        if current_paragraph:
            current_paragraph += " " + paragraph
        else:
            current_paragraph = paragraph
        
        word_count = len(current_paragraph.split())
        if word_count >= min_words:
            merged_paragraphs.append(current_paragraph)
            current_paragraph = ""
    
    # Add any remaining text
    if current_paragraph:
        merged_paragraphs.append(current_paragraph)
    
    return merged_paragraphs

def extract_paragraphs_from_txt(file_path):
    paragraphs = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        logging.info(f"Successfully extracted {len(paragraphs)} paragraphs from TXT: {file_path}")
    except Exception as e:
        logging.error(f"Error reading .txt file '{file_path}': {e}")
    return paragraphs



def extract_text_from_folder(folder_path, min_words):
    output = []
    paragraph_id = 1
    unsupported_files = []
    
    logging.info(f"Extracting text from folder: {folder_path}")
    logging.info(f"Files in folder: {os.listdir(folder_path)}")
    
    for root, _, files in os.walk(folder_path):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            logging.info(f"Processing file: {file_path}")
            logging.info(f"File size: {os.path.getsize(file_path)} bytes")
            
            if file_name.lower().endswith('.pdf'):
                paragraphs = extract_paragraphs_from_pdf(file_path)
            elif file_name.lower().endswith('.docx'):
                paragraphs = extract_paragraphs_from_docx(file_path)
            elif file_name.lower().endswith('.odt'):
                paragraphs = extract_paragraphs_from_odt(file_path)
            elif file_name.lower().endswith('.txt'):
                paragraphs = extract_paragraphs_from_txt(file_path)
            else:
                unsupported_files.append(file_name)
                logging.warning(f"Skipping unsupported file format: {file_name}")
                continue

            
            merged_paragraphs = merge_short_paragraphs(paragraphs, min_words)
            
            for para in merged_paragraphs:
                if para:
                    output.append({
                        "id": paragraph_id,
                        "text": para,
                        "source": file_name,
                        "char_count": len(para),
                        "word_count": len(para.split())
                    })
                    paragraph_id += 1
    logging.info(f"Extracted and merged a total of {len(output)} paragraphs from all documents")
    logging.info(f"Total paragraphs extracted: {len(output)}")
    return output, unsupported_files


def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Extract text from documents in a specified folder.")
    parser.add_argument('folder_path', type=str, help="Path to the folder containing the documents")
    parser.add_argument('--min-chars', type=int, default=0, help="Minimum number of characters for a paragraph to be included")
    parser.add_argument('--min-words', type=int, default=20, help="Minimum number of words for a paragraph before merging")
    parser.add_argument('--output-dir', type=str, help="Path to the output directory for extracted data")
    args = parser.parse_args()

    # Check if the provided path is a directory
    if not os.path.isdir(args.folder_path):
        logging.error(f"The provided path '{args.folder_path}' is not a valid directory.")
        print(f"Error: The provided path '{args.folder_path}' is not a valid directory.")
        return

    # Create the output directory if it does not exist
    output_dir = args.output_dir if args.output_dir else os.path.join(args.folder_path, 'sys', 'temp')
    os.makedirs(output_dir, exist_ok=True)
    logging.info(f"Created output directory: {output_dir}")

    # Process the folder and extract text
    documents, unsupported_files = extract_text_from_folder(args.folder_path, args.min_words)

    # Filter paragraphs based on minimum character count
    filtered_documents = [doc for doc in documents if doc['char_count'] >= args.min_chars]

    # Write the extracted text data to a JSON file
    output_file_path = os.path.join(output_dir, 'extracted_data.json')
    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(filtered_documents, f, indent=2, ensure_ascii=False)
    logging.info(f"Wrote {len(filtered_documents)} paragraphs to {output_file_path}")

    # Print the path to the JSON file
    print(f"Files have been saved to {output_file_path}")
    print(f"Total paragraphs extracted and merged: {len(documents)}")
    print(f"Paragraphs after filtering (min {args.min_chars} chars): {len(filtered_documents)}")

    # Print information about unsupported files
    if unsupported_files:
        logging.warning("The following files were skipped due to unsupported format:")
        for file in unsupported_files:
            logging.warning(f"  - {file}")
        print("Warning: Some files were skipped due to unsupported format. Check the log for details.")



if __name__ == "__main__":
    main()


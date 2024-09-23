# initial_processor.py

import os
import sys
import subprocess
import argparse
import json
from pathlib import Path
import logging

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from documentretriever.unified_retriever import UnifiedRetriever

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_script(script_name, *args):
    script_path = Path(__file__).parent / 'documentretriever' / f'{script_name}.py'
    result = subprocess.run(['python3', str(script_path), *args], 
                            capture_output=True, text=True, check=True)
    return result.stdout.strip()

def extract_path(output, prefix):
    for line in output.split('\n'):
        if line.startswith(prefix):
            return line.split(prefix)[-1].strip()
    raise ValueError(f"Could not find path in output: {output}")

def process_documents(tenderdocs, min_chars, min_words):
    # Upload all documents
    upload_output = run_script('upload', tenderdocs)
    destination_folder = extract_path(upload_output, "Files have been saved to")
    
    # Process all documents
    process_output = run_script('process', destination_folder, 
                                '--min-chars', str(min_chars),
                                '--min-words', str(min_words))
    json_output_path = extract_path(process_output, "Files have been saved to")
    
    return json_output_path

def preprocess_documents(json_output_path, index_path):
    with open(json_output_path, 'r') as f:
        documents = json.load(f)
    
    retriever = UnifiedRetriever(documents, on=["text"])
    retriever.save_index(index_path)
    
    logging.info(f"Unified index saved to {index_path}")

def main():
    parser = argparse.ArgumentParser(description="Process and preprocess tender documents.")
    parser.add_argument("tenderdocs", help="Path to the tender documents")
    parser.add_argument("--min-chars", type=int, default=100, 
                        help="Minimum number of characters for a paragraph to be included")
    parser.add_argument("--min-words", type=int, default=30, 
                        help="Minimum number of words for a paragraph before merging")
    args = parser.parse_args()
    
    try:
        processed_docs_path = process_documents(args.tenderdocs, args.min_chars, args.min_words)
        logging.info(f"Documents processed. Output saved to: {processed_docs_path}")
        index_path = Path(processed_docs_path).parent / 'unified_index.faiss'
        preprocess_documents(processed_docs_path, index_path)
        logging.info("Preprocessing completed.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error occurred while processing documents: {e}")
        logging.error(f"Error output: {e.stderr}")
        sys.exit(1)
    except ValueError as e:
        logging.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()


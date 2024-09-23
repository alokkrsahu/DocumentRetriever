import os
import sys
import subprocess
import argparse
import json
import logging
from pathlib import Path
from tqdm import tqdm

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from documentretriever.unified_retriever import UnifiedRetriever

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_script(script_name, *args):
    script_path = Path(__file__).parent / 'documentretriever' / f'{script_name}.py'
    try:
        result = subprocess.run(['python3', str(script_path), *args], 
                                capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running {script_name}: {e.stderr}")
        raise

def extract_path(output, prefix):
    for line in output.split('\n'):
        if line.startswith(prefix):
            return line.split(prefix)[-1].strip()
    raise ValueError(f"Could not find path in output: {output}")

def process_documents(tenderdocs, min_chars, min_words, output_dir):
    logging.info("Starting document processing...")
    
    upload_output = run_script('upload', tenderdocs)
    destination_folder = extract_path(upload_output, "Files have been saved to")
    logging.info(f"Documents uploaded to: {destination_folder}")
    
    process_output = run_script('process', destination_folder, 
                                '--min-chars', str(min_chars),
                                '--min-words', str(min_words),
                                '--output-dir', output_dir)
    json_output_path = extract_path(process_output, "Files have been saved to")
    logging.info(f"Documents processed. Output saved to: {json_output_path}")
    
    return json_output_path

def preprocess_documents(json_output_path, output_dir):
    logging.info("Starting document preprocessing...")
    with open(json_output_path, 'r') as f:
        documents = json.load(f)
    
    retriever = UnifiedRetriever(documents, on=["text"])
    
    index_path = os.path.join(output_dir, 'unified_index.faiss')
    retriever.save_index(index_path)
    
    logging.info(f"Unified index saved to {index_path}")
    return index_path

def main():
    parser = argparse.ArgumentParser(description="Process and preprocess tender documents.")
    parser.add_argument("tenderdocs", help="Path to the tender documents")
    parser.add_argument("--min-chars", type=int, default=100, 
                        help="Minimum number of characters for a paragraph to be included")
    parser.add_argument("--min-words", type=int, default=30, 
                        help="Minimum number of words for a paragraph before merging")
    parser.add_argument("--output-dir", type=str, default="./output",
                        help="Directory to save the extracted_data.json and unified_index.faiss files")
    args = parser.parse_args()
    
    try:
        # Create the output directory if it doesn't exist
        os.makedirs(args.output_dir, exist_ok=True)
        
        processed_docs_path = process_documents(args.tenderdocs, args.min_chars, args.min_words, args.output_dir)
        index_path = preprocess_documents(processed_docs_path, args.output_dir)
        
        logging.info("Preprocessing completed successfully.")
        
        print(f"Extracted data saved to: {processed_docs_path}")
        print(f"Unified index saved to: {index_path}")
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()


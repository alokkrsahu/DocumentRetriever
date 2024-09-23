# runner.py
import os
import json
import logging
import sys
import argparse
from pathlib import Path
from tqdm import tqdm
import numpy as np

# Set environment variable to avoid tokenizer parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"
# Disable PyTorch's sharing of memory objects
os.environ["PYTORCH_DISK_SHM_SIZE"] = "0"

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from documentretriever.unified_retriever import UnifiedRetriever

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

def load_documents(file_path):
    logging.info(f"Attempting to load documents from: {file_path}")
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            documents = json.load(f)
        logging.info(f"Loaded {len(documents)} documents")
        if documents:
            logging.debug(f"First document: {documents[0]}")
        else:
            logging.warning("File exists but no documents were loaded.")
    else:
        logging.error(f"File not found: {file_path}")
        documents = []
    return documents


def process_queries(retriever, queries, methods, k=5):
    results = {}
    for query_id, query_text in tqdm(queries.items(), desc="Processing queries"):
        logging.debug(f"Processing query: {query_id}, text: {query_text}")
        results[query_id] = {}
        for method in methods:
            try:
                result = retriever.retrieve(query_text, method=method, k=k)
                results[query_id][method] = result
                logging.debug(f"Result for method {method}: {result[:2]}...")  # Log first 2 results
            except Exception as e:
                logging.error(f"Error processing query {query_id} with method {method}: {str(e)}")
    return results

def read_query_from_file(file_path):
    with open(file_path, 'r') as f:
        return f.read().strip()

def main(processed_docs_path, methods, k=5, query_file=None, output_dir=None):
    documents = load_documents(processed_docs_path)
    index_path = Path(processed_docs_path).parent / 'unified_index.faiss'
    
    if not documents:
        logging.error("No documents loaded. Cannot proceed with retrieval.")
        return

    if index_path.exists():
        logging.info(f"Loading existing index from {index_path}")
        retriever = UnifiedRetriever.load(documents, str(index_path), key="id", on=["text"])
    else:
        logging.warning(f"Index not found at {index_path}. Creating new index.")
        retriever = UnifiedRetriever(documents, key="id", on=["text"])
        retriever.save_index(str(index_path))


    if query_file:
        # Process the single query from file
        single_query = read_query_from_file(query_file)
        queries = {"single_query": single_query}
        logging.info(f"Processing single query from file: {single_query}")
    else:
        # Try to load queries from file, use default if file not found
        script_dir = os.path.dirname(os.path.abspath(__file__))
        query_file_path = os.path.join(script_dir, 'pastcod', 'output_two_columns.json')
        if os.path.exists(query_file_path):
            with open(query_file_path, 'r') as f:
                queries = json.load(f)
            logging.info(f"Total queries loaded from file: {len(queries)}")
        else:
            logging.warning(f"Query file not found: {query_file_path}. Using default query.")
            queries = {"default_query": "What is the main topic of these documents?"}

    results = process_queries(retriever, queries, methods, k)

    # Create the output directory if it doesn't exist
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'retrieval_results.json')
    else:
        output_file = 'retrieval_results.json'

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, cls=NumpyEncoder)
    
    logging.info(f"Retrieval results saved to: {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the document retrieval process.")
    parser.add_argument("--processed_docs", type=str, required=True, help="Path to the processed documents JSON file")
    parser.add_argument("--method", type=str, nargs='+', default=["bm25"], help="Retrieval methods to use")
    parser.add_argument("--k", type=int, default=5, help="Number of top results to retrieve")
    parser.add_argument("--query_file", type=str, help="Path to file containing a single query (optional)")
    parser.add_argument("--output_dir", type=str, help="Directory to save the retrieval_results.json file")
    args = parser.parse_args()
    
    main(args.processed_docs, args.method, args.k, args.query_file, args.output_dir)


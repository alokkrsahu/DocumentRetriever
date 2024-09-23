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
    with open(file_path, 'r') as f:
        documents = json.load(f)
    logging.info(f"Total documents loaded: {len(documents)}")
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

def main(processed_docs_path, methods, k=5):
    documents = load_documents(processed_docs_path)
    with open('pastcod/output_two_columns.json', 'r') as f:
        queries = json.load(f)
    logging.info(f"Total queries loaded: {len(queries)}")

    index_path = Path(processed_docs_path).parent / 'unified_index.faiss'
    
    if index_path.exists():
        logging.info(f"Loading existing index from {index_path}")
        retriever = UnifiedRetriever(documents, on=["text"])
        retriever.load_index(str(index_path))
    else:
        logging.warning(f"Index not found at {index_path}. Creating new index.")
        retriever = UnifiedRetriever(documents, on=["text"])
        retriever.save_index(str(index_path))

    results = process_queries(retriever, queries, methods, k)

    with open('retrieval_results.json', 'w') as f:
        json.dump(results, f, indent=2, cls=NumpyEncoder)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the document retrieval process.")
    parser.add_argument("--processed_docs", type=str, required=True)
    parser.add_argument("--method", type=str, nargs='+', default=["bm25"])
    parser.add_argument("--k", type=int, default=5)
    args = parser.parse_args()
    
    main(args.processed_docs, args.method, args.k)

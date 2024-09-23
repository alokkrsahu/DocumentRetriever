import json
import argparse
from collections import defaultdict
from operator import itemgetter
from typing import Dict
import os

def load_extracted_data(project_folder):
    extracted_data_path = os.path.join(project_folder, 'sys', 'temp', 'extracted_data.json')
    with open(extracted_data_path, 'r') as f:
        return {item['id']: item for item in json.load(f)}

def load_clause_data(project_folder):
    clause_data_path = os.path.join(project_folder, '..', '..', 'retrievals', 'pastcod', 'output_two_columns.json')
    with open(clause_data_path, 'r') as f:
        return json.load(f)

def preprocess_data(data: Dict) -> Dict:
    methods_to_normalize = ['bm25', 'embedding', 'tfidf']
    for clause_index, methods in data.items():
        for method, results in methods.items():
            if method in methods_to_normalize:
                if isinstance(results[0], dict):  # For methods like 'embedding'
                    for result in results:
                        result['similarity'] *= 100
                elif isinstance(results[0], list):  # For methods like 'bm25', 'tfidf'
                    for result_list in results:
                        for result in result_list:
                            result['similarity'] *= 100
    return data

def analyze_retrieval_results(data, top_m_methods, min_threshold, top_n_docs, min_frequency, extracted_data, clause_data):
    doc_analysis = defaultdict(lambda: {"frequency": 0, "clause_ids": defaultdict(lambda: defaultdict(float))})
    
    for clause_id, methods in data.items():
        for method, results in methods.items():
            if isinstance(results[0], dict):
                result_list = [results]
            elif isinstance(results[0], list):
                result_list = results
            else:
                continue

            for result_sublist in result_list:
                for result in result_sublist:
                    doc_id = result["id"]
                    similarity = result["similarity"]
                    
                    if similarity >= min_threshold:
                        doc_analysis[doc_id]["frequency"] += 1
                        doc_analysis[doc_id]["clause_ids"][clause_id][method] = max(
                            doc_analysis[doc_id]["clause_ids"][clause_id][method],
                            similarity
                        )

    doc_analysis = {k: v for k, v in doc_analysis.items() if v["frequency"] >= min_frequency}
    sorted_docs = sorted(doc_analysis.items(), key=lambda x: x[1]["frequency"], reverse=True)

    output = {}
    for doc_id, info in sorted_docs[:top_n_docs]:
        sorted_clause_ids = sorted(
            info["clause_ids"].items(), 
            key=lambda x: max(x[1].values()), 
            reverse=True
        )
        
        clause_data_output = {}
        for clause_id, methods in sorted_clause_ids:
            sorted_methods = sorted(methods.items(), key=itemgetter(1), reverse=True)
            clause_data_output[clause_id] = {
                "clause_text": clause_data[clause_id]["Clause"],
                **dict(sorted_methods[:top_m_methods])
            }
        
        doc_data = extracted_data.get(int(doc_id), {})
        output[doc_id] = {
            "document_text": doc_data.get("text", ""),
            "document_source": doc_data.get("source", ""),
            "frequency": info["frequency"],
            "clause_ids": clause_data_output
        }

    return output

def main():
    parser = argparse.ArgumentParser(description='Analyze JSON file for document frequencies and method scores.')
    parser.add_argument('file_path', type=str, help='Path to the JSON file')
    parser.add_argument('output_path', type=str, help='Path to save the output JSON file')
    parser.add_argument('project_folder', type=str, help='Path to the project folder')
    parser.add_argument('--min_frequency', type=int, default=1, help='Minimum frequency to include in results (default: 1)')
    parser.add_argument('--top_m_methods', type=int, default=3, help='Top M methods to show for each clause (default: 3)')
    parser.add_argument('--min_threshold', type=float, default=10, help='Minimum threshold for scores (default: 10)')
    parser.add_argument('--top_n_docs', type=int, default=5, help='Number of top document IDs to present (default: 5)')
    args = parser.parse_args()

    with open(args.file_path, 'r') as f:
        data = json.load(f)

    extracted_data = load_extracted_data(args.project_folder)
    clause_data = load_clause_data(args.project_folder)

    preprocessed_data = preprocess_data(data)

    results = analyze_retrieval_results(
        preprocessed_data, 
        args.top_m_methods, 
        args.min_threshold, 
        args.top_n_docs, 
        args.min_frequency,
        extracted_data,
        clause_data
    )

    with open(args.output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Analysis complete. Results saved to {args.output_path}")

if __name__ == "__main__":
    main()
import json
import argparse
from collections import defaultdict
from typing import Dict, List, Union

def load_json(file_path: str) -> Dict:
    with open(file_path, 'r') as file:
        return json.load(file)

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

def analyze_json(data: Dict, min_similarity: float) -> Dict[str, Dict[str, Union[int, Dict[str, Dict[str, float]]]]]:
    doc_analysis = defaultdict(lambda: {"frequency": 0, "clause_similarity": defaultdict(dict)})
    
    for clause_index, methods in data.items():
        for method, results in methods.items():
            if isinstance(results[0], dict):  # For methods like 'embedding', 'encoder', 'dpr'
                process_results(results, clause_index, method, doc_analysis, min_similarity)
            elif isinstance(results[0], list):  # For methods like 'bm25', 'tfidf', etc.
                for result_list in results:
                    process_results(result_list, clause_index, method, doc_analysis, min_similarity)

    return dict(doc_analysis)

def process_results(results: List[Dict[str, Union[int, float]]], clause_index: str, method: str, 
                    doc_analysis: Dict[str, Dict[str, Union[int, Dict[str, Dict[str, float]]]]], 
                    min_similarity: float):
    for result in results:
        doc_id = str(result['id'])
        similarity = result['similarity']
        if similarity >= min_similarity:
            doc_analysis[doc_id]["frequency"] += 1
            doc_analysis[doc_id]["clause_similarity"][clause_index][method] = round(similarity, 2)

def filter_by_frequency(doc_analysis: Dict, min_frequency: int) -> Dict:
    return {
        doc_id: data
        for doc_id, data in doc_analysis.items()
        if data["frequency"] >= min_frequency
    }

def sort_by_frequency(doc_analysis: Dict) -> Dict:
    return dict(sorted(doc_analysis.items(), key=lambda x: x[1]['frequency'], reverse=True))

def main():
    parser = argparse.ArgumentParser(description='Analyze JSON file for document frequencies and clause analysis.')
    parser.add_argument('file_path', type=str, help='Path to the JSON file')
    parser.add_argument('output_path', type=str, help='Path to save the output JSON file')
    parser.add_argument('--min_similarity', type=float, default=0.0, help='Minimum similarity score to consider (default: 0.0)')
    parser.add_argument('--min_frequency', type=int, default=1, help='Minimum frequency to include in results (default: 1)')
    args = parser.parse_args()

    data = load_json(args.file_path)
    preprocessed_data = preprocess_data(data)
    analysis_result = analyze_json(preprocessed_data, args.min_similarity)
    filtered_result = filter_by_frequency(analysis_result, args.min_frequency)
    sorted_result = sort_by_frequency(filtered_result)

    with open(args.output_path, 'w') as f:
        json.dump(sorted_result, f, indent=2)

    print(f"Analysis complete. Results saved to {args.output_path}")

if __name__ == "__main__":
    main()

#################    NOTES     #################
Problem below:

This scripts are working absolutely fine.

fuzz works slow
flash not returning any results

All other methods are working fine.

Optimization work required in batch processing. Script need to be tested for effeciency in GPU environment.

################################################
run using below commands

1. Process the documents:
python3 initial_processor.py /home/alok/Documents/tenderpython/tenderdocuments --min-chars 100 --min-words 30 --output-dir /path/to/your/preferred/folder

--min-words:

Default value: 20
Purpose: Determines the minimum number of words a paragraph should have before it's merged with the next paragraph.
If not specified, the script will use 20 as the default value.


--min-chars:

Default value: 0
Purpose: Filters out paragraphs that have fewer characters than this value after merging.
If not specified, the script will use 0 as the default value, meaning no paragraphs will be filtered out based on character count.


2. RUN THE RETRIEVAL FUNCTION
python3 runner.py --processed_docs /path/to/your/preferred/folder/extracted_data.json --method  bm25 tfidf flash lunr fuzz embedding encoder dpr


python3 runner.py --processed_docs /path/to/your/preferred/folder/extracted_data.json --method bm25 tfidf flash lunr fuzz embedding encoder dpr --output_dir /path/to/your/preferred/folder

python runner.py --processed_docs all_files/20240911_145146/sys/temp/extracted_data.json --method bm25 tfidf --k 5 --query_file path/to/query.txt --output_dir /path/to/output/directory


python runner.py --processed_docs all_files/20240911_145146/sys/temp/extracted_data.json --method bm25 tfidf --k 5
python runner.py --processed_docs all_files/20240911_145146/sys/temp/extracted_data.json --method bm25 tfidf --k 5 --query_file path/to/query.txt

3. ANALYSE THE EXTRACTED DOCUMENTS

BELOW: 5 is the frequency

To analyze all methods and print JSON to console:
python analyser.py retrieval_results.json analysis_output.json


To analyze specific methods and save JSON to a file:
python analyser.py retrieval_results.json analysis_output.json --min_similarity 50 --min_frequency 5



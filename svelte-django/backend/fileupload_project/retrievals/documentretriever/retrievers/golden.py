import logging
from cherche import retrieve
from sentence_transformers import SentenceTransformer
import faiss
from rapidfuzz import fuzz
from lenlp import sparse

class DocumentRetriever:
    def __init__(self, method, documents, on, key="id", use_gpu=False, **kwargs):
        self.method = method.lower()
        self.documents = documents
        self.key = key
        self.on = on
        self.use_gpu = use_gpu
        self.kwargs = kwargs
        self.retriever = None
        self.encoder_model = None
        self.query_encoder = None

        logging.info(f"Initializing DocumentRetriever with method: {self.method}")
        logging.debug(f"Number of documents: {len(documents)}")
        logging.debug(f"Sample document: {documents[0] if documents else 'No documents'}")

        if self.method == "bm25":
            self.retriever = self._init_bm25()
        elif self.method == "tfidf":
            self.retriever = self._init_tfidf()
        elif self.method == "flash":
            self.retriever = self._init_flash()
        elif self.method == "lunr":
            self.retriever = self._init_lunr()
        elif self.method == "fuzz":
            self.retriever = self._init_fuzz()
        elif self.method == "embedding":
            self.retriever = self._init_embedding()
        else:
            logging.error(f"Unknown method: {self.method}")
            raise ValueError(f"Unknown method: {self.method}")

    def _filter_kwargs(self, valid_params):
        filtered = {k: v for k, v in self.kwargs.items() if k in valid_params}
        logging.debug(f"Filtered kwargs for {self.method}: {filtered}")
        return filtered

    def _init_bm25(self):
        logging.info("Initializing BM25 retriever")
        valid_params = ['k']
        filtered_kwargs = self._filter_kwargs(valid_params)
        try:
            logging.debug(f"Number of documents: {len(self.documents)}")
            logging.debug(f"Sample document keys: {list(self.documents[0].keys()) if self.documents else 'No documents'}")
            logging.debug(f"Fields used for BM25: {self.on}")
            logging.debug(f"Sample document content for BM25 fields: {' '.join(str(self.documents[0].get(field, '')) for field in self.on)[:100]}...")
            
            retriever = retrieve.BM25(key=self.key, on=self.on, documents=self.documents, **filtered_kwargs)
            logging.info("BM25 retriever initialized successfully")
            return retriever
        except Exception as e:
            logging.error(f"Error initializing BM25 retriever: {str(e)}", exc_info=True)
            raise

    def _init_tfidf(self):
        logging.info("Initializing TF-IDF retriever")
        valid_params = ['vectorizer_params']
        filtered_kwargs = self._filter_kwargs(valid_params)
        try:
            count_vectorizer = sparse.TfidfVectorizer(**filtered_kwargs.get("vectorizer_params", {}))
            retriever = retrieve.TfIdf(key=self.key, on=self.on, documents=self.documents, tfidf=count_vectorizer)
            logging.info("TF-IDF retriever initialized successfully")
            return retriever
        except Exception as e:
            logging.error(f"Error initializing TF-IDF retriever: {str(e)}", exc_info=True)
            raise

    def _init_flash(self):
        logging.info("Initializing Flash retriever")
        try:
            retriever = retrieve.Flash(key=self.key, on=self.on)
            retriever.add(self.documents)
            logging.info("Flash retriever initialized successfully")
            return retriever
        except Exception as e:
            logging.error(f"Error initializing Flash retriever: {str(e)}", exc_info=True)
            raise

    def _init_lunr(self):
        logging.info("Initializing Lunr retriever")
        try:
            retriever = retrieve.Lunr(key=self.key, on=self.on, documents=self.documents)
            logging.info("Lunr retriever initialized successfully")
            return retriever
        except Exception as e:
            logging.error(f"Error initializing Lunr retriever: {str(e)}", exc_info=True)
            raise

    def _init_fuzz(self):
        logging.info("Initializing Fuzz retriever")
        valid_params = ['fuzzer']
        filtered_kwargs = self._filter_kwargs(valid_params)
        try:
            fuzzer = filtered_kwargs.get("fuzzer", fuzz.partial_ratio)
            retriever = retrieve.Fuzz(key=self.key, on=self.on, fuzzer=fuzzer)
            retriever.add(self.documents)
            logging.info("Fuzz retriever initialized successfully")
            return retriever
        except Exception as e:
            logging.error(f"Error initializing Fuzz retriever: {str(e)}", exc_info=True)
            raise

    def _init_embedding(self):
        logging.info("Initializing Embedding retriever")
        valid_params = ['model_name']
        filtered_kwargs = self._filter_kwargs(valid_params)
        try:
            model_name = filtered_kwargs.get("model_name", "sentence-transformers/all-mpnet-base-v2")
            self.encoder_model = SentenceTransformer(model_name, device="cuda" if self.use_gpu else "cpu")
            encoder = self.encoder_model.encode

            def wrapped_encoder(texts):
                if isinstance(texts, str):
                    texts = [texts]
                return encoder(texts)

            d = wrapped_encoder(["This is a sample document."])[0].shape[0]
            index = faiss.IndexFlatL2(d)
            if self.use_gpu:
                index = faiss.index_cpu_to_gpu(faiss.StandardGpuResources(), 0, index)

            retriever = retrieve.Embedding(key=self.key, index=index)
            embeddings_documents = wrapped_encoder([doc["text"] for doc in self.documents])
            retriever.add(documents=self.documents, embeddings_documents=embeddings_documents)
            logging.info("Embedding retriever initialized successfully")
            return retriever
        except Exception as e:
            logging.error(f"Error initializing Embedding retriever: {str(e)}", exc_info=True)
            raise


    def retrieve(self, query, k=10, batch_size=64):
        logging.info(f"Retrieving with method: {self.method}")
        
        # Extract the 'Clause' value if query is a dictionary
        if isinstance(query, dict) and 'Clause' in query:
            query = query['Clause']
        
        if isinstance(query, str):
            query = [query]
    
        logging.info(f"Processed query type: {type(query)}")
        logging.debug(f"Processed query content: {query[0][:100]}...")  # Log the first 100 characters of the first query
    
        try:
            if self.method in ["encoder", "embedding"]:
                query_embeddings = self.encoder_model.encode(query)
                results = self.retriever(q=query_embeddings, k=k)
            elif self.method == "dpr":
                query_embeddings = self.query_encoder(query)
                results = self.retriever(q=query_embeddings, k=k)
            elif self.method == "flash":
                results = self.retriever(query)
            else:
                logging.debug(f"Calling {self.method} retriever with query type: {type(query)}")
                results = self.retriever(query, k=k)
            
            logging.debug(f"Retrieved {len(results)} results")
            return results
        except Exception as e:
            logging.error(f"Error in retrieve method for {self.method}: {str(e)}", exc_info=True)
            raise

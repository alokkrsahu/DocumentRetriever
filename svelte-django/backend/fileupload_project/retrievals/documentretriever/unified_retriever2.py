import faiss
import torch
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import logging
from .retrievers.golden import DocumentRetriever

class UnifiedRetriever:
    def __init__(self, documents, key="id", on=["text"], batch_size=32):
        self.documents = documents
        self.key = key
        self.on = on
        self.batch_size = batch_size
        
        logging.info(f"Initializing UnifiedRetriever with {len(documents)} documents")
        logging.debug(f"Sample document: {documents[0] if documents else 'No documents'}")
        
        # Determine device (GPU if available, else CPU)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logging.info(f"Using device: {self.device}")
        
        # Initialize encoders
        self.dpr_encoder = SentenceTransformer('facebook-dpr-ctx_encoder-single-nq-base', device=self.device)
        self.dpr_query_encoder = SentenceTransformer('facebook-dpr-question_encoder-single-nq-base', device=self.device)
        self.encoder = SentenceTransformer("sentence-transformers/all-mpnet-base-v2", device=self.device)
        
        # Create a unified index for DPR and Encoder
        self.create_unified_index()
        
        # Initialize other retrievers from golden.py
        self.initialize_other_retrievers()
    
    def create_unified_index(self):
        logging.info("Creating unified index")
        texts = [doc[self.on[0]] for doc in self.documents]
        
        # Encode documents using both DPR and Encoder
        dpr_embeddings = self.encode_batch(texts, self.dpr_encoder)
        encoder_embeddings = self.encode_batch(texts, self.encoder)
        
        # Concatenate embeddings
        unified_embeddings = torch.cat([dpr_embeddings, encoder_embeddings], dim=1)
        
        # Create Faiss index
        embedding_dim = unified_embeddings.shape[1]
        self.index = faiss.IndexFlatL2(embedding_dim)
        if self.device == "cuda":
            self.gpu_resource = faiss.StandardGpuResources()
            self.index = faiss.index_cpu_to_gpu(self.gpu_resource, 0, self.index)
        
        # Add embeddings to index
        self.index.add(unified_embeddings.cpu().numpy())
        logging.info(f"Created unified index with dimension {embedding_dim}")
    

    def initialize_other_retrievers(self):
        self.other_retrievers = {}
        methods = ["bm25", "tfidf", "flash", "lunr", "fuzz", "embedding"]
        
        for method in methods:
            try:
                self.other_retrievers[method] = DocumentRetriever(
                    method=method,
                    documents=self.documents,
                    on=self.on,
                    key=self.key,
                    use_gpu=(self.device == "cuda")
                )
                logging.info(f"Initialized {method} retriever")
            except Exception as e:
                logging.error(f"Failed to initialize {method} retriever: {str(e)}", exc_info=True)
        
        # Initialize DPR and Encoder separately
        try:
            self.other_retrievers['dpr'] = DPRRetriever(self.documents, key=self.key, on=self.on)
            logging.info("Initialized DPR retriever")
        except Exception as e:
            logging.error(f"Failed to initialize DPR retriever: {str(e)}", exc_info=True)
        
        try:
            self.other_retrievers['encoder'] = DocumentRetriever(self.documents, key=self.key, on=self.on)
            logging.info("Initialized Encoder retriever")
        except Exception as e:
            logging.error(f"Failed to initialize Encoder retriever: {str(e)}", exc_info=True)
    

    
    def encode_batch(self, texts, model):
        logging.debug(f"Encoding batch of {len(texts)} texts")
        embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i+self.batch_size]
            with torch.no_grad():
                batch_embeddings = model.encode(batch, convert_to_tensor=True, device=self.device)
                embeddings.append(batch_embeddings.cpu())
        return torch.cat(embeddings)
    
    def retrieve(self, query, method, k=10):
        logging.info(f"UnifiedRetriever: Retrieving with method: {method}")
        
        # Extract the 'Clause' value if query is a dictionary
        if isinstance(query, dict) and 'Clause' in query:
            query = query['Clause']
        
        logging.debug(f"Query type: {type(query)}")
        logging.debug(f"Query content: {query[:100]}...")  # Log the first 100 characters
    
        try:
            if method in ["dpr", "encoder"]:
                return self.retrieve_vector(query, method, k)
            elif method in self.other_retrievers:
                return self.other_retrievers[method].retrieve(query, k=k)
            else:
                raise ValueError(f"Unknown method: {method}")
        except Exception as e:
            logging.error(f"Error in UnifiedRetriever retrieve method for {method}: {str(e)}", exc_info=True)
            raise

    
    def retrieve_vector(self, query, method, k=10):
        logging.debug(f"Performing vector retrieval for method: {method}")
        if method == "dpr":
            query_embedding = self.dpr_query_encoder.encode([query], convert_to_tensor=True, device=self.device)
        elif method == "encoder":
            query_embedding = self.encoder.encode([query], convert_to_tensor=True, device=self.device)
        
        # Pad the query embedding to match the unified embedding size
        padding_size = self.index.d - query_embedding.shape[1]
        padded_query_embedding = torch.cat([query_embedding, torch.zeros(1, padding_size, device=self.device)], dim=1)
        
        # Perform search
        distances, indices = self.index.search(padded_query_embedding.cpu().numpy(), k)
        
        # Prepare results
        results = []
        for i, distance in zip(indices[0], distances[0]):
            results.append({
                "id": self.documents[i][self.key],
                "similarity": 1 / (1 + distance)  # Convert distance to similarity
            })
        
        logging.debug(f"Retrieved {len(results)} results")
        return results
    
    def save_index(self, file_path):
        logging.info(f"Saving index to {file_path}")
        if self.device == "cuda":
            # If the index is on GPU, we need to move it to CPU first
            index_cpu = faiss.index_gpu_to_cpu(self.index)
        else:
            index_cpu = self.index
        faiss.write_index(index_cpu, str(file_path))
        logging.info(f"Saved index to {file_path}")
    
    def load_index(self, file_path):
        logging.info(f"Loading index from {file_path}")
        self.index = faiss.read_index(str(file_path))
        if self.device == "cuda":
            self.gpu_resource = faiss.StandardGpuResources()
            self.index = faiss.index_cpu_to_gpu(self.gpu_resource, 0, self.index)
        logging.info(f"Loaded index from {file_path}")

#  documentretriever/retrievers/encoder.py

from cherche import retrieve
from sentence_transformers import SentenceTransformer
import faiss
import torch
from tqdm import tqdm
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DocumentRetriever:
    def __init__(self, documents, model_name="sentence-transformers/all-mpnet-base-v2", 
                 key="id", on=["text"], batch_size=32):
        self.documents = documents
        self.key = key
        self.on = on
        self.batch_size = batch_size
        
        # Determine device (GPU if available, else CPU)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logging.info(f"Using device: {self.device}")
        
        self.model = SentenceTransformer(model_name, device=self.device)
        
        # Get the embedding dimension from the model
        embedding_dim = self.model.get_sentence_embedding_dimension()
        
        # Create a Faiss index for storing embeddings
        self.index = faiss.IndexFlatL2(embedding_dim)
        if self.device == "cuda":
            self.index = faiss.index_cpu_to_gpu(faiss.StandardGpuResources(), 0, self.index)
        
        # Initialize the retriever with the encoder and index
        self.retriever = retrieve.Encoder(
            key=self.key,
            on=self.on,
            encoder=self.encode,
            index=self.index,
            normalize=True
        )
        
        # Add documents to the retriever
        self.add_documents(documents)
    
    def encode(self, texts):
        embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i+self.batch_size]
            with torch.no_grad():
                batch_embeddings = self.model.encode(batch, convert_to_tensor=True, device=self.device)
                embeddings.append(batch_embeddings.cpu())
        return torch.cat(embeddings).numpy()

    def add_documents(self, documents):
        try:
            texts = [doc[self.on[0]] for doc in documents]
        except KeyError as e:
            logging.error(f"KeyError: {e}. The specified field '{self.on[0]}' is not present in all documents.")
            logging.error(f"Document structure: {documents[0].keys()}")
            logging.error("Please ensure that all documents contain the specified field.")
            raise
        embeddings = self.encode(texts)
        self.retriever = self.retriever.add(documents=documents, embeddings_documents=embeddings)

    def retrieve(self, query, k=10):
        if isinstance(query, str):
            query = [query]
        results = self.retriever(query, k=k)
        return results

    def save_index(self, file_path):
        if self.device == "cuda":
            index_cpu = faiss.index_gpu_to_cpu(self.index)
            faiss.write_index(index_cpu, file_path)
        else:
            faiss.write_index(self.index, file_path)

    def load_index(self, file_path):
        self.index = faiss.read_index(file_path)
        if self.device == "cuda":
            self.index = faiss.index_cpu_to_gpu(faiss.StandardGpuResources(), 0, self.index)
        self.retriever.index = self.index

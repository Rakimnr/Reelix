import faiss
import numpy as np
import json
import os

class IndexBuilder:
    def __init__(self, embedding_dim: int = 512):
        self.index = faiss.IndexFlatL2(embedding_dim)
        self.metadata = []

    def add_embeddings(self, embeddings: np.ndarray, meta_list: list[dict]):
        if len(embeddings) != len(meta_list):
            raise ValueError("Embeddings and metadata must have the same length")
        
        self.index.add(embeddings)
        self.metadata.extend(meta_list)
        
    def save(self, index_path: str, meta_path: str):
        faiss.write_index(self.index, index_path)
        with open(meta_path, 'w') as f:
            json.dump(self.metadata, f, indent=2)
            
    def load(self, index_path: str, meta_path: str):
        if not os.path.exists(index_path) or not os.path.exists(meta_path):
            raise FileNotFoundError("Index or metadata file not found.")
        self.index = faiss.read_index(index_path)
        with open(meta_path, 'r') as f:
            self.metadata = json.load(f)

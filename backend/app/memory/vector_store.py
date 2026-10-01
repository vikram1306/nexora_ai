import os
from typing import List, Dict, Any

try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    HAS_VECTOR_DB = True
except ImportError:
    HAS_VECTOR_DB = False

from app.core.config import settings

class VectorMemoryStore:
    """Enterprise Vector Database Manager using ChromaDB & SentenceTransformers with lazy model loading."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorMemoryStore, cls).__new__(cls)
            cls._instance._init_store()
        return cls._instance

    def _init_store(self):
        self.chroma_client = None
        self.embedding_model = None
        self._model_loaded = False

    def _ensure_model_loaded(self):
        """Lazy load SentenceTransformer only when vector indexing/search is actually called."""
        if not self._model_loaded and HAS_VECTOR_DB:
            try:
                os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
                self.chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
                self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
                self._model_loaded = True
            except Exception:
                self._model_loaded = False

    def get_tenant_collection(self, tenant_id: str):
        self._ensure_model_loaded()
        if self.chroma_client:
            collection_name = f"tenant_{tenant_id.replace('-', '_')}"
            return self.chroma_client.get_or_create_collection(name=collection_name)
        return None

    def index_dataset_metadata(self, tenant_id: str, dataset_id: str, department: str, profile_data: Dict[str, Any]):
        self._ensure_model_loaded()
        collection = self.get_tenant_collection(tenant_id)
        if not collection or not self.embedding_model:
            return

        documents = []
        metadatas = []
        ids = []

        # Index KPIs
        kpi_text = f"Department: {department}. Dataset KPIs and summaries: {profile_data.get('kpis_extracted')}"
        documents.append(kpi_text)
        metadatas.append({"dataset_id": dataset_id, "department": department, "type": "kpi"})
        ids.append(f"{dataset_id}_kpi")

        # Index Trends
        for idx, trend in enumerate(profile_data.get("trends_detected", [])):
            trend_text = f"Department: {department}. Metric trend for {trend['metric']}: {trend['direction']} by {trend['change_percentage']}%. Start: {trend['start_val']}, End: {trend['end_val']}"
            documents.append(trend_text)
            metadatas.append({"dataset_id": dataset_id, "department": department, "type": "trend"})
            ids.append(f"{dataset_id}_trend_{idx}")

        if documents:
            embeddings = self.embedding_model.encode(documents).tolist()
            collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )

    def search_memory(self, tenant_id: str, query: str, department: str = None, top_k: int = 5) -> List[Dict[str, Any]]:
        self._ensure_model_loaded()
        collection = self.get_tenant_collection(tenant_id)
        if not collection or not self.embedding_model or collection.count() == 0:
            return []

        query_embedding = self.embedding_model.encode([query]).tolist()
        where_clause = {"department": department} if department else None

        results = collection.query(
            query_embeddings=query_embedding,
            n_results=min(top_k, collection.count()),
            where=where_clause
        )

        output = []
        if results and results.get("documents"):
            for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                output.append({
                    "content": doc,
                    "metadata": meta
                })

        return output

vector_memory_store = VectorMemoryStore()

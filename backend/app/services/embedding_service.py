"""Configurable embeddings provider abstraction layer."""

from abc import ABC, abstractmethod
from typing import List, Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger


class BaseEmbeddingProvider(ABC):
    """Abstract base class for embedding models."""

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Compute embeddings for a batch of documents."""
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Compute embedding for a single query string."""
        pass


class HuggingFaceEmbeddingProvider(BaseEmbeddingProvider):
    """Local HuggingFace embedding provider using sentence-transformers."""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self._model = None

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        model = self._get_model()
        embeddings = model.encode(texts, batch_size=64, convert_to_numpy=True, show_progress_bar=False)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        model = self._get_model()
        embedding = model.encode([text], convert_to_numpy=True, show_progress_bar=False)[0]
        return embedding.tolist()


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """Deterministic pseudo-embedding for rapid testing without downloading weights."""

    def __init__(self, dim: int = 384):
        self.dim = dim

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [[0.01 * (i % 10) for i in range(self.dim)] for _ in texts]

    def embed_query(self, text: str) -> List[float]:
        return [0.01 * (i % 10) for i in range(self.dim)]


def get_embedding_provider() -> BaseEmbeddingProvider:
    """Factory for embedding provider."""
    provider = settings.EMBEDDING_PROVIDER.lower()
    if provider == "mock":
        return MockEmbeddingProvider()
    try:
        return HuggingFaceEmbeddingProvider()
    except Exception as e:
        logger.warning(f"Failed to initialize HuggingFace embeddings: {e}. Using mock embedding provider.")
        return MockEmbeddingProvider()


embedding_service = get_embedding_provider()

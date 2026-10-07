"""Application configuration using Pydantic Settings."""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    PROJECT_NAME: str = "GraphMind — Adaptive Agentic GraphRAG"
    BACKEND_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    API_PREFIX: str = "/api/v1"
    BACKEND_PORT: int = 8000
    FRONTEND_PORT: int = 3000

    # LLM Settings
    LLM_PROVIDER: str = Field(default="gemini", description="gemini | openai | anthropic | ollama | mock")
    LLM_MODEL: str = "gemini-1.5-flash"
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    # Embeddings
    EMBEDDING_PROVIDER: str = Field(default="huggingface", description="huggingface | openai | gemini")
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Vector Store (ChromaDB)
    VECTOR_STORE_PROVIDER: str = "chromadb"
    CHROMA_PERSIST_DIR: str = "./data/processed/chroma"
    CHROMA_COLLECTION_NAME: str = "olympic_corpus"

    # Graph Store (TigerGraph)
    GRAPH_STORE_PROVIDER: str = "tigergraph"
    TIGERGRAPH_HOST: str = "http://127.0.0.1"
    TIGERGRAPH_RESTPP_PORT: int = 9000
    TIGERGRAPH_GS_PORT: int = 14240
    TIGERGRAPH_GRAPH_NAME: str = "OlympicGraph"
    TIGERGRAPH_USERNAME: str = "tigergraph"
    TIGERGRAPH_PASSWORD: str = "tigergraph"
    TIGERGRAPH_SECRET: Optional[str] = None
    TIGERGRAPH_TOKEN: Optional[str] = None

    # Agent Settings
    MAX_AGENT_ITERATIONS: int = 6
    TOKEN_BUDGET_LIMIT: int = 8000
    DEFAULT_TOP_K: int = 5


settings = Settings()

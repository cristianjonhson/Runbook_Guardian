"""Configuración centralizada de la aplicación usando pydantic-settings."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de Runbook Guardian.

    Valores cargados desde variables de entorno o archivo .env.
    Las variables sensibles (AWS) no tienen valor por defecto y fallarán
    si se necesitan sin estar definidas.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Aplicación ---
    app_env: str = "development"
    app_debug: bool = True
    app_port: int = 8000
    app_host: str = "0.0.0.0"
    app_version: str = "0.1.0"

    # --- Runbooks ---
    runbooks_path: Path = Path("./data/runbooks")
    runbook_max_age_days: int = 90

    # --- Embeddings ---
    embedding_model: str = "all-MiniLM-L6-v2"
    chroma_persist_dir: Path = Path("./chroma_data")
    chroma_collection_name: str = "runbooks"

    # --- Seguridad ---
    destructive_patterns: str = (
        r"rm\s+-rf|rm\s+-f|drop\s+database|drop\s+table|delete\s+from|truncate|"
        r"format\s+c:|shutdown\s+-h|halt|kill\s+-9|iptables\s+-F|chmod\s+777|"
        r"kubectl\s+delete|terraform\s+destroy|aws\s+.*--force"
    )

    # --- RAG Provider ---
    rag_provider: str = "local"  # local | bedrock | auto

    # --- AWS / Bedrock ---
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-3-haiku-20240307-v1:0"
    bedrock_embedding_model_id: str = "amazon.titan-embed-text-v2:0"
    bedrock_max_tokens: int = 500
    bedrock_temperature: float = 0.1
    bedrock_timeout_seconds: int = 10
    s3_runbooks_bucket: str = ""

    # --- Logging ---
    log_level: str = "INFO"
    log_format: str = "json"

    # --- Query ---
    query_max_length: int = 500
    retrieval_top_k: int = 5
    similarity_threshold: float = 0.3


settings = Settings()

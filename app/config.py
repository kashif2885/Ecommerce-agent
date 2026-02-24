from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    model_name: str = "gpt-5.1"
    embedding_model: str = "text-embedding-3-large"
    chroma_persist_dir: str = "./chroma_db_v2"
    pdf_path: str = "./Data/Adoob_FAQ.pdf"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

import os
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Read from .env (load_dotenv should be called once in main.py)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not found in environment variables")

client = OpenAI(api_key=OPENAI_API_KEY)


def embed_texts(texts: list[str]) -> np.ndarray:
    """
    Single embedding function for:
    - product embeddings
    - query embeddings

    Returns:
        np.ndarray of shape (len(texts), embedding_dim) with dtype float32
    """

    if not texts:
        raise ValueError("embed_texts received empty input")

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts
    )

    embeddings = [item.embedding for item in response.data]

    # Convert to numpy float32 for FAISS
    embeddings_np = np.array(embeddings, dtype=np.float32)

    return embeddings_np

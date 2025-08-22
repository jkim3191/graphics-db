from sentence_transformers import SentenceTransformer
import torch

device = "cuda" if torch.cuda.is_available() else "cpu"

# Model
sbert_model = SentenceTransformer("all-mpnet-base-v2", device=device)


def get_sbert_embeddings(text_query: str):
    """
    Generates SBERT embeddings for a given text query.
    """
    return sbert_model.encode(
        text_query, convert_to_tensor=False, show_progress_bar=False
    )

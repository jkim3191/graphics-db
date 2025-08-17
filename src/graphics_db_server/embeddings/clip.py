import numpy as np
import open_clip
import torch
import torch.nn.functional as F

from graphics_db_server.core.config import USE_MEAN_POOL

device = "cuda" if torch.cuda.is_available() else "cpu"

# Models
(
    clip_model,
    _,
    clip_preprocess,
) = open_clip.create_model_and_transforms(
    "ViT-L-14",
    pretrained="laion2b_s32b_b82k",
)
clip_tokenizer = open_clip.get_tokenizer("ViT-L-14")


def get_clip_embeddings(text_query: str):
    with torch.no_grad():
        query_feature_clip = clip_model.encode_text(
            clip_tokenizer([text_query]).to(device)
        )
        query_feature_clip = F.normalize(query_feature_clip, p=2, dim=-1)

        if query_feature_clip.ndim != 1:
            if USE_MEAN_POOL:
                query_feature_clip = query_feature_clip.mean(0)
            else:
                raise NotImplementedError()

    return query_feature_clip.numpy()

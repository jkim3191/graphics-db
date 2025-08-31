"""
Script to download the Objathor CLIP/SBERT embeddings from AllenAI.
"""

import os
from pathlib import Path
from huggingface_hub import snapshot_download
from dotenv import load_dotenv


def main():
    load_dotenv()
    
    local_dir = Path(__file__).parent
    cache_dir = os.getenv("CACHE_DIR", os.path.expanduser("~/.cache/huggingface/hub"))
        
    repo_id = "yunho-c/objathor-assets"
    repo_type = "dataset"
        
    try:
        
        kwargs = {
            "repo_id": repo_id,
            "repo_type": repo_type,
            "local_dir": local_dir,
            "cache_dir": cache_dir,
        }
        
        downloaded_path = snapshot_download(**kwargs)
        
        print(f"Successfully downloaded to: {downloaded_path}")
                
    except Exception as e:
        print(f"Error downloading: {e}")


if __name__ == "__main__":
    main()

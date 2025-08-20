import requests
import base64

from src.graphics_db_server.logging import logger
from test_asset_retrieval import test_asset_search


def test_thumbnail_retrieval():
    """
    Tests getting asset thumbnails.
    """
    search_results = test_asset_search("a blue car")
    asset_uids = [asset["uid"] for asset in search_results]

    response = requests.post(
        "http://localhost:8000/api/v0/assets/thumbnails",
        json={"asset_uids": asset_uids},
    )
    logger.info(f"Asset UIDs: {asset_uids}. Response: {response}")
    assert response.status_code == 200
    response_json = response.json()
    assert len(response_json) > 0
    for uid, image_data in response_json.items():
        assert uid in asset_uids
        # Check if the image data is a valid base64 string
        assert base64.b64decode(image_data)


if __name__ == "__main__":
    test_thumbnail_retrieval()

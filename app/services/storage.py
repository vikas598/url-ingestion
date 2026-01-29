import json
import os
from app.core.exceptions import APIException

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "products")


def store_product(product_id: str, product_data: dict) -> str:
    try:
        os.makedirs(DATA_DIR, exist_ok=True)

        file_path = os.path.join(DATA_DIR, f"{product_id}.json")

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(product_data, f, ensure_ascii=False, indent=2)

        return file_path

    except Exception:
        raise APIException("STORAGE_FAILURE")

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import DATA_DIR

CUSTOMER_DATA_PATH = DATA_DIR / "mock_customers.json"


def load_customers() -> List[Dict[str, Any]]:
    if not CUSTOMER_DATA_PATH.exists():
        return []
    return json.loads(CUSTOMER_DATA_PATH.read_text(encoding="utf-8"))


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def find_customer_in_text(text: str, customers: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    normalized_text = _normalize(text)
    digits_only = "".join(character for character in text if character.isdigit())

    for customer in customers:
        if _normalize(customer["full_name"]) in normalized_text:
            return customer
        first_name = _normalize(customer["full_name"].split()[0])
        if first_name and (
            f"{first_name}'s" in normalized_text
            or f"{first_name}s" in normalized_text
            or normalized_text == first_name
            or f" {first_name} " in f" {normalized_text} "
        ):
            return customer
        if digits_only and customer["account_number"] in digits_only:
            return customer
    return None


def find_customer_from_history(history: List[Dict[str, str]], customers: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for item in reversed(history):
        if item.get("role") != "user":
            continue
        customer = find_customer_in_text(item.get("content", ""), customers)
        if customer:
            return customer
    return None

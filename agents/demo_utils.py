import os
import sys
from typing import Optional

import requests


DEFAULT_BASE_URL = os.getenv("FARAMESH_BASE_URL", "http://localhost:8000")
DEFAULT_TOKEN = os.getenv("FARAMESH_TOKEN") or os.getenv("FARAMESH_API_KEY")


def ensure_server_available(
    base_url: Optional[str] = None, timeout: float = 2.0
) -> bool:
    """Best-effort ping to ensure the Faramesh server is reachable.

    Returns True if the /health or root responds; False otherwise.
    """
    url = (base_url or DEFAULT_BASE_URL).rstrip("/")
    health_urls = [f"{url}/health", f"{url}/v1/health", url]
    headers = {}
    if DEFAULT_TOKEN:
        headers["Authorization"] = f"Bearer {DEFAULT_TOKEN}"

    for candidate in health_urls:
        try:
            resp = requests.get(candidate, headers=headers, timeout=timeout)
            if resp.ok:
                return True
        except Exception:
            continue
    print(
        f"⚠️  Faramesh server not reachable at {url}. Start it before running this demo."
    )
    print("   e.g., cd faramesh-horizon-code && python -m faramesh.server.main")
    return False


__all__ = ["ensure_server_available", "DEFAULT_BASE_URL", "DEFAULT_TOKEN"]

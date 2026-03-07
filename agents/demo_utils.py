import sys, os as _os
from pathlib import Path as _Path

# --- faramesh source resolution ---
# Priority: 1) installed package  2) PYTHONPATH env  3) sibling faramesh-core/src
def _add_faramesh_src():
    try:
        import faramesh  # already installed or on PYTHONPATH
        return
    except ImportError:
        pass
    # Look for a sibling faramesh-core clone
    _here = _Path(__file__).resolve().parent
    for _candidate in [
        _here.parent / "faramesh-core" / "src",
        _here.parent.parent / "faramesh-core" / "src",
        _Path.home() / "faramesh-core" / "src",
    ]:
        if (_candidate / "faramesh").is_dir():
            sys.path.insert(0, str(_candidate))
            return
    print("\n[faramesh] Could not find faramesh. Run:")
    print("  git clone https://github.com/faramesh/faramesh-core.git")
    print("  pip install -e ./faramesh-core  OR  export PYTHONPATH=./faramesh-core/src")
    sys.exit(1)

_add_faramesh_src()
# --- end faramesh source resolution ---

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
    print("   e.g., python -m faramesh.server.main  # or: faramesh serve")
    return False


__all__ = ["ensure_server_available", "DEFAULT_BASE_URL", "DEFAULT_TOKEN"]

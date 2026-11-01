"""Run the web app: python scripts/serve.py  ->  http://localhost:8000"""
from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

if __name__ == "__main__":
    import uvicorn

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    uvicorn.run("traffic_law.api.app:app", host="127.0.0.1", port=port, app_dir=str(SRC))

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("APP_API_KEY", "test-key")
os.environ.setdefault("APP_DB_HOST", "localhost")
os.environ.setdefault("APP_DB_PORT", "3306")
os.environ.setdefault("APP_DB_USER", "root")
os.environ.setdefault("APP_DB_PASSWORD", "root")
os.environ.setdefault("APP_DB_NAME", "mamutero")
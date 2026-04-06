import os
import sys
from pathlib import Path

# Many tests POST /analyze; keep suite stable without burning the default per-IP quota.
os.environ.setdefault("FAIRTERMS_RATE_LIMIT_ENABLED", "0")

sys.path.insert(0, str(Path(__file__).resolve().parent))

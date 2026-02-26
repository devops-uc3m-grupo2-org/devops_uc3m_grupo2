import sys
from pathlib import Path

# Ensure project root is in sys.path so 'app' package is importable during tests
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

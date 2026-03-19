"""
Vercel entrypoint for Lions Cred.
Maps the existing Flask app in app.py to Vercel's Python function.
"""
import sys
from pathlib import Path

# Ensure project root is on sys.path so we can import app.py
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from app import app as application  # Flask app defined in app.py

# Vercel expects a top-level variable named "app"
app = application

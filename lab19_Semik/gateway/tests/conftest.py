import os
import sys
from pathlib import Path

os.environ["SERVICE_AUTOSTART"] = "0"
SERVICE_DIR = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(SERVICE_DIR), str(SERVICE_DIR.parent)]

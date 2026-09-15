import sys
from pathlib import Path

# Make src/ importable from the tests, without needing a package install.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
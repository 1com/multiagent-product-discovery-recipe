"""Repository locations shared by every pipeline stage.

The project is installed in editable mode (`uv sync`), so paths resolve relative to the
repository checkout rather than to site-packages.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
NOTEBOOKS_DIR = REPO_ROOT / "notebooks"
OUTPUTS_DIR = REPO_ROOT / "outputs"
EDA_OUTPUT_DIR = OUTPUTS_DIR / "eda"
EDA_PROFILE_PATH = EDA_OUTPUT_DIR / "evidence_profile.json"

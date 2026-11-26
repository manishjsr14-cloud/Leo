"""Where checks keep their databases: the OS temporary folder, never leo_data/.

leo_data/ is Leo's real data folder. Checks run on fictional data in fresh
databases, so they live in <temp>/leo_evals/ (M2.3b fix round: the first
M2.3b check wrote to leo_data/evals/). A database stays there between
processes, so the M1.10 regression can start from the store a check left.
"""

import tempfile
from pathlib import Path

EVAL_DB_DIR = Path(tempfile.gettempdir()) / "leo_evals"

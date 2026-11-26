"""Checks keep their databases in the OS temporary folder, never in leo_data/ or the
project folder (M2.3b fix round: the first M2.3b check wrote to leo_data/evals/)."""

import tempfile
from pathlib import Path

from evals import eval_memory, m2_3b_memory_check
from evals.eval_paths import EVAL_DB_DIR
from leo.paths import PROJECT_ROOT


# The eval database folder is under the temp folder and outside the project.
def test_eval_databases_are_temporary():
    assert EVAL_DB_DIR.is_relative_to(Path(tempfile.gettempdir()))
    assert not EVAL_DB_DIR.resolve().is_relative_to(PROJECT_ROOT.resolve())


# Every check that makes a database uses that folder.
def test_checks_use_the_temporary_folder():
    assert m2_3b_memory_check.DB_DIR == EVAL_DB_DIR
    assert eval_memory.DB_DIR == EVAL_DB_DIR

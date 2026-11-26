"""Fakes for memory tests (M2.3): a table-driven embedding model and a temp memory bank.

The real Embedder wraps the fake model, so its prefixes and its per-message
cache are the real code; only the model is fake. The database is always a
temporary file, never leo_data/.
"""

import math

from leo.config import load_config
from leo.memory.memories import MemoryBank, open_bank
from leo.memory.store import open_db
from leo.ml.embedder import Embedder

DIM = 4


# A unit-length copy of a vector.
def unit(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vector))
    return [x / norm for x in vector]


class TableModel:
    """Stands in for SentenceTransformer: a text's vector comes from a table
    (e5 prefix removed; stored facts are keyed "<subject words>: <fact>"), else
    from its length and letters. Counts encoded texts."""

    def __init__(self, table: dict[str, list[float]] | None = None):
        self.table = {k: unit(v) for k, v in (table or {}).items()}
        self.encoded: list[str] = []

    def get_embedding_dimension(self) -> int:
        return DIM

    def encode(self, texts, **kwargs):
        self.encoded += list(texts)
        rows = []
        for text in texts:
            plain = text.split(": ", 1)[1] if text.startswith(("query: ", "passage: ")) else text
            seed = sum(map(ord, plain))
            rows.append(self.table.get(plain) or unit([1 + (seed * (i + 3)) % 11 for i in range(DIM)]))
        return rows


# A memory bank on a fresh database in tmp_path, with the real Embedder around
# a TableModel, and the memory settings from config.yaml (or `changes` to them).
def make_bank(tmp_path, table: dict | None = None, **changes) -> MemoryBank:
    config = load_config()
    embedder_cfg = config.embedder.model_copy(update={"dimension": DIM})
    memory_cfg = config.memory.model_copy(update=changes)
    embedder = Embedder(TableModel(table), embedder_cfg)
    return open_bank(open_db(tmp_path / "leo.db"), embedder, memory_cfg, DIM)

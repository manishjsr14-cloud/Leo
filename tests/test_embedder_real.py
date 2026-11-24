"""One test with the real e5 model. Skipped by default; run it with:

  python -m pytest -m real_model

The first run downloads the model into embedder.cache_dir (config.yaml).
"""

import math

import pytest

from leo.config import load_config
from leo.ml.embedder import load_embedder


# The real model loads on the CPU, gives normalized 384-dim vectors, and the
# e5 prefix changes the vector (so the prefix really reaches the model).
@pytest.mark.real_model
def test_real_model_vectors():
    cfg = load_config().embedder
    emb = load_embedder(cfg)
    assert str(emb.model.device) == "cpu"
    query = emb.embed_query("Kal shaam 5 baje meri meeting hai.")
    passage = emb.embed_passages(["Kal shaam 5 baje meri meeting hai."])[0]
    assert len(query) == cfg.dimension
    assert math.isclose(sum(x * x for x in query), 1.0, rel_tol=1e-4)
    assert query != passage

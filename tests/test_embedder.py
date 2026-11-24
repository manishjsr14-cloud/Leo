"""Tests for leo/ml/embedder.py with a fake model (the real model is never loaded here)."""

import math

import pytest
from pydantic import ValidationError

from leo.config import PROJECT_ROOT, EmbedderConfig, load_config
from leo.ml.embedder import Embedder, load_model

DIM = 4


# A stand-in for SentenceTransformer: records every encode call and returns
# a unit vector that depends on the text, so different texts differ.
class FakeModel:
    def __init__(self, dim: int = DIM):
        self.dim = dim
        self.calls: list[tuple[list[str], dict]] = []

    def get_embedding_dimension(self) -> int:
        return self.dim

    def encode(self, texts, **kwargs):
        self.calls.append((list(texts), kwargs))
        rows = []
        for t in texts:
            raw = [float(len(t) + i * (sum(map(ord, t)) % 7 + 1)) for i in range(self.dim)]
            norm = math.sqrt(sum(x * x for x in raw))
            rows.append([x / norm for x in raw])
        return rows


# The real config's embedder section, with a small cache for the cache tests.
def make_cfg(**changes) -> EmbedderConfig:
    base = load_config().embedder.model_dump()
    base.update({"dimension": DIM, **changes})
    return EmbedderConfig.model_validate(base)


# A query gets "query: " once; passages get "passage: " and keep their order.
def test_prefixes_are_applied():
    model = FakeModel()
    emb = Embedder(model, make_cfg())
    emb.embed_query("kal meeting hai")
    emb.embed_passages(["likes tea", "lives in Pune"])
    assert model.calls[0][0] == ["query: kal meeting hai"]
    assert model.calls[1][0] == ["passage: likes tea", "passage: lives in Pune"]


# Passage vectors come back in the order the texts were given.
def test_passage_order_is_kept():
    emb = Embedder(FakeModel(), make_cfg())
    a, b = emb.embed_passages(["likes tea", "lives in Pune"])
    assert [a, b] == [emb.embed_passages(["likes tea"])[0], emb.embed_passages(["lives in Pune"])[0]]


# The model is always asked for normalized vectors.
def test_vectors_are_normalized():
    model = FakeModel()
    vec = Embedder(model, make_cfg()).embed_query("hello")
    assert model.calls[0][1]["normalize_embeddings"] is True
    assert len(vec) == DIM and math.isclose(sum(x * x for x in vec), 1.0)


# The same message twice runs the model once and returns the same (immutable) vector.
def test_message_is_embedded_once():
    model = FakeModel()
    emb = Embedder(model, make_cfg())
    first = emb.embed_query("aaj ki news")
    second = emb.embed_query("aaj ki news")
    assert len(model.calls) == 1
    assert first is second and isinstance(first, tuple)


# A repeated text inside one batch is sent to the model once.
def test_duplicates_in_a_batch_are_embedded_once():
    model = FakeModel()
    out = Embedder(model, make_cfg()).embed_passages(["a fact", "a fact"])
    assert model.calls[0][0] == ["passage: a fact"]
    assert out[0] == out[1]


# The same text as a query and as a passage are two different cache entries.
def test_query_and_passage_are_cached_apart():
    model = FakeModel()
    emb = Embedder(model, make_cfg())
    emb.embed_query("likes tea")
    emb.embed_passages(["likes tea"])
    assert [c[0] for c in model.calls] == [["query: likes tea"], ["passage: likes tea"]]


# Over cache_size, the least recently used vector is dropped and recomputed later.
def test_cache_drops_the_oldest():
    model = FakeModel()
    emb = Embedder(model, make_cfg(cache_size=2))
    for text in ["one", "two", "three"]:
        emb.embed_query(text)
    emb.embed_query("three")  # still cached
    emb.embed_query("one")    # was dropped
    assert len(model.calls) == 4


# A batch bigger than the cache still returns every vector.
def test_batch_bigger_than_cache():
    out = Embedder(FakeModel(), make_cfg(cache_size=1)).embed_passages(["a", "b", "c"])
    assert len(out) == 3


# Empty text is refused instead of being embedded as a bare prefix.
def test_empty_text_is_refused():
    with pytest.raises(ValueError):
        Embedder(FakeModel(), make_cfg()).embed_query("  ")


# Loading asks for the CPU and the configured cache folder, offline first.
def test_load_is_cpu_and_offline_first():
    seen = []

    def loader(name, **kwargs):
        seen.append((name, kwargs))
        return FakeModel()

    cfg = make_cfg()
    load_model(cfg, loader)
    assert seen == [(cfg.model, {"local_files_only": True, "device": "cpu",
                                 "cache_folder": str(cfg.resolved_cache_dir())})]


# When the model is not cached yet, loading downloads it once.
def test_load_downloads_only_when_missing():
    seen = []

    def loader(name, **kwargs):
        seen.append(kwargs["local_files_only"])
        if kwargs["local_files_only"]:
            raise OSError("not cached")
        return FakeModel()

    load_model(make_cfg(), loader)
    assert seen == [True, False]


# A model whose vector size differs from config is refused.
def test_dimension_mismatch_is_refused():
    with pytest.raises(ValueError):
        load_model(make_cfg(), lambda name, **kw: FakeModel(dim=DIM + 1))


# Config: the real file is CPU, 384-dim e5-small, cache under the project folder.
def test_real_config_embedder_section():
    cfg = load_config().embedder
    assert cfg.model == "intfloat/multilingual-e5-small"
    assert (cfg.device, cfg.dimension) == ("cpu", 384)
    assert (cfg.query_prefix, cfg.passage_prefix) == ("query: ", "passage: ")
    assert cfg.resolved_cache_dir() == PROJECT_ROOT / "models" / "hf_cache"


# Config: any device other than the CPU is rejected (the GPU stays for Ollama).
def test_gpu_device_is_rejected():
    with pytest.raises(ValidationError):
        make_cfg(device="cuda")

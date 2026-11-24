"""The shared text embedder: intfloat/multilingual-e5-small on the CPU (section 8.1).

e5 models expect a prefix on every text:
  "query: "   the incoming message, and any comparison of two messages
  "passage: " stored texts that queries search (memories, documents)
The prefixes come from config.yaml and are added here, so callers never add them.

Vectors are normalized (length 1), so cosine similarity is a plain dot product.

Each message is embedded once: recent vectors are kept in a small cache keyed by
(prefix, text), and asking again returns the same vector without running the
model. Vectors are tuples, so a caller cannot change the cached copy.

The model is cached in embedder.cache_dir (config.yaml). Loading tries that
cache offline first and downloads from Hugging Face only when it is missing.
sentence_transformers (and torch) are imported only when the model is loaded,
so importing this file stays cheap.
"""

import threading
from collections import OrderedDict
from collections.abc import Callable, Sequence

from leo.config import EmbedderConfig

Vector = tuple[float, ...]


# Load the model on the configured device (always the CPU) from the cache folder.
# Offline first; only if the model is not cached yet is it downloaded once.
# `loader` is SentenceTransformer unless a test passes a fake.
def load_model(cfg: EmbedderConfig, loader: Callable | None = None):
    if loader is None:
        from sentence_transformers import SentenceTransformer
        loader = SentenceTransformer
    options = {"device": cfg.device, "cache_folder": str(cfg.resolved_cache_dir())}
    try:
        model = loader(cfg.model, local_files_only=True, **options)
    except OSError:  # not in the cache yet: download it this one time
        model = loader(cfg.model, local_files_only=False, **options)
    size = model.get_embedding_dimension()
    if size != cfg.dimension:
        raise ValueError(f"{cfg.model} gives {size}-dim vectors, config says {cfg.dimension}")
    return model


class Embedder:
    """A loaded model plus a small cache of recent vectors, safe to share between threads."""

    # Keep the model and settings; the cache starts empty.
    def __init__(self, model, cfg: EmbedderConfig):
        self.model = model
        self.cfg = cfg
        self._cache: OrderedDict[tuple[str, str], Vector] = OrderedDict()
        self._lock = threading.Lock()

    # The vector of one incoming message (or one side of a message-to-message comparison).
    def embed_query(self, text: str) -> Vector:
        return self._embed_many(self.cfg.query_prefix, [text])[0]

    # Vectors for stored texts (memories, documents), in the same order as `texts`.
    def embed_passages(self, texts: Sequence[str]) -> list[Vector]:
        return self._embed_many(self.cfg.passage_prefix, list(texts))

    # Embed texts with one prefix: cached ones are reused, the rest go to the
    # model in one batch and are added to the cache.
    def _embed_many(self, prefix: str, texts: list[str]) -> list[Vector]:
        if any(not t.strip() for t in texts):
            raise ValueError("cannot embed empty text")
        with self._lock:
            found = {t: self._lookup((prefix, t)) for t in texts if (prefix, t) in self._cache}
        missing = [t for t in dict.fromkeys(texts) if t not in found]
        if missing:
            rows = self.model.encode([prefix + t for t in missing], normalize_embeddings=True)
            new = {t: tuple(float(x) for x in row) for t, row in zip(missing, rows, strict=True)}
            with self._lock:
                for text, vector in new.items():
                    self._remember((prefix, text), vector)
            found.update(new)
        return [found[t] for t in texts]

    # Add one vector, dropping the oldest when the cache is full. Lock held by caller.
    def _remember(self, key: tuple[str, str], vector: Vector) -> None:
        self._cache[key] = vector
        self._cache.move_to_end(key)
        while len(self._cache) > self.cfg.cache_size:
            self._cache.popitem(last=False)

    # Read one vector and mark it as recently used. Lock held by caller.
    def _lookup(self, key: tuple[str, str]) -> Vector:
        self._cache.move_to_end(key)
        return self._cache[key]


# Load the model from config and wrap it in an Embedder.
def load_embedder(cfg: EmbedderConfig) -> Embedder:
    return Embedder(load_model(cfg), cfg)

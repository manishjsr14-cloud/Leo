"""Tests for leo/memory/sqlite_vec.py (M2.1), always on a temporary database.

Vectors are random with a fixed seed, so every run uses the same data.
"""

import math
import random

import pytest

from leo.memory.sqlite_vec import SqliteVecStore
from leo.memory.store import VectorStore, open_db

DIM = 384          # the size multilingual-e5-small will use (section 7)
SEED = 2026        # fixed: never change it to make a test pass
TIE = 1e-5         # distances closer than this may come back in either order


# A list of `count` random vectors of size DIM from one seeded generator.
def _vectors(count: int, rng: random.Random) -> list[list[float]]:
    return [[rng.gauss(0.0, 1.0) for _ in range(DIM)] for _ in range(count)]


# Cosine distance (1 - cosine similarity) in plain Python, for the brute-force check.
def _cosine_distance(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return 1.0 - dot / norm


# A store on a fresh database file in tmp_path.
def _store(tmp_path, table: str = "vec_test") -> SqliteVecStore:
    return SqliteVecStore(open_db(tmp_path / "leo.db"), table, DIM)


# Done-when check: 1,000 vectors in, 20 searches out; each top 5 matches a
# brute-force cosine top 5. Position by position, the brute-force distance
# of the returned id must equal the brute-force distance at that rank
# (within TIE), so near-ties may swap places but a wrong id fails.
def test_thousand_vectors_match_brute_force(tmp_path):
    rng = random.Random(SEED)
    stored = _vectors(1000, rng)
    queries = _vectors(20, rng)
    store = _store(tmp_path)
    store.add(list(range(1, 1001)), stored)
    for query in queries:
        exact = {i + 1: _cosine_distance(query, v) for i, v in enumerate(stored)}
        ranked = sorted(exact.values())[:5]
        found = store.search(query, 5)
        ids = [i for i, _ in found]
        assert len(ids) == 5 and len(set(ids)) == 5
        for rank, (found_id, found_distance) in enumerate(found):
            assert abs(exact[found_id] - ranked[rank]) < TIE
            assert abs(found_distance - exact[found_id]) < TIE


# A slightly changed copy of stored vector 417 finds 417 first.
def test_near_copy_finds_its_original(tmp_path):
    rng = random.Random(SEED)
    stored = _vectors(1000, rng)
    store = _store(tmp_path)
    store.add(list(range(1, 1001)), stored)
    query = [x + rng.gauss(0.0, 0.05) for x in stored[416]]
    assert store.search(query, 3)[0][0] == 417


# Results come back nearest first, and k limits how many.
def test_results_sorted_and_limited_by_k(tmp_path):
    rng = random.Random(SEED)
    store = _store(tmp_path)
    store.add(list(range(1, 51)), _vectors(50, rng))
    found = store.search(_vectors(1, rng)[0], 7)
    distances = [d for _, d in found]
    assert len(found) == 7
    assert distances == sorted(distances)


# Vectors are still there after the file is closed and opened again.
def test_vectors_survive_reopen(tmp_path):
    rng = random.Random(SEED)
    stored = _vectors(10, rng)
    store = _store(tmp_path)
    store.add(list(range(1, 11)), stored)
    store.conn.close()
    again = _store(tmp_path)
    assert again.search(stored[3], 1)[0][0] == 4


# A vector of the wrong size is refused on add and on search, and a
# refused add stores nothing.
def test_wrong_dimension_is_refused(tmp_path):
    store = _store(tmp_path)
    with pytest.raises(ValueError):
        store.add([1, 2], [[0.1] * DIM, [0.1] * (DIM - 1)])
    with pytest.raises(ValueError):
        store.search([0.1] * (DIM + 1), 1)
    assert store.conn.execute("SELECT count(*) FROM vec_test").fetchone()[0] == 0


# Table names that are not plain vec_ names are refused before any SQL runs.
@pytest.mark.parametrize("name", ["x; DROP TABLE tasks", "memories", "vec_1", "VEC_A", ""])
def test_bad_table_name_is_refused(tmp_path, name):
    conn = open_db(tmp_path / "leo.db")
    with pytest.raises(ValueError):
        SqliteVecStore(conn, name, DIM)


# Mismatched id and vector counts, and k below 1, are refused.
def test_bad_arguments_are_refused(tmp_path):
    store = _store(tmp_path)
    with pytest.raises(ValueError):
        store.add([1, 2], [[0.1] * DIM])
    with pytest.raises(ValueError):
        store.search([0.1] * DIM, 0)


# SqliteVecStore has the methods the VectorStore interface asks for.
def test_sqlite_store_is_a_vector_store(tmp_path):
    assert isinstance(_store(tmp_path), VectorStore)

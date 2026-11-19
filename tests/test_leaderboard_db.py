import os
import tempfile
from pathlib import Path

from leaderboard_db import add_entry, rank_of, top_entries


def _temp_db_path() -> Path:
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return Path(path)


def test_add_entry_and_top_entries_round_trip():
    db_path = _temp_db_path()
    try:
        entry_id = add_entry("Bubbly Crab", "Patrick", 22, db_path=db_path)
        assert isinstance(entry_id, int)
        entries = top_entries(10, db_path=db_path)
        assert len(entries) == 1
        assert entries[0].name == "Bubbly Crab"
        assert entries[0].habitat == "Patrick"
        assert entries[0].score == 22
    finally:
        db_path.unlink(missing_ok=True)


def test_top_entries_sorted_descending_by_score():
    db_path = _temp_db_path()
    try:
        add_entry("A", "Patrick", 10, db_path=db_path)
        add_entry("B", "Patrick", 30, db_path=db_path)
        add_entry("C", "Patrick", 20, db_path=db_path)
        entries = top_entries(10, db_path=db_path)
        assert [e.score for e in entries] == [30, 20, 10]
    finally:
        db_path.unlink(missing_ok=True)


def test_top_entries_respects_limit():
    db_path = _temp_db_path()
    try:
        for i in range(5):
            add_entry(f"P{i}", "Patrick", i, db_path=db_path)
        assert len(top_entries(2, db_path=db_path)) == 2
    finally:
        db_path.unlink(missing_ok=True)


def test_rank_of_gives_tied_scores_the_same_rank():
    db_path = _temp_db_path()
    try:
        id_a = add_entry("A", "Patrick", 30, db_path=db_path)
        id_b = add_entry("B", "Patrick", 20, db_path=db_path)
        id_c = add_entry("C", "Patrick", 20, db_path=db_path)  # ties with B
        id_d = add_entry("D", "Patrick", 10, db_path=db_path)
        assert rank_of(id_a, db_path=db_path) == 1
        assert rank_of(id_b, db_path=db_path) == 2
        assert rank_of(id_c, db_path=db_path) == 2
        assert rank_of(id_d, db_path=db_path) == 4
    finally:
        db_path.unlink(missing_ok=True)


if __name__ == "__main__":
    test_add_entry_and_top_entries_round_trip()
    test_top_entries_sorted_descending_by_score()
    test_top_entries_respects_limit()
    test_rank_of_gives_tied_scores_the_same_rank()
    print("OK")

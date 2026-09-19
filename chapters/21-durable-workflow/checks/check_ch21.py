import sqlite3

import pytest
from exercise_support import load_target

target = load_target(__file__)


def test_retry_and_conflict(tmp_path):
    db = str(tmp_path / "deliveries.sqlite")
    assert target.publish_once(db, "r1", "body") == "published:r1"
    assert target.publish_once(db, "r1", "body") == "published:r1"
    with pytest.raises(ValueError):
        target.publish_once(db, "r1", "changed")
    connection = sqlite3.connect(db)
    try:
        assert connection.execute("SELECT * FROM deliveries").fetchall() == [("r1", "body")]
    finally:
        connection.close()


def test_different_requests_and_invalid_input(tmp_path):
    db = str(tmp_path / "deliveries.sqlite")
    assert target.publish_once(db, "r1", "a") != target.publish_once(db, "r2", "b")
    with pytest.raises(ValueError):
        target.publish_once(db, "", "a")

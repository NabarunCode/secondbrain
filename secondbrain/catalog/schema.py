# secondbrain/catalog/schema.py
#
# Applies schema.sql to a database connection. Every statement in that file
# is CREATE ... IF NOT EXISTS, so this is safe to call every time the app
# starts, whether data/secondbrain.db is brand new or already exists.
#
# No version number, no migrations table, no runner. See schema.sql header
# and docs/decisions.md (2026-07-03) for why.

import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_PATH.read_text())
    conn.commit()

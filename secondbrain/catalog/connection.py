# secondbrain/catalog/connection.py
#
# Owns how the rest of the application talks to the SQLite catalog file.
# No other module should call sqlite3.connect() directly — every connection
# must go through get_connection() so the required PRAGMAs are always applied.
# (See docs/phase1b_catalog_architecture.md §6 "Persistence Strategy".)

import sqlite3
from pathlib import Path

DB_PATH = Path("data/secondbrain.db")


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """
    Open a SQLite connection configured for this project.

    Ensures the database's parent directory exists, sets row_factory so
    query results are accessible by column name, and applies the two
    connection-level PRAGMAs this project relies on (WAL journaling,
    foreign key enforcement). See docs/phase1b_catalog_architecture.md §6.
    """
    # Make sure the parent directory exists — sqlite3.connect() creates the
    # .db file itself automatically, but never creates missing directories.
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Connections here are short-lived: created, used, and discarded within
    # a single operation, in the same thread that opened them — never
    # handed off to a different thread. That's exactly the case the default
    # check_same_thread=True guards correctly, so no override is needed.
    # (If we ever switched to one long-lived shared connection, this
    # reasoning would need to be revisited.)
    conn = sqlite3.connect(db_path)

    # Rows come back as sqlite3.Row objects: accessible by column name
    # (row["filename"]) as well as by position, instead of plain tuples.
    conn.row_factory = sqlite3.Row

    # journal_mode is a property of the file itself, so this only truly
    # needs to run once ever per file — but it's harmless and cheap to set
    # on every connection, so we do it here for simplicity.
    conn.execute("PRAGMA journal_mode=WAL;")

    # foreign_keys is a per-connection setting that resets every time —
    # this one genuinely must run on every single connection, no exceptions.
    conn.execute("PRAGMA foreign_keys=ON;")

    return conn
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

    TODO 1:
        Make sure the parent directory of db_path exists before connecting.
        sqlite3.connect() will NOT create missing directories for you — it
        will raise if "data/" doesn't exist yet. (Hint: Path has a method
        for exactly this.)

    TODO 2:
        Open the connection with sqlite3.connect(db_path).
        Think about this before you write it: we decided in the architecture
        doc that connections are "short-lived, opened per operation" rather
        than one long-lived global connection. Given that, do you think you
        need the check_same_thread=False argument here, or not? Write down
        your reasoning as a comment above this line — we'll check it
        together.

    TODO 3:
        Set conn.row_factory = sqlite3.Row.
        This makes rows come back as dict-like objects (row["filename"])
        instead of plain tuples (row[3]) — the repository layer we build
        next relies on this.

    TODO 4:
        Run the two PRAGMAs we just discussed, using conn.execute(...):
          - PRAGMA journal_mode=WAL;
          - PRAGMA foreign_keys=ON;

    TODO 5:
        Return the connection.
    """
    raise NotImplementedError

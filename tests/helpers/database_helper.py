from __future__ import annotations

import os
import gc
import shutil
import sqlite3
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable


class DatabaseHelper:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.temp_dir: Path | None = None
        self.previous_cwd: str | None = None

    def __enter__(self) -> "DatabaseHelper":
        if str(self.repo_root) not in sys.path:
            sys.path.insert(0, str(self.repo_root))

        self.temp_dir = Path(tempfile.mkdtemp(prefix="uth_portal_test_"))
        self.previous_cwd = os.getcwd()
        os.chdir(self.temp_dir)

        from core import initialize_database
        from tests.fixtures.import_seed_data import import_seed_data

        initialize_database()
        import_seed_data(self.db_path)
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self.previous_cwd:
            os.chdir(self.previous_cwd)
        if self.temp_dir and self.temp_dir.exists():
            for attempt in range(5):
                try:
                    gc.collect()
                    shutil.rmtree(self.temp_dir)
                    break
                except PermissionError:
                    if attempt == 4:
                        shutil.rmtree(self.temp_dir, ignore_errors=True)
                    else:
                        time.sleep(0.1)

    @property
    def db_path(self) -> Path:
        if self.temp_dir is None:
            raise RuntimeError("DatabaseHelper must be used as a context manager.")
        return self.temp_dir / "uth_portal_final.db"

    def query(self, sql: str, params: Iterable[Any] = ()) -> list[sqlite3.Row]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.cursor()
            cur.execute(sql, tuple(params))
            return cur.fetchall()
        finally:
            conn.close()

    def execute(self, sql: str, params: Iterable[Any] = ()) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            cur.execute(sql, tuple(params))
            conn.commit()
        finally:
            conn.close()

    def scalar(self, sql: str, params: Iterable[Any] = ()) -> Any:
        rows = self.query(sql, params)
        return rows[0][0] if rows else None

from __future__ import annotations

import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "uth_portal_final.db"


def initialize_schema() -> None:
    sys.path.insert(0, str(REPO_ROOT))
    from core import initialize_database

    previous_cwd = Path.cwd()
    try:
        os.chdir(REPO_ROOT)
        initialize_database()
    finally:
        os.chdir(previous_cwd)


def main() -> int:
    sys.path.insert(0, str(REPO_ROOT))
    from tests.fixtures.import_seed_data import import_seed_data, table_counts

    with_scenarios = "--with-scenarios" in sys.argv
    initialize_schema()
    import_seed_data(DB_PATH, with_scenarios=with_scenarios)

    print(f"Database seeded from JSON: {DB_PATH}")
    for table, count in table_counts(DB_PATH).items():
        print(f"{table}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

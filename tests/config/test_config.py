from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def load_env_file() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env.test"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env_file()


@dataclass(frozen=True)
class TestConfig:
    environment: str = os.getenv("TEST_ENVIRONMENT", "local")
    database_file: str = os.getenv("TEST_DATABASE_FILE", "uth_portal_final.db")
    allow_non_test_environment: bool = False

    def assert_safe(self) -> None:
        if self.environment.lower() not in {"local", "test"} and not self.allow_non_test_environment:
            raise RuntimeError(
                "Refusing to run tests outside local/test environment. "
                "Set TEST_ENVIRONMENT=local or pass --allow-non-test-environment."
            )

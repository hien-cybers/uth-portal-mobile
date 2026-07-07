from __future__ import annotations

import time
import uuid


class TestDataFactory:
    @staticmethod
    def suffix() -> str:
        return f"{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"

    @staticmethod
    def student_id(prefix: str = "AUT") -> str:
        return f"{prefix}{uuid.uuid4().hex[:8].upper()}"

    @staticmethod
    def student_name() -> str:
        return f"Automation Student {TestDataFactory.suffix()}"

    @staticmethod
    def major() -> str:
        return "Automation Major"

    @staticmethod
    def subject_id() -> str:
        return f"SUB{uuid.uuid4().hex[:6].upper()}"

    @staticmethod
    def class_id(subject_id: str) -> str:
        return f"{subject_id}-A"

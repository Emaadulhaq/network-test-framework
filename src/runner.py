"""
src/runner.py
Base test infrastructure: result dataclasses, base test class, and the
TestSuite orchestrator that runs everything and collects results.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
import time


# ── Result model ────────────────────────────────────────────────────────────

@dataclass
class TestResult:
    test_name:   str
    category:    str          # ping | http | dns | port
    target:      str
    status:      str          # PASS | FAIL | ERROR
    message:     str
    duration_ms: float
    timestamp:   str = field(default_factory=lambda: datetime.now().isoformat())
    details:     dict = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.status == "PASS"


@dataclass
class SuiteResult:
    suite_name:  str
    started_at:  str
    finished_at: str = ""
    results:     List[TestResult] = field(default_factory=list)

    @property
    def total(self):    return len(self.results)
    @property
    def passed(self):   return sum(1 for r in self.results if r.passed)
    @property
    def failed(self):   return self.total - self.passed
    @property
    def pass_rate(self):
        return round(self.passed / self.total * 100, 1) if self.total else 0.0

    def by_category(self) -> dict:
        cats = {}
        for r in self.results:
            cats.setdefault(r.category, []).append(r)
        return cats


# ── Base test class ──────────────────────────────────────────────────────────

class BaseTest:
    """All test classes inherit from this. Wraps execution with timing."""

    category = "base"

    def run_test(self, test_name: str, target: str, fn, **kwargs) -> TestResult:
        start = time.perf_counter()
        try:
            status, message, details = fn(**kwargs)
        except Exception as exc:
            status, message, details = "ERROR", f"Unhandled exception: {exc}", {}
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        result = TestResult(
            test_name=test_name,
            category=self.category,
            target=target,
            status=status,
            message=message,
            duration_ms=duration_ms,
            details=details,
        )
        icon = "✓" if result.passed else "✗"
        print(f"  [{icon}] {test_name:<40} {status:<6} {duration_ms:>7.1f}ms  {message}")
        return result


# ── Suite orchestrator ───────────────────────────────────────────────────────

class TestSuite:
    def __init__(self, name: str):
        self.name    = name
        self.testers = []       # list of (tester_instance, args_list)
        self._suite  = SuiteResult(
            suite_name=name,
            started_at=datetime.now().isoformat()
        )

    def register(self, tester, args_list: list):
        """Register a test class instance and the list of argument dicts to run."""
        self.testers.append((tester, args_list))

    def run(self) -> SuiteResult:
        print(f"\n{'='*60}")
        print(f"  {self.name}")
        print(f"  Started: {self._suite.started_at}")
        print(f"{'='*60}")

        for tester, args_list in self.testers:
            print(f"\n── {tester.category.upper()} TESTS ──")
            for kwargs in args_list:
                result = tester.execute(**kwargs)
                self._suite.results.append(result)

        self._suite.finished_at = datetime.now().isoformat()
        self._print_summary()
        return self._suite

    def _print_summary(self):
        s = self._suite
        print(f"\n{'='*60}")
        print(f"  SUMMARY: {s.passed}/{s.total} passed  ({s.pass_rate}%)")
        for cat, results in s.by_category().items():
            p = sum(1 for r in results if r.passed)
            print(f"    {cat:<12} {p}/{len(results)}")
        print(f"{'='*60}\n")

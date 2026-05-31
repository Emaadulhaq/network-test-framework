"""
main.py
Entry point. Loads config/targets.yaml, builds the test suite,
runs all tests, and generates the HTML report.

Usage:
    python main.py
    python main.py --config config/targets.yaml
    python main.py --no-ping          (skip ICMP if blocked by firewall)
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(__file__))

try:
    import yaml
    def load_config(path):
        with open(path) as f:
            return yaml.safe_load(f)
except ImportError:
    import json, re
    def load_config(path):
        # Minimal YAML → dict fallback using json (works for simple configs)
        raise SystemExit("PyYAML not installed. Run:  pip install pyyaml")


from src.runner             import TestSuite
from src.tests.ping_tests   import PingTester
from src.tests.http_tests   import HttpTester, SslTester
from src.tests.dns_tests    import DnsTester
from src.tests.port_tests   import PortTester
from src.report             import generate_html_report


def build_suite(cfg: dict, skip_ping: bool = False) -> TestSuite:
    suite = TestSuite("Automated Network System Test Framework")

    # ── Ping tests ──────────────────────────────────────────────────────
    if not skip_ping:
        suite.register(
            PingTester(),
            cfg.get("hosts", [])
        )

    # ── DNS tests ───────────────────────────────────────────────────────
    suite.register(
        DnsTester(),
        cfg.get("dns_lookups", [])
    )

    # ── Port tests ──────────────────────────────────────────────────────
    suite.register(
        PortTester(),
        cfg.get("port_checks", [])
    )

    # ── HTTP tests ──────────────────────────────────────────────────────
    suite.register(
        HttpTester(),
        cfg.get("http_endpoints", [])
    )

    # ── SSL tests (auto-generated from HTTPS endpoints) ──────────────────
    ssl_targets = [
        {"name": ep["name"], "hostname": ep["url"].split("/")[2]}
        for ep in cfg.get("http_endpoints", [])
        if ep["url"].startswith("https://")
    ]
    suite.register(SslTester(), ssl_targets)

    return suite


def main():
    parser = argparse.ArgumentParser(description="Network Test Framework")
    parser.add_argument("--config",    default="config/targets.yaml")
    parser.add_argument("--no-ping",   action="store_true",
                        help="Skip ICMP ping tests (useful if ICMP is blocked)")
    parser.add_argument("--out",       default="reports",
                        help="Directory for HTML report output")
    args = parser.parse_args()

    cfg   = load_config(args.config)
    suite = build_suite(cfg, skip_ping=args.no_ping)
    result = suite.run()

    report_path = generate_html_report(result, out_dir=args.out)
    print(f"\nOpen the report:  {report_path}")


if __name__ == "__main__":
    main()

"""
src/tests/dns_tests.py
DNS resolution validation:
- Forward lookup (hostname → IP)
- Expected failure detection
- Resolution latency measurement
- Multi-record reporting
"""

import socket
import time
from src.runner import BaseTest


class DnsTester(BaseTest):
    category = "dns"

    def execute(self, name: str, hostname: str,
                expect_failure: bool = False) -> object:

        def _run():
            try:
                t0      = time.perf_counter()
                results = socket.getaddrinfo(hostname, None)
                elapsed = round((time.perf_counter() - t0) * 1000, 2)

                # Deduplicate IPs
                ips = list({r[4][0] for r in results})
                ipv4 = [ip for ip in ips if ":" not in ip]
                ipv6 = [ip for ip in ips if ":" in ip]

                details = {
                    "resolved_ips": ips,
                    "ipv4": ipv4,
                    "ipv6": ipv6,
                    "record_count": len(ips),
                    "resolution_ms": elapsed,
                }

                if expect_failure:
                    return (
                        "FAIL",
                        f"Expected DNS failure but resolved to {ips[0]}",
                        details
                    )
                return (
                    "PASS",
                    f"Resolved → {ipv4[0] if ipv4 else ips[0]} in {elapsed}ms "
                    f"({len(ips)} record{'s' if len(ips)>1 else ''})",
                    details
                )

            except socket.gaierror as e:
                details = {"error": str(e)}
                if expect_failure:
                    return ("PASS", f"Expected DNS failure confirmed ({e.args[0]})", details)
                return ("FAIL", f"DNS resolution failed: {e}", details)

            except Exception as e:
                return ("ERROR", str(e), {})

        return self.run_test(
            test_name=f"DNS {name}",
            target=hostname,
            fn=_run
        )

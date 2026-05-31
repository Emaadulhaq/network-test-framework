"""
src/tests/port_tests.py
TCP port reachability checks:
- Confirms port open/closed as expected
- Measures connection latency
- Detects unexpected open/closed states as failures
"""

import socket
import time
from src.runner import BaseTest

# Well-known port → service name mapping
PORT_NAMES = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
    53: "DNS", 80: "HTTP", 110: "POP3", 143: "IMAP",
    443: "HTTPS", 445: "SMB", 3306: "MySQL", 3389: "RDP",
    5432: "PostgreSQL", 6379: "Redis", 8080: "HTTP-Alt",
    8443: "HTTPS-Alt", 27017: "MongoDB",
}


class PortTester(BaseTest):
    category = "port"

    def execute(self, name: str, host: str, port: int,
                expect_open: bool = True, timeout: int = 3) -> object:

        service = PORT_NAMES.get(port, f"port/{port}")

        def _run():
            try:
                t0 = time.perf_counter()
                with socket.create_connection((host, port), timeout=timeout):
                    elapsed = round((time.perf_counter() - t0) * 1000, 2)

                # Port is open
                details = {
                    "host": host, "port": port,
                    "service": service,
                    "state": "open",
                    "connect_ms": elapsed,
                    "expected_open": expect_open,
                }
                if expect_open:
                    return ("PASS", f"{service} open on :{port} ({elapsed}ms)", details)
                else:
                    return ("FAIL", f"{service} on :{port} is open but expected closed", details)

            except (ConnectionRefusedError, socket.timeout, OSError):
                # Port is closed / filtered
                details = {
                    "host": host, "port": port,
                    "service": service,
                    "state": "closed",
                    "expected_open": expect_open,
                }
                if not expect_open:
                    return ("PASS", f":{port} correctly closed/filtered", details)
                else:
                    return ("FAIL", f"{service} on :{port} is unreachable", details)

            except Exception as e:
                return ("ERROR", str(e), {})

        return self.run_test(
            test_name=f"Port {name} (:{port})",
            target=f"{host}:{port}",
            fn=_run
        )

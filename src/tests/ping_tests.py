"""
src/tests/ping_tests.py
ICMP ping connectivity checks using subprocess.
Works on Linux and macOS; falls back to TCP connect on Windows.
"""

import subprocess
import platform
import socket
import time
from src.runner import BaseTest


class PingTester(BaseTest):
    category = "ping"

    def execute(self, name: str, address: str, description: str = "",
                count: int = 4, timeout: int = 5) -> object:

        def _run():
            system = platform.system().lower()

            if system == "windows":
                cmd = ["ping", "-n", str(count), "-w", str(timeout * 1000), address]
            else:
                cmd = ["ping", "-c", str(count), "-W", str(timeout), address]

            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout * count + 5
                )
                output = proc.stdout + proc.stderr

                if proc.returncode == 0:
                    # Parse packet loss and round-trip time
                    loss_pct  = _parse_loss(output)
                    avg_rtt   = _parse_rtt(output)
                    return (
                        "PASS",
                        f"Reachable — {loss_pct}% packet loss, avg RTT {avg_rtt}ms",
                        {"packet_loss_pct": loss_pct, "avg_rtt_ms": avg_rtt,
                         "packets_sent": count, "raw": output[:400]}
                    )
                else:
                    return ("FAIL", f"Host unreachable (exit {proc.returncode})",
                            {"raw": output[:400]})

            except subprocess.TimeoutExpired:
                return ("FAIL", f"Ping timed out after {timeout}s", {})
            except FileNotFoundError:
                # ping not available — fall back to TCP socket connect
                return _tcp_fallback(address)

        return self.run_test(
            test_name=f"Ping {name} ({address})",
            target=address,
            fn=_run
        )


def _parse_loss(output: str) -> float:
    import re
    m = re.search(r'(\d+(?:\.\d+)?)%\s*packet loss', output)
    return float(m.group(1)) if m else -1.0


def _parse_rtt(output: str) -> float:
    import re
    # Linux: rtt min/avg/max/mdev = 1.2/3.4/5.6/0.8 ms
    m = re.search(r'(?:avg|rtt)[^=]+=\s*[\d.]+/([\d.]+)/', output)
    if m:
        return float(m.group(1))
    # macOS / Windows alternate format
    m = re.search(r'Average\s*=\s*([\d.]+)ms', output)
    return float(m.group(1)) if m else -1.0


def _tcp_fallback(address: str, port: int = 80, timeout: int = 3):
    """TCP connect as a ping substitute when ICMP is unavailable."""
    try:
        start = time.perf_counter()
        with socket.create_connection((address, port), timeout=timeout):
            rtt = round((time.perf_counter() - start) * 1000, 2)
        return ("PASS", f"TCP reachable on port {port}, RTT {rtt}ms",
                {"method": "tcp_fallback", "port": port, "rtt_ms": rtt})
    except Exception as e:
        return ("FAIL", f"TCP connect failed: {e}", {"method": "tcp_fallback"})

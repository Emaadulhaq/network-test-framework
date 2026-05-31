"""
src/tests/http_tests.py
HTTP/HTTPS endpoint validation:
- Status code assertion
- Response time measurement
- SSL/TLS certificate check
- Redirect chain tracking
"""

import urllib.request
import urllib.error
import ssl
import socket
import time
from src.runner import BaseTest


class HttpTester(BaseTest):
    category = "http"

    def execute(self, name: str, url: str,
                expected_status: int = 200, timeout_s: int = 5) -> object:

        def _run():
            ctx = ssl.create_default_context()
            opener = urllib.request.build_opener(
                urllib.request.HTTPRedirectHandler()
            )

            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "NetworkTestFramework/1.0"}
                )
                t0       = time.perf_counter()
                response = opener.open(req, timeout=timeout_s)
                elapsed  = round((time.perf_counter() - t0) * 1000, 2)

                actual_status = response.status
                content_type  = response.headers.get("Content-Type", "unknown")
                content_len   = response.headers.get("Content-Length", "unknown")
                final_url     = response.url

                # Read a small chunk to confirm data flows
                body_preview  = response.read(256)

                details = {
                    "status_code":   actual_status,
                    "expected":      expected_status,
                    "response_ms":   elapsed,
                    "content_type":  content_type,
                    "content_length": content_len,
                    "final_url":     final_url,
                    "redirected":    final_url != url,
                }

                if actual_status == expected_status:
                    return (
                        "PASS",
                        f"HTTP {actual_status} in {elapsed}ms",
                        details
                    )
                else:
                    return (
                        "FAIL",
                        f"Expected HTTP {expected_status}, got {actual_status}",
                        details
                    )

            except urllib.error.HTTPError as e:
                # HTTPError is still a valid HTTP response
                actual = e.code
                elapsed = 0
                details = {"status_code": actual, "expected": expected_status}
                if actual == expected_status:
                    return ("PASS", f"HTTP {actual} (expected)", details)
                return ("FAIL", f"HTTP {actual} — expected {expected_status}", details)

            except urllib.error.URLError as e:
                return ("ERROR", f"URL error: {e.reason}", {})
            except socket.timeout:
                return ("FAIL", f"Timed out after {timeout_s}s", {})
            except Exception as e:
                return ("ERROR", str(e), {})

        return self.run_test(
            test_name=f"HTTP {name}",
            target=url,
            fn=_run
        )


class SslTester(BaseTest):
    """Checks SSL certificate validity and expiry."""
    category = "http"

    def execute(self, name: str, hostname: str, port: int = 443) -> object:

        def _run():
            import datetime
            ctx = ssl.create_default_context()
            try:
                with socket.create_connection((hostname, port), timeout=5) as sock:
                    with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                        cert    = ssock.getpeercert()
                        version = ssock.version()

                not_after_str = cert.get("notAfter", "")
                # Format: 'Dec 31 23:59:59 2025 GMT'
                try:
                    not_after = datetime.datetime.strptime(
                        not_after_str, "%b %d %H:%M:%S %Y %Z"
                    )
                    days_left = (not_after - datetime.datetime.utcnow()).days
                except Exception:
                    days_left = -1

                subject = dict(x[0] for x in cert.get("subject", []))
                issuer  = dict(x[0] for x in cert.get("issuer",  []))

                details = {
                    "tls_version":  version,
                    "common_name":  subject.get("commonName", "unknown"),
                    "issuer":       issuer.get("organizationName", "unknown"),
                    "expires":      not_after_str,
                    "days_until_expiry": days_left,
                }

                if days_left < 0:
                    return ("ERROR", "Could not parse cert expiry", details)
                elif days_left < 14:
                    return ("FAIL", f"Certificate expires in {days_left} days!", details)
                else:
                    return ("PASS", f"Valid TLS ({version}), expires in {days_left} days",
                            details)

            except ssl.SSLError as e:
                return ("FAIL", f"SSL error: {e}", {})
            except Exception as e:
                return ("ERROR", str(e), {})

        return self.run_test(
            test_name=f"SSL {name} ({hostname})",
            target=hostname,
            fn=_run
        )

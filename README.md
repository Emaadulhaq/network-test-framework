# Automated Network System Test Framework

A Python-based automation framework that simulates and validates system-level network communication scenarios — covering connectivity, DNS resolution, port reachability, HTTP endpoint validation, and TLS certificate integrity.

Outputs a self-contained **HTML report** you can open in any browser.

---

## What it tests

| Layer | Tests |
|---|---|
| **Connectivity (ICMP)** | Ping hosts, measure RTT, detect packet loss |
| **DNS** | Forward resolution, expected failure detection, latency |
| **TCP Ports** | Confirm ports open/closed as expected (SSH, HTTP, HTTPS, custom) |
| **HTTP/HTTPS** | Status code assertion, response time, redirect tracking |
| **TLS/SSL** | Certificate validity, TLS version, days until expiry |

---

## Project structure

```
network-test-framework/
├── main.py                      # Entry point — run this
├── requirements.txt
├── config/
│   └── targets.yaml             # Define your test targets here
├── src/
│   ├── runner.py                # TestResult model, BaseTest, TestSuite orchestrator
│   ├── report.py                # HTML report generator
│   └── tests/
│       ├── ping_tests.py        # ICMP connectivity checks
│       ├── http_tests.py        # HTTP + SSL validation
│       ├── dns_tests.py         # DNS resolution tests
│       └── port_tests.py        # TCP port checks
└── reports/
    └── test_report.html         # Generated after each run
```

---

## Quickstart

```bash
git clone https://github.com/YOUR_USERNAME/network-test-framework.git
cd network-test-framework
pip install -r requirements.txt

python main.py
```

Then open `reports/test_report.html` in your browser.

---

## Options

```bash
python main.py                          # Full suite
python main.py --no-ping                # Skip ICMP (if firewall blocks ping)
python main.py --config my_config.yaml  # Custom config file
python main.py --out /tmp/reports       # Custom output directory
```

---

## Configuring targets

Edit `config/targets.yaml` to point at your own infrastructure:

```yaml
hosts:
  - name: "My Server"
    address: "192.168.1.10"

http_endpoints:
  - name: "My API"
    url: "https://api.myapp.com/health"
    expected_status: 200
    timeout_s: 3

port_checks:
  - name: "App Server"
    host: "myapp.com"
    port: 8443
    expect_open: true
```

---

## How it works

Each test category is a class inheriting `BaseTest`. Tests are registered into a `TestSuite`, which runs them sequentially, collects `TestResult` objects, and passes the `SuiteResult` to the report generator.

```
targets.yaml
     ↓
TestSuite.register(testers)
     ↓
run() → list of TestResult
     ↓
generate_html_report() → test_report.html
```

The design is deliberately extensible — adding a new test type means creating one new class with an `execute()` method and registering it in `main.py`.

---

## Key concepts demonstrated

- **Subprocess automation** — spawning ping as a child process and parsing output
- **Socket programming** — raw TCP connect for port checks, SSL handshake inspection
- **urllib / HTTP** — protocol-level HTTP validation without third-party libs
- **Test result modelling** — dataclasses for structured pass/fail reporting
- **Report generation** — templated HTML from Python, no frameworks needed
- **YAML-driven config** — targets defined in config, not hardcoded

---

## Tech stack

- Python 3.10+ (stdlib only — socket, subprocess, ssl, urllib)
- PyYAML (config parsing)

---

*Built as a portfolio project demonstrating automation testing, network protocols, and system validation.*

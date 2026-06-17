# CyberPulse Scanner

> A multi-threaded reconnaissance CLI for HTTP security header auditing and TCP port scanning, with structured JSON reporting.

## Table of Contents

- [Overview](#overview)
- [Legal & Ethical Use](#legal--ethical-use)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Report Output](#report-output)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Limitations](#limitations)
- [Testing](#testing)
- [Contributing](#contributing)
- [Contact](#contact)

## Overview

CyberPulse Scanner is a Python command-line tool for lightweight network reconnaissance against a single target. It audits HTTPS responses for missing security headers, runs a multi-threaded TCP scan against a configurable list of ports, and attempts to grab a service banner from each open port. Findings are written to a timestamped JSON report, making the tool useful both for quick manual checks and as a building block in a larger scanning pipeline. It targets security practitioners, system administrators, and students who want a small, dependency-light alternative to heavier scanning suites for a first-pass assessment.

## Legal & Ethical Use

This tool performs active reconnaissance — port scanning and banner grabbing — against the host it is given. Run it only against systems you own or are explicitly authorized to test. Scanning third-party systems without permission may violate computer-misuse laws (e.g., the U.S. Computer Fraud and Abuse Act) or equivalent legislation elsewhere, as well as the target's terms of service. The authors and contributors accept no liability for misuse of this tool.

## Key Features

- **HTTP Security Header Audit** — Flags missing `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`, `Strict-Transport-Security`, and `Permissions-Policy` headers on the target's HTTPS response.
- **Concurrent Port Scanning** — Scans a configurable list of TCP ports using a 10-thread worker pool instead of checking ports one at a time.
- **Service Banner Grabbing** — Attempts to read a banner from each open port for a quick hint at the running service.
- **Structured JSON Reporting** — Writes every finding to a timestamped JSON file for further processing or integration with other tooling.
- **Color-Coded CLI Output** — Uses `colorama` to highlight open ports, detected issues, and errors in the terminal.
- **No External Configuration** — Runs from a single interactive prompt; no `.env` files or config management required.
- **Runs Without Elevated Privileges** — Uses standard `connect()` calls rather than raw sockets, so no root/administrator access is needed.

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3 |
| HTTP client | [`requests`](https://pypi.org/project/requests/) |
| Terminal styling | [`colorama`](https://pypi.org/project/colorama/) — cross-platform ANSI color support |
| Concurrency | `threading` + `queue.Queue` (10-worker pool) |
| Networking | `socket` (standard library) |
| Report format | JSON via `json` (standard library) |

## Requirements

- Python 3.8 or later. The script relies on f-strings (Python 3.6+), but 3.8+ is recommended since 3.6/3.7 are end-of-life.
- `pip` for installing dependencies.
- Outbound network access to the target on TCP 443 (header audit) and on whichever ports are scanned — by default: `21, 22, 23, 25, 53, 80, 110, 443, 445, 3306, 8080`.
- Authorization to scan the target — see [Legal & Ethical Use](#legal--ethical-use).

## Installation

```bash
git clone https://github.com/eryks23/CyberPulse-Scanner.git
cd CyberPulse-Scanner
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

CyberPulse Scanner does not use environment variables or `.env` files. Two things can be adjusted directly in `sec_intel_tool.py`:

1. **Target** — supplied interactively at runtime (see [Usage](#usage)).
2. **Port list** — the default ports scanned are defined in the `if __name__ == "__main__":` block:

```python
common_ports = [21, 22, 23, 25, 53, 80, 110, 443, 445, 3306, 8080]
```

Edit this list to scan a custom set of ports.

## Usage

Run the script and respond to the prompt:

```bash
python sec_intel_tool.py
```

```text
Enter target hostname or IP: www.example.com
```

Enter a bare hostname (e.g. `example.com`) or an IPv4 address. The tool then:

1. Resolves the target to an IP address.
2. Audits the HTTPS response for the five security headers listed in [Key Features](#key-features).
3. Scans the default port list concurrently (10 threads) and attempts to grab a banner from each open port.
4. Writes a JSON report to the current directory.

Example output:

```text
[+] Analyzing HTTP headers for: example.com
[!] DETECTED: Missing security header: Content-Security-Policy
[!] DETECTED: Missing security header: Permissions-Policy

[+] Starting multi-threaded port scan on 93.184.216.34...
[*] Port 80 OPEN | Service: Service unrecognized
[*] Port 443 OPEN | Service: Service unrecognized

[+] Audit complete. Report saved to: report_example.com_20260617.json
```

## Report Output

Each run writes `report_<target>_<YYYYMMDD>.json` to the working directory:

```json
{
    "timestamp": "2026-06-17T10:42:11.123456",
    "target": "example.com",
    "ip": "93.184.216.34",
    "vulnerabilities": [
        {"level": "Medium", "issue": "Missing security header: Content-Security-Policy"}
    ],
    "open_ports": [
        {"port": 80, "banner": "Service unrecognized"},
        {"port": 443, "banner": "Service unrecognized"}
    ]
}
```

| Field | Type | Description |
|---|---|---|
| `timestamp` | string (ISO 8601) | Time the scan started |
| `target` | string | Hostname or IP entered at the prompt |
| `ip` | string | Resolved IPv4 address |
| `vulnerabilities` | array of objects | Missing security headers, each `{"level": "Medium", "issue": "..."}` |
| `open_ports` | array of objects | Open TCP ports, each `{"port": <int>, "banner": "..."}` |

## API Reference

The scanning logic lives in a single class, `SecIntelTool`, which can be imported and reused outside the interactive CLI:

```python
from sec_intel_tool import SecIntelTool

scanner = SecIntelTool("example.com")
if scanner.ip:
    scanner.audit_http_headers()
    scanner.run_multi_scan([80, 443])
    scanner.generate_report()
```

### `SecIntelTool(target)`

Initializes the scanner for `target`. Immediately resolves it to an IP address via `resolve_target()` and stores the result in `self.ip`. Sets up `self.lock` (a `threading.Lock` for thread-safe writes) and `self.report`, the dictionary that accumulates all findings.

**Parameters:** `target` (`str`) — hostname or IP address to audit.

### `resolve_target()`

Resolves `self.target` to an IPv4 address using `socket.gethostbyname()`.

**Returns:** the resolved address as a `str`, or `None` if DNS resolution fails.

### `audit_http_headers()`

Sends an HTTPS `GET` request to `self.target` (5-second timeout) and checks the response for the five headers listed in [Key Features](#key-features). Each missing header is appended to `self.report["vulnerabilities"]`. Connection errors are caught and printed to the console without stopping execution.

**Returns:** `None`. Results are written to `self.report`.

### `service_fingerprint(port)`

Opens a TCP socket to `self.ip:port` (1-second timeout), sends `b"\r\n"`, and reads up to 1024 bytes.

**Parameters:** `port` (`int`) — TCP port to probe.
**Returns:** the decoded banner as a `str`, or `"Service unrecognized"` if the connection fails, times out, or returns no data.

### `scan_port(port)`

Attempts a TCP connection to `self.ip:port`. If the port is open, calls `service_fingerprint()` and appends the result to `self.report["open_ports"]`. Console output and report writes are synchronized with `self.lock`.

**Parameters:** `port` (`int`) — TCP port to scan.
**Returns:** `None`.

### `thread_worker(queue)`

Worker loop intended to run inside a thread. Pulls ports from `queue` and calls `scan_port()` until the queue is empty.

**Parameters:** `queue` (`queue.Queue`) — shared queue of ports to scan.
**Returns:** `None`.

### `run_multi_scan(port_list)`

Loads `port_list` into a `Queue`, starts 10 threads running `thread_worker`, and blocks until all threads finish. This is the main entry point for the concurrent scan.

**Parameters:** `port_list` (`list[int]`) — TCP ports to scan.
**Returns:** `None`.

### `generate_report()`

Serializes `self.report` to indented JSON and writes it to `report_<target>_<YYYYMMDD>.json` in the current working directory.

**Returns:** `None`. Prints the output path, or an error message if the file cannot be written.

## Project Structure

```text
CyberPulse-Scanner/
├── sec_intel_tool.py    # SecIntelTool class + CLI entry point
├── requirements.txt     # Python dependencies
└── README.md
```

## Limitations

- The header audit checks only for the *presence* of the five headers, not their configured values or policy strength.
- `service_fingerprint()` sends a generic CRLF probe. Protocols that require a specific handshake (e.g., TLS on port 443) or wait for a client request (e.g., HTTP on port 80) typically return no banner, so `"Service unrecognized"` is common even on genuinely open ports.
- `vulnerabilities` in the report refers exclusively to missing HTTP security headers — there is no CVE or exploit-based vulnerability scanning.
- Hosts that don't respond on HTTPS, or present an invalid certificate, trigger a caught, printed error without halting the rest of the scan.
- DNS resolution uses `socket.gethostbyname()`, which only returns IPv4 addresses; IPv6-only hosts cannot be resolved.
- Each run produces a new report file; there is no built-in diffing between historical scans.

## Testing

No automated test suite is included. To verify behavior manually, run the script against a host you control:

```bash
python sec_intel_tool.py
```

```text
Enter target hostname or IP: localhost
```

Contributions that add a test suite (e.g., `pytest` with mocked `socket` and `requests` calls) are welcome — see [Contributing](#contributing).

## Contributing

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/your-feature`.
3. Commit your changes: `git commit -m "Add: your feature"`.
4. Push the branch: `git push origin feature/your-feature`.
5. Open a pull request describing the change and how it was tested.

Keep pull requests focused on a single change.


## Contact

Maintained by [eryks23](https://github.com/eryks23). For bugs or feature requests, open an issue on the [GitHub repository](https://github.com/eryks23/CyberPulse-Scanner).

# SubScout

**SubScout** is a lightweight subdomain discovery tool that queries public sources (`crt.sh`, `hackertarget`, `wayback`) and optionally checks which subdomains are alive. It features a beautiful terminal interface with progress bars, colored output, and parallel checking.

![Python](https://img.shields.io/badge/Python-3.6+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Features

-  **Multi‑source**: Queries crt.sh, hackertarget, and Wayback Machine.
- ⚡ **Live check**: Verifies which subdomains respond to HTTP/HTTPS (parallel).
-  **Rich UI**: Progress bars, color‑coded tables, and clear panels.
-  **Export**: Save results to a file; automatically creates an `_alive.txt` version for live hosts.
-  **Verbose mode**: See exactly what’s happening.

## Installation

```bash
git clone https://github.com/arthenox/subscout.git
cd subscout
pip install -r requirements.txt

 Usage

Basic scan:
bash

python subscout.py example.com

Select specific sources and save output:
bash

python subscout.py example.com -s crtsh hackertarget -o subs.txt

Check which subdomains are alive:
bash

python subscout.py example.com --alive -v

 Command Line Options
Option	Description
domain	Target domain (e.g., example.com)
-s, --sources	Sources to use: crtsh, hackertarget, wayback (default: all)
-o, --output	Save results to a file
-v, --verbose	Show detailed progress and logs
--alive	Check which subdomains are currently live
--no-color	Disable colored output for plain terminals
 Example Output
text

$ python subscout.py yahoo.com --alive -v

Fetching subdomains...
✓ crtsh: 142 subdomains found
✓ hackertarget: 86 subdomains found

Checking live hosts...
+----+---------------------+--------+--------+
| #  | Subdomain           | Status | Length |
+----+---------------------+--------+--------+
| 1  | mail.yahoo.com      | ✅ alive | 15    |
| 2  | login.yahoo.com     | ✅ alive | 16    |
| 3  | old.yahoo.com       | ❌ dead  | 13    |
+----+---------------------+--------+--------+

 Requirements

    Python 3.6+

    requests

    rich

⚖️ License

MIT © arthenox

Disclaimer

Use this tool only on domains you own or have explicit permission to test. Unauthorized scanning may violate laws and terms of service.
EOF

# Log Analyzer

A command line tool that reads a web server log file and prints a summary report. Shows things like the slowest endpoints, most errors, top IPs, and response time stats.

No external libraries needed, just Python 3.

---

## How to run

Make sure you have Python 3.7 or above installed.

Generate a sample log file first:

```
python scripts/generate_logs.py
```

This creates `logs/sample.log` with 1000 lines. Then run the analyzer on it:

```
python analyzer.py logs/sample.log
```

You can pass any log file path as the argument. To generate a bigger file:

```
python scripts/generate_logs.py 5000 logs/big.log
```

---

## Project structure

```
assesment/
├── analyzer.py
├── scripts/
│   └── generate_logs.py
├── logs/
│   └── sample.log
├── README.md
└── ANSWERS.md
```

---

## What it handles

- Standard format: `2024-03-15T14:23:01Z 192.168.1.1 GET /api/users 200 142ms`
- Different timestamp formats: slash dates, human readable, unix epoch
- Response time as `142ms`, `0.142s`, or just `142`
- Missing status code shown as `-`
- Extra fields at end of line like user agent strings
- JSON formatted log lines
- Blank lines and totally broken lines are skipped and counted

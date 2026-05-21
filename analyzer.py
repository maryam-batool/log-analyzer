import sys
import re
import json
from datetime import datetime
from collections import defaultdict

def parse_timestamp(ts_str):
    ts_str = ts_str.strip()
    try:
        return datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        pass
    try:
        return datetime.strptime(ts_str, "%Y/%m/%d %H:%M:%S")
    except ValueError:
        pass
    try:
        return datetime.strptime(ts_str, "%d-%b-%Y %H:%M:%S")
    except ValueError:
        pass
    try:
        epoch = float(ts_str)
        if epoch > 1_000_000_000:
            return datetime.utcfromtimestamp(epoch)
    except (ValueError, OSError):
        pass
    return None

def parse_response_time(rt_str):
    rt_str = rt_str.strip()
    match = re.match(r'^(\d+\.?\d*)ms$', rt_str, re.IGNORECASE)
    if match:
        return float(match.group(1))
    match = re.match(r'^(\d+\.?\d*)s$', rt_str, re.IGNORECASE)
    if match:
        return float(match.group(1)) * 1000.0
    match = re.match(r'^(\d+\.?\d*)$', rt_str)
    if match:
        return float(match.group(1))
    return None

def parse_status(status_str):
    status_str = status_str.strip()
    if status_str == '-':
        return None
    try:
        code = int(status_str)
        if 100 <= code <= 599:
            return code
    except ValueError:
        pass
    return None
STANDARD_PATTERN = re.compile(
    r'(\S+)\s+'
    r'(\d{1,3}(?:\.\d{1,3}){3})\s+'
    r'(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+'
    r'(\S+)\s+'
    r'(\S+)\s+'
    r'(\S+)'
)
STANDARD_PATTERN_2TOKEN_TS = re.compile(
    r'(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})\s+'
    r'(\d{1,3}(?:\.\d{1,3}){3})\s+'
    r'(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+'
    r'(\S+)\s+'
    r'(\S+)\s+'
    r'(\S+)'
)
STANDARD_PATTERN_HUMAN_TS = re.compile(
    r'(\d{1,2}-[A-Za-z]{3}-\d{4}\s+\d{2}:\d{2}:\d{2})\s+'
    r'(\d{1,3}(?:\.\d{1,3}){3})\s+'
    r'(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+'
    r'(\S+)\s+'
    r'(\S+)\s+'
    r'(\S+)'
)

def try_parse_standard(line):
    for pattern in [STANDARD_PATTERN, STANDARD_PATTERN_2TOKEN_TS, STANDARD_PATTERN_HUMAN_TS]:
        m = pattern.search(line)
        if m:
            ts_raw, ip, method, path, status_raw, rt_raw = m.groups()
            return {
                "timestamp": parse_timestamp(ts_raw),
                "ip": ip,
                "method": method,
                "path": path,
                "status": parse_status(status_raw),
                "response_time_ms": parse_response_time(rt_raw),
                "raw": line.rstrip()
            }
    return None

def try_parse_json(line):
    stripped = line.strip()
    if not stripped.startswith('{'):
        return None
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    ts_raw = data.get("timestamp") or data.get("time") or data.get("ts") or ""
    ip = data.get("ip") or data.get("remote_addr") or data.get("client") or ""
    method = (data.get("method") or data.get("http_method") or "").upper()
    path = data.get("path") or data.get("url") or data.get("uri") or ""
    status_raw = str(data.get("status") or data.get("status_code") or "-")
    rt_raw = str(data.get("response_time") or data.get("duration") or data.get("latency") or "")
    if not method or not path:
        return None
    return {
        "timestamp": parse_timestamp(str(ts_raw)) if ts_raw else None,
        "ip": ip,
        "method": method,
        "path": path,
        "status": parse_status(status_raw),
        "response_time_ms": parse_response_time(rt_raw) if rt_raw else None,
        "raw": line.rstrip()
    }

def parse_log_file(filepath):
    parsed = []
    malformed_count = 0
    total_lines = 0
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"[ERROR] File not found: {filepath}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Could not open file: {e}")
        sys.exit(1)
    for line in lines:
        total_lines += 1
        if not line.strip():
            malformed_count += 1
            continue
        entry = try_parse_json(line)
        if entry is None:
            entry = try_parse_standard(line)
        if entry is not None:
            parsed.append(entry)
        else:
            malformed_count += 1
    return parsed, malformed_count, total_lines

def get_status_summary(entries):
    counts = defaultdict(int)
    for e in entries:
        if e["status"] is None:
            counts["unknown"] += 1
        elif e["status"] < 400:
            counts["2xx/3xx (success)"] += 1
        elif e["status"] < 500:
            counts["4xx (client error)"] += 1
        else:
            counts["5xx (server error)"] += 1
    return counts

def get_top_endpoints(entries, n=10):
    counts = defaultdict(int)
    for e in entries:
        counts[e["path"]] += 1
    return sorted(counts.items(), key=lambda x: x[1], reverse=True)[:n]

def get_slowest_endpoints(entries, n=10):
    totals = defaultdict(float)
    counts = defaultdict(int)
    for e in entries:
        if e["response_time_ms"] is not None:
            totals[e["path"]] += e["response_time_ms"]
            counts[e["path"]] += 1
    averages = {path: totals[path] / counts[path] for path in totals}
    return sorted(averages.items(), key=lambda x: x[1], reverse=True)[:n]

def get_top_ips(entries, n=10):
    counts = defaultdict(int)
    for e in entries:
        if e["ip"]:
            counts[e["ip"]] += 1
    return sorted(counts.items(), key=lambda x: x[1], reverse=True)[:n]

def get_error_endpoints(entries, n=10):
    counts = defaultdict(int)
    for e in entries:
        if e["status"] and e["status"] >= 400:
            counts[e["path"]] += 1
    return sorted(counts.items(), key=lambda x: x[1], reverse=True)[:n]

def get_method_breakdown(entries):
    counts = defaultdict(int)
    for e in entries:
        counts[e["method"]] += 1
    return dict(counts)

def sep(char="-", length=60):
    print(char * length)

def print_report(parsed, malformed, total):
    print()
    print("=" * 60)
    print("         LOG ANALYZER - SUMMARY REPORT")
    print("=" * 60)
    print(f"  Total lines read     : {total}")
    print(f"  Lines parsed (OK)    : {len(parsed)}")
    print(f"  Lines skipped/bad    : {malformed}")
    if total > 0:
        print(f"  Malformed rate       : {(malformed / total) * 100:.1f}%")
    print()
    if not parsed:
        print("  No valid log entries found.")
        return
    sep()
    print("  STATUS CODE BREAKDOWN")
    sep()
    for label, count in sorted(get_status_summary(parsed).items()):
        print(f"  {label:<30} {count:>6}  ({(count / len(parsed)) * 100:.1f}%)")
    print()
    sep()
    print("  HTTP METHOD BREAKDOWN")
    sep()
    for method, count in sorted(get_method_breakdown(parsed).items(), key=lambda x: x[1], reverse=True):
        print(f"  {method:<10} {count:>6} requests")
    print()
    sep()
    print("  TOP 10 MOST REQUESTED ENDPOINTS")
    sep()
    for i, (path, count) in enumerate(get_top_endpoints(parsed, 10), 1):
        print(f"  {i:>2}. {path:<40} {count:>6} requests")
    print()
    sep()
    print("  TOP 10 SLOWEST ENDPOINTS (avg response time)")
    sep()
    slow = get_slowest_endpoints(parsed, 10)
    if slow:
        for i, (path, avg_ms) in enumerate(slow, 1):
            print(f"  {i:>2}. {path:<40} {avg_ms:>8.1f} ms avg")
    else:
        print("  (no response time data)")
    print()
    sep()
    print("  TOP 10 ENDPOINTS WITH MOST ERRORS (4xx/5xx)")
    sep()
    errors = get_error_endpoints(parsed, 10)
    if errors:
        for i, (path, count) in enumerate(errors, 1):
            print(f"  {i:>2}. {path:<40} {count:>6} errors")
    else:
        print("  (no errors found)")
    print()
    sep()
    print("  TOP 10 IPs BY REQUEST COUNT")
    sep()
    for i, (ip, count) in enumerate(get_top_ips(parsed, 10), 1):
        print(f"  {i:>2}. {ip:<20} {count:>6} requests")
    print()
    response_times = [e["response_time_ms"] for e in parsed if e["response_time_ms"] is not None]
    if response_times:
        sep()
        print("  RESPONSE TIME STATS (ms)")
        sep()
        sorted_rt = sorted(response_times)
        print(f"  Min   : {min(response_times):.1f} ms")
        print(f"  Max   : {max(response_times):.1f} ms")
        print(f"  Avg   : {sum(response_times) / len(response_times):.1f} ms")
        print(f"  Median: {sorted_rt[len(sorted_rt) // 2]:.1f} ms")
        print()
    print("=" * 60)
    print("  END OF REPORT")
    print("=" * 60)
    print()

def main():
    if len(sys.argv) < 2:
        print("Usage: python analyzer.py <path_to_log_file>")
        sys.exit(1)
    filepath = sys.argv[1]
    print(f"[INFO] Analyzing: {filepath}")
    parsed, malformed, total = parse_log_file(filepath)
    print_report(parsed, malformed, total)

if __name__ == "__main__":
    main()

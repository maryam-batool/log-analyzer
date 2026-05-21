import random
import sys
import os
import json
from datetime import datetime
os.makedirs("logs", exist_ok=True)
NUM_LINES = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
OUTPUT_FILE = sys.argv[2] if len(sys.argv) > 2 else "logs/sample.log"
IPS = [
    "192.168.1.42", "10.0.0.7", "172.16.0.3", "203.0.113.5",
    "198.51.100.22", "192.168.0.101", "10.10.10.10", "8.8.8.8"
]
METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH"]
METHOD_WEIGHTS = [60, 20, 8, 5, 7]
PATHS = [
    "/api/users", "/api/users/12", "/api/login", "/api/logout",
    "/api/products", "/api/products/55", "/api/orders",
    "/api/orders/88", "/health", "/metrics", "/api/search",
    "/api/cart", "/api/checkout", "/api/admin/users", "/favicon.ico"
]
STATUS_CODES = [200, 200, 200, 201, 204, 301, 400, 401, 403, 404, 500, 502, 503]
USER_AGENTS = [
    '"Mozilla/5.0 (Windows NT 10.0)"',
    '"curl/7.68.0"',
    '"python-requests/2.28.0"',
    '"PostmanRuntime/7.29.0"'
]
MALFORMED_LINES = [
    "",
    "ERROR: Connection refused at socket layer",
    "   [warn] worker process exited",
    "2024-03-15 PARTIAL WRITE >>>",
    "null null null",
    "GET /api/users 200",
]
def iso_ts(epoch):
    return datetime.utcfromtimestamp(epoch).strftime("%Y-%m-%dT%H:%M:%SZ")
def variant_ts(epoch):
    dt = datetime.utcfromtimestamp(epoch)
    choice = random.randint(0, 2)
    if choice == 0:
        return dt.strftime("%Y/%m/%d %H:%M:%S")
    elif choice == 1:
        return dt.strftime("%d-%b-%Y %H:%M:%S")
    else:
        return str(int(epoch))

def rand_rt():
    ms = random.randint(5, 3000)
    choice = random.randint(0, 2)
    if choice == 0:
        return f"{ms}ms"
    elif choice == 1:
        return f"{ms / 1000:.3f}s"
    else:
        return str(ms)

def normal_line(epoch):
    return f"{iso_ts(epoch)} {random.choice(IPS)} {random.choices(METHODS, weights=METHOD_WEIGHTS)[0]} {random.choice(PATHS)} {random.choice(STATUS_CODES)} {rand_rt()}"

def variant_ts_line(epoch):
    return f"{variant_ts(epoch)} {random.choice(IPS)} {random.choices(METHODS, weights=METHOD_WEIGHTS)[0]} {random.choice(PATHS)} {random.choice(STATUS_CODES)} {rand_rt()}"

def line_with_extras(epoch):
    return f"{normal_line(epoch)} {random.choice(USER_AGENTS)}"

def missing_status_line(epoch):
    return f"{iso_ts(epoch)} {random.choice(IPS)} {random.choices(METHODS, weights=METHOD_WEIGHTS)[0]} {random.choice(PATHS)} - {rand_rt()}"

def json_line(epoch):
    record = {
        "timestamp": iso_ts(epoch),
        "ip": random.choice(IPS),
        "method": random.choices(METHODS, weights=METHOD_WEIGHTS)[0],
        "path": random.choice(PATHS),
        "status": random.choice(STATUS_CODES),
        "response_time": f"{random.randint(5, 2000)}ms"
    }
    return json.dumps(record)

print(f"Generating {NUM_LINES} lines -> {OUTPUT_FILE}")
epoch = 1710512581
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for i in range(NUM_LINES):
        epoch += random.randint(0, 3)
        roll = random.random()
        if roll < 0.70:
            line = normal_line(epoch)
        elif roll < 0.80:
            line = variant_ts_line(epoch)
        elif roll < 0.87:
            line = line_with_extras(epoch)
        elif roll < 0.91:
            line = missing_status_line(epoch)
        elif roll < 0.95:
            line = json_line(epoch)
        else:
            line = random.choice(MALFORMED_LINES)
        f.write(line + "\n")

print(f"Done. Log saved to: {OUTPUT_FILE}")

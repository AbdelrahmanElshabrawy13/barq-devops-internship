#!/usr/bin/env python3
import time
import subprocess
import urllib.request
import sys

BASE_URL = "http://127.0.0.1:8080"

def check_instance():
    try:
        with urllib.request.urlopen(f"{BASE_URL}/instance", timeout=3) as resp:
            return resp.status
    except Exception:
        return 500

def main():
    print("=== Starting High-Availability Failover Test ===")
    print("Stopping app-01 container...")
    subprocess.run(["docker", "stop", "app-01"], check=True)

    print("Testing HTTP traffic stability during app-01 downtime...")
    success, errors = 0, 0
    for _ in range(15):
        if check_instance() == 200:
            success += 1
        else:
            errors += 1
        time.sleep(0.2)

    print(f"Results: {success} Successful (200 OK), {errors} Failures")

    print("Restarting app-01 container...")
    subprocess.run(["docker", "start", "app-01"], check=True)
    time.sleep(4)

    if errors > 0:
        print("[FAIL] Requests failed while one backend was down!")
        sys.exit(1)

    print("[PASS] Failover test passed with 100% availability during backend failure.")
    sys.exit(0)

if __name__ == "__main__":
    main()

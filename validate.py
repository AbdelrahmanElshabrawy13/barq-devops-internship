#!/usr/bin/env python3
import json
import sys
import time
import urllib.request
import urllib.error
import socket

BASE_URL = "http://127.0.0.1:8080"
if len(sys.argv) > 1:
    BASE_URL = f"http://127.0.0.1:{sys.argv[1]}"

def make_request(path, method="GET", data=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"} if data else {}
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))
    except Exception as e:
        print(f"[FAIL] Request to {path} failed: {e}")
        sys.exit(1)

def main():
    print(f"=== Starting System Validation on {BASE_URL} ===")
    
    # 1. Health and Readiness Checks
    status, body = make_request("/health")
    assert status == 200 and body.get("status") == "alive", f"[FAIL] /health failed: {body}"
    print("[PASS] GET /health")

    status, body = make_request("/ready")
    assert status == 200 and body.get("status") == "ready", f"[FAIL] /ready failed: {body}"
    print("[PASS] GET /ready (PostgreSQL + Redis connected)")

    # 2. Base Endpoint
    status, body = make_request("/")
    assert status == 200, f"[FAIL] GET / failed: {body}"
    print("[PASS] GET /")

    # 3. Database /records Endpoint
    status, body = make_request("/records", method="POST", data={"title": "validation_entry"})
    assert status == 201, f"[FAIL] POST /records failed: {body}"
    print("[PASS] POST /records")

    status, body = make_request("/records")
    assert status == 200 and len(body.get("records", [])) > 0, f"[FAIL] GET /records failed: {body}"
    print("[PASS] GET /records")

    # 4. Redis /counter Endpoint
    status, body = make_request("/counter")
    assert status == 200 and "counter" in body, f"[FAIL] GET /counter failed: {body}"
    print("[PASS] GET /counter")

    # 5. Dynamic Load Balancing Verification (app-01 & app-02)
    seen_instances = set()
    for _ in range(10):
        status, body = make_request("/instance")
        if status == 200 and "instance_id" in body:
            seen_instances.add(body.get("instance_id"))
        time.sleep(0.1)

    print(f"Detected instances serving traffic: {seen_instances}")
    if len(seen_instances) < 2:
        print(f"[FAIL] Load balancing failed. Expected both app-01 and app-02, saw: {seen_instances}")
        sys.exit(1)
    print("[PASS] Load Balancing verified across backends")

    # 6. Host Port Isolation Verification
    for port in [5432, 6379]:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        res = s.connect_ex(("127.0.0.1", port))
        s.close()
        if res == 0:
            print(f"[FAIL] Port {port} is directly exposed on host!")
            sys.exit(1)
        print(f"[PASS] Port {port} is isolated from host")

    print("\n=== ALL VALIDATION TESTS PASSED ===")
    sys.exit(0)

if __name__ == "__main__":
    main()

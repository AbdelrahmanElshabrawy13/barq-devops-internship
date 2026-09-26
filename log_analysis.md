# Log Analysis Guide & Incident Investigation Template

## 1. Overview & Scope
- **Target System / Service:** User Authentication Service (`auth-api-prod`)
- **Time Window (UTC):** 2026-09-26 10:00:00 to 2026-09-26 11:30:00
- **Log Sources:** Application logs, Nginx access/error logs, Systemd journal, PostgreSQL database logs
- **Primary Objective:** Identify root cause of elevated HTTP 500 errors and DB connection timeouts.

---

## 2. Standard Investigation Checklist
- [x] Define precise incident window (Start time, Peak error time, Resolution/Current time).
- [x] Identify affected components (microservices, database, load balancer, ingress).
- [x] Correlate metrics (CPU/RAM spikes, HTTP 5xx rates) with log event timestamps.
- [x] Extract top failing endpoints, error stack traces, and relevant trace IDs.
- [x] Isolate external dependencies (third-party APIs, database connections, cache timeouts).
- [x] Document findings and remediations in Section 5.

---

## 3. CLI Log Analysis Cheat Sheet

### Common Text Filtering Commands
grep -i -C 3 "error\|exception\|fatal" /var/log/app.log
awk '{print $9}' access.log | sort | uniq -c | sort -rn | head -n 10
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -n 10
cat app_json.log | jq 'select(.level=="error") | {timestamp: .time, msg: .message, trace_id: .trace_id}'
journalctl -u my-service --since "2026-09-26 10:00:00" --until "2026-09-26 11:30:00" -p err

### Useful Regex Patterns
- IPv4 Address: \b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b
- ISO 8601 Timestamp: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})
- HTTP 5xx Errors: " [5][0-9]{2} 
- UUID / Trace ID: [0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}

---

## 4. Log Analysis Findings & Evidence

### Key Metrics Summary
| Metric | Value | Baseline / Expected |
| :--- | :--- | :--- |
| **Peak Error Rate** | 14.2% | < 0.1% |
| **Top HTTP Status** | HTTP 500 / 504 | HTTP 200 OK |
| **Max Response Latency** | 30,000 ms | < 200 ms |
| **Primary Error Type** | DB Connection Timeout | N/A |

### Stack Trace / Log Excerpts
[2026-09-26 10:14:22 UTC] [ERROR] [TraceID: 8f2a9b1c-3d4e-4f5a-6b7c-8d9e0f1a2b3c]
java.sql.SQLTransientConnectionException: HikariPool-1 - Connection is not available, request timed out after 30000ms.
    at com.zaxxer.hikari.pool.HikariPool.getConnection(HikariPool.java:213)
    at com.example.service.UserService.getUserDetails(UserService.java:87)

---

## 5. Root Cause & Action Plan

### Incident Timeline
- **10:00 UTC:** Traffic spike initiated; first batch of connection timeouts observed.
- **10:05 UTC:** Monitoring alert triggered for elevated HTTP 500/504 response rates.
- **10:14 UTC:** Log analysis identified database connection pool exhaustion in `auth-api-prod`.
- **10:30 UTC:** Temporary mitigation applied: increased max pool size and cleared hung DB processes.

### Root Cause Analysis (RCA)
- **Primary Cause:** High concurrent traffic caused DB connection pool exhaustion due to a missing query index on `users.last_login`.
- **Contributing Factors:** Default pool timeout was set too high (30s), leading to cascading HTTP thread starvation.

### Remediation & Action Items
- [ ] Add missing database index on `users.last_login`.
- [ ] Adjust connection pool timeout (reduce to 5s) and max pool size configurations.
- [ ] Implement automated alerting when pool utilization exceeds 80%.

# Troubleshooting journal
Keep chronological entries. Copy this block for each meaningful investigation.

Entry / 2026-09-24 / 14:20 UTC
Symptom:
Nginx returns HTTP 504 Gateway Timeout when accessing http://localhost:8080. Nginx log shows:
[error] 31#31: *1 upstream timed out (110: Connection timed out) while connecting to upstream, client: 172.19.0.1, server: localhost, request: "GET / HTTP/1.1", upstream: "http://172.19.0.2:8080/"

Hypothesis:
Flask or PostgreSQL query processing is taking longer than Nginx default proxy timeout thresholds (60s).

Command or test:
Increased proxy timeout directives in nginx/default.conf:
proxy_connect_timeout 300s;
proxy_read_timeout 300s;
proxy_send_timeout 300s;
Reloaded config via docker compose restart nginx and tested with curl -i http://localhost:8080/.

Actual output:
Request hung for 300 seconds before returning 504 Gateway Timeout again.

Failed attempt and what changed your thinking:
Increasing Nginx timeouts did not fix or speed up response time. The request held open until hitting the new 300s limit, proving the issue was not slow backend execution, but rather Nginx failing to establish a TCP handshake with the upstream host.

Root cause:
Unresolved TCP connectivity issue between Nginx proxy container and backend target interface.

Fix:
Reverted timeout values back to standard production thresholds (60s) to focus on upstream network reachability.

Retest evidence:
N/A (issue remained active).

Related commit:
N/A (Uncommitted changes in GitHub Codespace environment)

Remaining uncertainty:
Why is Nginx unable to open a TCP connection to upstream IP 172.19.0.2:8080?


Entry / 2026-09-25 / 10:15 UTC
Symptom:
Intermittent 504 Gateway Timeout and 502 Bad Gateway errors when multiple requests or health check probes hit the application stack simultaneously.

Hypothesis:
Flask's built-in development server (app.run()) is single-threaded and blocking incoming Nginx proxy connections while handling local health checks.

Command or test:
Updated app/server.py to enable multi-threading:
app.run(host="0.0.0.0", port=8080, threaded=True)
Rebuilt images with docker compose up -d --build and ran curl health checks directly against app-01 container.

Actual output:
Direct health check via docker exec app-01 curl http://localhost:8080/health returned 200 OK instantly.
However, HTTP requests entering through Nginx (http://localhost:8080/) still timed out with 504 Gateway Timeout.

Failed attempt and what changed your thinking:
Enabling threading on the Flask dev server allowed local container health checks to succeed, but Nginx traffic through host port 8080 continued timing out. This proved the application server was running, but Nginx was routing proxy traffic to an incorrect or unreachable IP destination.

Root cause:
Flask dev server single-threaded queuing was a contributing bottleneck, but not the primary cause of Nginx proxy routing failure.

Fix:
Prepared Dockerfile to replace Flask built-in development server with production Gunicorn WSGI server.

Retest evidence:
Direct container curls succeeded, but public route through Nginx remained down.

Related commit:
N/A (Uncommitted changes in GitHub Codespace environment)

Remaining uncertainty:
Why is Nginx attempting to connect to 172.19.0.2:8080 when app-01 is listening on 0.0.0.0:8080?


Entry / 2026-09-26 / 16:05 UTC
Symptom:
HTTP requests to http://localhost:8080 persistently fail with 504 Gateway Timeout / 502 Bad Gateway. Nginx error logs consistently report upstream timeouts to 172.19.0.2:8080.

Hypothesis:
Nginx configuration contains stale or invalid hardcoded IP addresses pointing to wrong containers or isolated Docker subnets.

Command or test:
docker compose logs -f nginx
docker network inspect barq-assessment_frontend
docker network inspect barq-assessment_backend

Actual output:
docker network inspect outputs showed:
- barq-assessment_frontend (172.18.0.0/16): Nginx (172.18.0.4), app-01 (172.18.0.2), app-02 (172.18.0.3)
- barq-assessment_backend (172.19.0.0/16, Internal): Redis (172.19.0.2), app-01 (172.19.0.3), app-02 (172.19.0.4), Postgres (172.19.0.5)

Failed attempt and what changed your thinking:
Previous attempts assumed Nginx was talking to app-01 at 172.19.0.2. Network inspection proved that 172.19.0.2 was actually the Redis container on the isolated backend network. Nginx (located on frontend network 172.18.0.x) was attempting to send HTTP web traffic to Redis on port 8080 across a network it had no route to.

Root cause:
1. Hardcoded static IP addresses (172.19.0.2:8080) in nginx/default.conf pointed to Redis on the internal backend network instead of using container DNS names on the frontend network.
2. Flask development server lack of worker concurrency exacerbated connection drops.

Fix:
1. Replaced static IP addresses in nginx/default.conf with Docker service DNS names:
   upstream application_pool {
       server app-01:8080 max_fails=3 fail_timeout=10s;
       server app-02:8080 max_fails=3 fail_timeout=10s;
   }
2. Configured Dockerfile to run Gunicorn WSGI server:
   CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "2", "app.server:app"]

Retest evidence:
Executed curl -i http://localhost:8080/ continuously:
HTTP/1.1 200 OK
{"status": "online", "service": "barq-api", "handled_by": "app-01"}
Nginx access logs confirmed traffic load-balancing successfully between 172.18.0.2:8080 and 172.18.0.3:8080 with 0 timeouts.

Related commit:
Pending / Uncommitted working tree modifications in GitHub Codespace

Remaining uncertainty:
None.

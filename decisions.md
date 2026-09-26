# Technical decisions
# Architectural Decision Records (ADRs) & Engineering Rationale

## ADR-01: Upstream Port Alignment & Proxy Failover Strategy

* **Context:** `app-01` was configured in `nginx.conf` with port `8081`, while the Flask application listened on port `8080`. Furthermore, `proxy_next_upstream off;` was configured, causing client requests to fail with `502 Bad Gateway` whenever `app-01` was routed to or encountered errors.
* **Decision:**
  1. Standardized all application backend ports in `nginx/nginx.conf` to `8080`.
  2. Enabled upstream retry logic: `proxy_next_upstream error timeout http_502 http_503 http_504;` with `proxy_next_upstream_tries 2;`.
  3. Configured failure thresholds on upstream pool members: `max_fails=2 fail_timeout=5s`.
* **Impact:** Restored round-robin load distribution across `app-01` and `app-02`. Guaranteed high availability (HA) by ensuring NGINX transparently redirects traffic to a healthy backend if one instance fails or drops out.

---

## ADR-02: Container Network Architecture & Host Isolation

* **Context:** Database (`postgres:5432`) and cache (`redis:6379`) ports were bound to host network interfaces, exposing sensitive infrastructure directly to external network scanning. Additionally, NGINX was placed on the same backend network as the databases.
* **Decision:** Implemented a segmented two-tier network architecture using Docker bridge networks:
  * `frontend`: Connects `nginx` and backend application containers (`app-01`, `app-02`).
  * `backend`: Internal-only network (`internal: true`) connecting application containers, `postgres`, and `redis`.
* **Impact:** Completely isolated PostgreSQL and Redis from direct host port binding (`127.0.0.1` or `0.0.0.0`). Prevents unauthorized direct access to datastores while maintaining necessary inter-container connectivity.

---

## ADR-03: Stateful Data Persistence & Cache Durability

* **Context:** `postgres` used an ephemeral `tmpfs` mount on `/var/lib/postgresql/data`, causing total data loss whenever the container was restarted or updated. `redis` ran without persistence configured.
* **Decision:**
  1. Replaced `tmpfs` with a managed Docker named volume (`postgres-data`) mounted to `/var/lib/postgresql/data`.
  2. Configured Redis startup command with Append-Only File logging: `redis-server --appendonly yes`.
* **Impact:** Ensures database records and Redis cache states persist across container lifecycle events, restarts, and host reboots.

---

## ADR-04: Application Binding & Health Probe Standardization

* **Context:** `APP_HOST` was set to `127.0.0.1`, forcing Flask to bind only to the container's local loopback interface, making it unreachable from NGINX across the Docker network. The Compose healthcheck targeted `/healthz`, which did not match the application route `/health`.
* **Decision:**
  1. Updated `APP_HOST` to `0.0.0.0` across all backend instances.
  2. Updated healthcheck probe target to `http://127.0.0.1:8080/health`.
* **Impact:** Enables external container traffic routing through NGINX while accurately reporting container liveness status to Docker Compose dependencies.

---

## ADR-05: Infrastructure as Code (IaC) & Immutable Dependency Pinning

* **Context:** Base container images in `docker-compose.yml` relied on floating tag versions (`postgres:16-alpine`, `redis:7.4-alpine`), exposing builds to potential breaking updates or supply chain risks.
* **Decision:** Explicitly pinned image digests using immutable SHA-256 hashes for all third-party container images (`postgres`, `redis`, `nginx`).
* **Impact:** Guarantees strict build reproducibility across local development, CI/CD runners, and production environments.

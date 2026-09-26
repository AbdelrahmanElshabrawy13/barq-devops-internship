# AI usage disclosure

- Tool/model: Gemini (Google AI Assistant)
- Purpose: Root cause analysis of Nginx 504/502 errors, Docker network topology inspection, WSGI server configuration, automated backup/restore scripting, CI pipeline generation, security review, chaos testing, log analysis, and project documentation.
- Files or decisions affected: `docker-compose.yml`, `nginx/default.conf`, `Dockerfile`, `app/server.py`, `app.env`, `troubleshooting.md`, `AI_USAGE.md`, `decisions.md`, `security_review.md`, `failure_test.py`, `restore.sh`, `validate.py`, `backup.sh`, `.github/workflows/ci.yml`, `log_analysis.md`.
- What you changed or rejected:
  - Rejected increasing Nginx proxy timeouts to 300s after testing proved it did not fix underlying TCP routing failures.
  - Rejected hardcoded static IP addresses (`172.19.0.2:8080`) in Nginx upstream configuration; replaced them with Docker DNS service names (`app-01:8080`, `app-02:8080`).
  - Replaced single-threaded Flask development server execution (`python -m app.server`) with multi-worker Gunicorn WSGI (`gunicorn`).
  - Attached application containers (`app-01`, `app-02`) to both `frontend` and `backend` networks while keeping database services (`postgres`, `redis`) isolated on `backend`.
  - Created automated database backup (`backup.sh`) and point-in-time recovery (`restore.sh`) scripts integrated with automated validation (`validate.py`).
  - Established environment configuration (`app.env`), CI workflow pipeline (`.github/workflows/ci.yml`), resilience testing suite (`failure_test.py`), security assessment report (`security_review.md`), log analysis documentation (`log_analysis.md`), and architectural decision records (`decisions.md`).
- How you independently verified it:
  - Verified IP address assignments and network boundaries using `docker network inspect barq-assessment_frontend` and `docker network inspect barq-assessment_backend`.
  - Tested backend health endpoints directly using `docker exec app-01 curl -i http://localhost:8080/health`.
  - Sent HTTP requests to public proxy gateway using `curl -i http://localhost:8080/` to confirm round-robin load balancing and HTTP 200 OK responses without timeouts.
  - Validated syntax and structural integrity for shell scripts (`backup.sh`, `restore.sh`), Python scripts (`validate.py`, `failure_test.py`), and YAML workflow configurations (`ci.yml`, `docker-compose.yml`).
- Related commit: Pending / Uncommitted working tree modifications in GitHub Codespace

# Security Review & Risk Assessment Report

## 1. Executive Summary

A comprehensive security audit was conducted across the container infrastructure, networking rules, configuration files, and secrets handling mechanisms. Critical vulnerabilities involving unauthorized data exposure, unsegmented networks, and non-persistent datastores were identified and remediated.

---

## 2. Threat & Risk Assessment Matrix

| Risk ID | Vulnerability / Threat Area | Likelihood | Impact | Status | Mitigation Applied |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SEC-01** | Exposed Database Ports on Host (`5432`, `6379`) | High | Critical | **REMEDIATED** | Removed `ports:` key bindings from `postgres` and `redis` services in Compose. |
| **SEC-02** | Unsegmented Container Network | Medium | High | **REMEDIATED** | Created isolated `frontend` and internal `backend` networks; blocked NGINX from database access. |
| **SEC-03** | Local Loopback Binding (`APP_HOST=127.0.0.1`) | High | High | **REMEDIATED** | Configured `0.0.0.0` binding inside containers while keeping edge exposure strictly through NGINX. |
| **SEC-04** | Plaintext Environment Secrets in VCS | Medium | Medium | **REMEDIATED** | Moved application configuration to `./config/app.env` and restricted file access permissions. |
| **SEC-05** | Image Tag Mutability & Supply Chain | Low | High | **REMEDIATED** | Pinned all base image tags to specific SHA-256 content digests. |

---

## 3. Implemented Security Controls

### Network Hardening & Microsegmentation
* **Internal Network Boundaries:** The `backend` network is defined with `internal: true`. Containers on this network cannot initiate or receive traffic outside the Docker engine unless routed through explicit proxy application rules.
* **Edge Containment:** Only port `8080` (mapped to NGINX port `80`) is bound to the host `127.0.0.1` interface (`127.0.0.1:8080:80`). Direct host access to datastores is blocked, as verified by `validate.py` socket testing.

### Least Privilege & Runtime Security
* **Read-Only Volume Mounts:** Sensitive configuration mounts (`./nginx/nginx.conf` and `./database/init.sql`) are mounted in read-only mode (`:ro`) to prevent compromise via container escape or unauthorized runtime file modifications.
* **Init Container Execution:** Process initialization utilizes `init: true` to ensure proper signal forwarding and zombie process reaping (PID 1 management).

### Secrets Management
* Credentials (`POSTGRES_USER`, `POSTGRES_PASSWORD`, `DATABASE_URL`) are isolated from main code pathways and supplied through environment configurations.

---

## 4. Residual Risks & Production Recommendations

1. **Secrets Rotation:** Plaintext database passwords stored in `app.env` should be migrated to a dedicated secret management solution (e.g., HashiCorp Vault, AWS Secrets Manager, or GitHub Encrypted Secrets) prior to production deployment.
2. **Container Privileges & User Namespaces:** Application containers currently run as the default image user. Production deployments should enforce non-root execution (`USER node/python/nginx`) and enable Docker user namespace remapping (`userns-mode`).
3. **TLS/SSL Encryption:** Traffic between the host and NGINX currently uses plain HTTP. Production ingress must enforce HTTPS/TLS 1.3 encryption using valid certificates.

# System Architecture Documentation

## 1. Overview
This document details the architectural topology, component interactions, and infrastructure layout for the service.

---

## 2. Diagram Assets
- **Image Overview:** ![Architecture Diagram](architecture.png)
- **PDF Version:** [Download PDF Vector Schematic](architecture.pdf)

---

## 3. Core Components

| Layer | Component | Description |
| :--- | :--- | :--- |
| **Ingress** | Nginx / Load Balancer | Handles SSL termination and routes incoming HTTP/HTTPS traffic. |
| **Application** | `auth-api-prod` | Microservice handling user auth, OAuth tokens, and profile lookups. |
| **Cache** | Redis Cluster | Caches active session tokens and user permissions. |
| **Database** | PostgreSQL Primary/Replica | Persistent database storage with connection pooling managed by HikariCP. |

---

## 4. Data Flow
1. **Client** sends request to Nginx Ingress.
2. **Nginx** forwards request to `auth-api-prod` instances.
3. **Application** checks Redis for cached sessions.
4. If cached item is missing, **Application** queries PostgreSQL database via HikariCP pool.

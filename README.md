# Automation Guild 2025 Demo

This repository shows the Automation Guild 2025 Demo using multiple open‑source tools, deployed on [Kubernetes](https://kubernetes.io) via [KinD (Kubernetes in Docker)](https://kind.sigs.k8s.io/). This repo is to be treated as a sandbox, so feel free to clone and modify anything. Create an issue, pull-request, etc. for any issues or improvements. It includes:

- **Flask + HTMX** Frontend
- **FastAPI** Backend (instrumented with [OpenTelemetry](https://opentelemetry.io/) for metrics and tracing)
- **PostgreSQL** database
- **OpenTelemetry Collector**
- **Prometheus** + **Grafana** for metrics collection and visualization
- (Optional) **Jaeger** for distributed tracing
- A **Playwright** test (run via **Pytest**) that exposes a pass/fail metric to Prometheus

This setup provides an end‑to‑end observability demonstration: from basic logs in Python to metrics and dashboards, as well as distributed traces if you enable Jaeger.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Setup and Deployment](#setup-and-deployment)
    1. [Create KinD Cluster](#1-create-kind-cluster)
    2. [Build Docker Images](#2-build-docker-images)
    3. [Load Images into KinD](#3-load-images-into-kind)
    4. [Apply Kubernetes Manifests](#4-apply-kubernetes-manifests)
    5. [Initialize PostgreSQL Table](#5-initialize-postgresql-table)
4. [Accessing the Services](#accessing-the-services)
    1. [Frontend (Flask + HTMX)](#frontend-flask--htmx)
    2. [Prometheus](#prometheus)
    3. [Grafana](#grafana)
    4. [Jaeger (Optional)](#jaeger-optional)
5. [Running the Playwright Test with Pytest](#running-the-playwright-test-with-pytest)
    - [Test Result in Prometheus/Grafana](#test-result-in-prometheusgrafana)
6. [Credentials / Environment Variables](#credentials--environment-variables)
7. [Tools and References](#tools-and-references)
8. [Future Improvements](#future-improvements)

---

## 1. Prerequisites

You’ll need:

- [**Docker**](https://www.docker.com/)
- [**KinD**](https://kind.sigs.k8s.io/) (Kubernetes in Docker)
- [**kubectl**](https://kubernetes.io/docs/tasks/tools/)
- [**Python 3.10+**](https://www.python.org/) (for building images or running tests locally)
- (Optional) [**Playwright**](https://playwright.dev/) if you want to run the test that checks the “Create Item” button.

---

## 2. Architecture Overview

This project features a microservices-like architecture where a **Flask + HTMX** frontend communicates with a **FastAPI** backend, which stores data in **PostgreSQL**. Observability is achieved via **OpenTelemetry**, **Prometheus**, **Grafana**, and optionally **Jaeger**. A **Playwright + Pytest** test checks the frontend and reports the pass/fail metric to Prometheus.

Key components:

- **Frontend (Flask + HTMX)**: Renders a page allowing users to create and list items.
- **Backend (FastAPI)**: Handles item creation/storage, instrumented with OpenTelemetry for metrics/traces.
- **PostgreSQL**: Stores items in a simple table.
- **OpenTelemetry Collector**: Aggregates metrics/traces; exports metrics to Prometheus and (optionally) traces to Jaeger.
- **Prometheus**: Scrapes metrics and provides time‑series data storage.
- **Grafana**: Visualizes the collected metrics in dashboards.
- **Jaeger** (optional): Displays distributed traces for performance and debugging.
- **Playwright + Pytest**: Automates a UI test to ensure the “Create Item” button is present, then exposes a pass/fail metric.

---

## 3. Setup and Deployment

### 1. Create KinD Cluster

1. Ensure Docker is running.
2. Create a KinD cluster with the provided config:

kind create cluster --name o11y-demo --config k8s/kind-config.yaml


3. Verify:

`kubectl get nodes`



### 2. Build Docker Images

**Frontend**:

`cd frontend docker build -t local-frontend:1.0 .`

**Backend**:

`cd ../backend docker build -t local-backend:1.0 .`

### 3. Load Images into KinD

`kind load docker-image local-frontend:1.0 --name o11y-demo kind load docker-image local-backend:1.0 --name o11y-demo`

### 4. Apply Kubernetes Manifests

From the `k8s/` directory:

`cd ../k8s kubectl apply -f postgres-deployment.yaml kubectl apply -f backend-deployment.yaml kubectl apply -f frontend-deployment.yaml kubectl apply -f otel-collector.yaml kubectl apply -f prometheus.yaml kubectl apply -f grafana.yaml`

(Optional)

`kubectl apply -f jaeger.yaml`

### 5. Initialize PostgreSQL Table

`kubectl get pods`

find the "postgres" pod

`kubectl exec -it <postgres-pod> -- psql -U my_user -d my_database -c "CREATE TABLE items (id SERIAL PRIMARY KEY, data TEXT NOT NULL);"`


*(If you used an init script ConfigMap, this might be created automatically.)*

---

## 4. Accessing the Services

### 1. Frontend (Flask + HTMX)

If exposed as a NodePort (e.g., `30500`), open:

http://localhost:30500


You should see a page where you can **Create Item** and **List Items**.

### 2. Prometheus

If `prometheus` service is a `ClusterIP`, port-forward:

`kubectl port-forward svc/prometheus 9090:9090`

Then open:

http://localhost:9090


### 3. Grafana

If using a NodePort (e.g. `32000`):

http://localhost:32000


Log in with credentials set in the YAML (e.g., `admin / my_grafana_password`). In **Data Sources**, add Prometheus with the URL `http://prometheus:9090` (if in the same namespace) or port-forwarded `http://localhost:9090`.

### 4. Jaeger (Optional)

If NodePort is something like `31686`:

http://localhost:31686


Search for traces from `backend-service` if the Otel Collector is exporting to Jaeger.

---

## 5. Running the Playwright Test with Pytest

1. **Install local test dependencies**:

`pip install pytest playwright prometheus_client playwright install`

2. **Run Tests**:

`pytest`


Depending on how you’ve configured the test, it may expose a pass/fail metric on `http://localhost:8000/metrics` or push to a pushgateway.

### Test Result in Prometheus/Grafana

- The `conftest.py` script can set a metric like `demo_test_result` to **1** if passed or **0** if failed.
- Prometheus scrapes that metric (e.g., via `host.docker.internal:8000` if you run tests on your local machine).
- Grafana can display it on a dashboard panel (`demo_test_result` query).

---

## 6. Credentials / Environment Variables

The YAML uses placeholder credentials like `my_user`, `my_password`, and `my_database`. Update them in these ways:

1. **Directly in YAML**:

env:

* name: DB_USER value: "real_user"
* name: DB_PASSWORD value: "superSecret!"

2. **Kubernetes Secrets**:

env:
* name: DB_PASSWORD valueFrom: secretKeyRef: name: database-credentials key: db_password

Then create a secret:

`kubectl create secret generic database-credentials --from-literal=db_password=superSecret!`

3. **Local Env Overrides**:

`DB_USER=my_user DB_PASSWORD=my_password docker run -p 8000:8000 local-backend:1.0`


Similarly, store the Grafana admin password as a secret or override its environment variable.

---

## 7. Tools and References

- [**Docker**](https://www.docker.com/)
- [**KinD**](https://kind.sigs.k8s.io/)
- [**Kubernetes**](https://kubernetes.io/)
- [**Flask**](https://flask.palletsprojects.com/)
- [**HTMX**](https://htmx.org/)
- [**FastAPI**](https://fastapi.tiangolo.com/)
- [**PostgreSQL**](https://www.postgresql.org/)
- [**OpenTelemetry**](https://opentelemetry.io/)
- [**Prometheus**](https://prometheus.io/)
- [**Grafana**](https://grafana.com/)
- [**Jaeger**](https://www.jaegertracing.io/)
- [**Pytest**](https://docs.pytest.org/)
- [**Playwright**](https://playwright.dev/)

---

## 8. Future Improvements

- **Ingress Controller**: Provide friendlier domain names.
- **Pushgateway** or in-cluster test runner for ephemeral test metrics.
- **Kubernetes Secrets** for all credentials.
- **Helm or Kustomize** to simplify deployment.
- **Deeper tracing** if multiple microservices are introduced.

---

Now, have some fun!

#!/usr/bin/env python3

# *****************************************************************************
# Copyright (c) 2026 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# *****************************************************************************

# Verifies, via the Instana Analyze API, that an AI Service tenant namespace has been
# fully removed from a cluster. It is the gate that must pass before the tenant's secrets
# are purged from AWS Secrets Manager (see gitops_deprovision_aiservice_tenant).
#
# Exit codes:
#   0 - Instana reports no pods left in the tenant namespace (totalHits == 0): safe to purge secrets
#   1 - namespace still active after the timeout, Instana unreachable, or cluster not visible in Instana
#
# Environment variables:
#   INSTANA_URL                    (required) e.g. https://myunit-mytenant.instana.io
#   INSTANA_TOKEN                  (required) Instana API token
#   CLUSTER_NAME                   (required) Kubernetes cluster name as reported to Instana
#   AISERVICE_INSTANCE_ID          (required)
#   TENANT_ID                      (required)
#   INSTANA_POLL_INTERVAL_SECONDS  (optional, default 20)
#   INSTANA_POLL_TIMEOUT_MINUTES   (optional, default 10)
#   INSTANA_WINDOW_SECONDS         (optional, default 60) look-back window for the Analyze query. Instana
#                                  returns entities that existed at any point in the window, so keep it short.

import json
import os
import sys
import time
import urllib.error
import urllib.request

ANALYZE_ENTITIES = "api/infrastructure-monitoring/analyze/entities"


def tag_filter(name, value):
    return {"type": "TAG_FILTER", "entity": "NOT_APPLICABLE", "name": name, "operator": "EQUALS", "value": value}


def count_pods(base_url, token, window_seconds, cluster_name, namespace=None):
    """Return totalHits of kubernetesPod entities on the cluster (optionally limited to one namespace)."""
    elements = [tag_filter("kubernetes.cluster.name", cluster_name)]
    if namespace:
        elements.append(tag_filter("kubernetes.namespace.name", namespace))

    body = {
        "type": "kubernetesPod",
        "pagination": {"retrievalSize": 1},
        "timeFrame": {"windowSize": window_seconds * 1000},
        "tagFilterExpression": {"type": "EXPRESSION", "logicalOperator": "AND", "elements": elements},
    }
    request = urllib.request.Request(
        f"{base_url}/{ANALYZE_ENTITIES}",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"apiToken {token}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return int(json.load(response).get("totalHits", 0))


def main():
    required = ["INSTANA_URL", "INSTANA_TOKEN", "CLUSTER_NAME", "AISERVICE_INSTANCE_ID", "TENANT_ID"]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        print(f"ERROR: required environment variables not set: {', '.join(missing)}")
        return 1

    base_url = os.environ["INSTANA_URL"].rstrip("/")
    token = os.environ["INSTANA_TOKEN"]
    cluster_name = os.environ["CLUSTER_NAME"]
    namespace = f"aiservice-{os.environ['AISERVICE_INSTANCE_ID']}-{os.environ['TENANT_ID']}"
    interval = int(os.getenv("INSTANA_POLL_INTERVAL_SECONDS", "20"))
    timeout = int(os.getenv("INSTANA_POLL_TIMEOUT_MINUTES", "10")) * 60
    window = int(os.getenv("INSTANA_WINDOW_SECONDS", "60"))

    print(f"Cluster .................. {cluster_name}")
    print(f"Tenant namespace ......... {namespace}")
    print(f"Poll interval / timeout .. {interval}s / {timeout // 60}m")

    deadline = time.monotonic() + timeout
    cluster_seen = False

    while True:
        try:
            # Zero hits is only trustworthy if Instana can see the cluster at all. If the agent is down or the
            # cluster name is wrong, the namespace query would return 0 and we would purge secrets prematurely.
            if not cluster_seen:
                cluster_hits = count_pods(base_url, token, window, cluster_name)
                if cluster_hits == 0:
                    print(f"Instana reports no pods for cluster {cluster_name}; cannot verify namespace removal")
                    raise RuntimeError("cluster not visible in Instana")
                cluster_seen = True

            total_hits = count_pods(base_url, token, window, cluster_name, namespace)
            if total_hits == 0:
                print(f"totalHits == 0: namespace {namespace} is gone, safe to purge secrets")
                return 0
            print(f"totalHits == {total_hits}: namespace {namespace} still active")
        except (urllib.error.URLError, TimeoutError, RuntimeError, ValueError) as exc:
            # Includes HTTP 4xx/5xx (HTTPError), network failures and non-JSON responses. Never treat as "deleted".
            print(f"Instana check failed: {exc}")

        if time.monotonic() + interval > deadline:
            print(f"ERROR: namespace removal not verified within {timeout // 60} minutes; secrets are preserved")
            return 1
        time.sleep(interval)


if __name__ == "__main__":
    sys.exit(main())

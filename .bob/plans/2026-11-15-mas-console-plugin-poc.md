# MAS OpenShift Console Plugin PoC Plan

## Objective

Build the smallest possible OpenShift Console **dynamic plugin** that provides:

1. A new navigation section in the console: **IBM Maximo**
2. One nav item under it: **Overview**
3. One page at `/mas/overview` showing a table of all MAS **Suite** custom resources in the cluster

The PoC is read-only, has no backend of its own (no proxy, no API server), and gets all data
from the Kubernetes API via the logged-in console user's credentials.

> ⚠️ **Knowledge caveat**: the extension-point schemas, SDK versions and wiring below are from
> training knowledge (early-2025 era), not verified against the current OpenShift release.
> Treat the [openshift/console-plugin-template](https://github.com/openshift/console-plugin-template)
> as the source of truth for exact manifest syntax and SDK versioning, and follow its existing
> `ExamplePage` pattern when swapping in the MAS page.

## Scope

**In scope**
- Nav section + nav item + route + Suite table page
- Container image build (multi-stage: node build → nginx serve)
- Cluster manifests: Deployment, Service (TLS via service-serving cert), `ConsolePlugin` CR, RBAC
- Step-by-step deployment instructions for a running cluster
- Uninstall instructions

**Out of scope (future work)**
- Any write actions on Suite CRs
- Application/workspace detail pages (`apps.mas.ibm.com/*App`, `*Workspace`)
- Console server-side proxy to MAS APIs
- Air-gapped install (image/npm mirroring), GitOps/ansible integration
- Local hot-reload dev workflow (referenced in [Local development](#local-development-optional) only)
- Tests

## Architecture

OpenShift's web console loads dynamic plugins at runtime via webpack Module Federation:

```
┌──────────────────────────┐        ┌─────────────────────────────┐
│  OCP Console (browser)   │        │  mas-console-plugin         │
│  - React + PatternFly    │  HTTP  │  Deployment (nginx)         │
│    shared from host      ├───────►│  - serves dist/ over HTTPS  │
│  - loads plugin bundle   │  :9443 │  - TLS: service-serving cert│
│  - useK8sWatchResource ──┼──┐     └─────────────────────────────┘
└──────────────────────────┘  │                  ▲
                              ▼                  │ ConsolePlugin CR points
                    Kubernetes API               │ console at this service
                    (Suite CRs, as                │
                     logged-in user)   ┌──────────┴──────────┐
                                       │ console operator     │
                                       │ spec.plugins enables │
                                       └─────────────────────┘
```

Key properties:

- The plugin is a **static web app in a container**. No server-side logic for this PoC.
- Plugin JS runs **in the browser as the logged-in console user**. RBAC applies natively —
  the table only shows what the user is allowed to list.
- The console (not us) proxies plugin assets, so the plugin service never needs to be
  exposed outside the cluster.
- React and PatternFly are **shared singletons from the host console** via module federation —
  our bundle is small and visually consistent, but our build must be compatible with the
  console's frontend versions (use the template's pinned versions as the baseline).

## Data source (verified against this repo)

- Suite CR: **`core.mas.ibm.com/v1`, kind `Suite`, plural `suites`**
- Namespaced: one Suite per instance, living in `mas-<instanceId>-core`, named `<instanceId>`
  (see [suite.py:395-433](../../python/src/mas/cli/must_gather/summarizer/suite.py#L395) and
  [cluster-extensions.md](../../docs/reference/cluster-extensions.md))
- Fields used by the table:
  - `metadata.name` — instance ID
  - `metadata.namespace` — always `mas-<instanceId>-core`
  - `status.versions.reconciled` — MAS core version (e.g. `9.1.x`)
  - `status.conditions[type=Ready].status` — readiness (⚠️ verify the exact condition types
    against a live CR with `oc get suite <name> -n mas-<id>-core -o yaml` before trusting it)
  - `metadata.creationTimestamp` — install date

Because Suites are namespaced, the page does a **cluster-wide list/watch** (no namespace filter),
which requires a cluster-scoped `list`/`watch` RBAC grant.

## Project location & structure

Standalone JS project (not inside `ibm-mas/cli` — this repo is Python; keep the plugin
separate so it can graduate to its own repo later):

```
mas-console-plugin/
├── Dockerfile
├── nginx.conf
├── package.json
├── webpack.config.js          # from template, exposes changed to MasOverviewPage
├── consolePlugin.manifest.json
├── tsconfig.json
├── src/
│   └── pages/
│       └── mas-overview.tsx   # the whole feature
└── manifests/
    ├── namespace.yaml
    ├── deployment.yaml
    ├── service.yaml
    ├── consoleplugin.yaml
    └── rbac.yaml
```

## Scaffold from the official template

Start from [openshift/console-plugin-template](https://github.com/openshift/console-plugin-template)
(GitHub "Use this template" / clone and strip). It provides the webpack Module Federation wiring,
TypeScript setup, the `@openshift-console/dynamic-plugin-sdk` dependency at a version matched to
current OCP, a working Dockerfile/nginx TLS setup, and a dev-server workflow. We keep its
infrastructure and replace its example content.

### `consolePlugin.manifest.json` (shape — follow template syntax)

```jsonc
{
  "name": "mas-console-plugin",
  "version": "0.0.1",
  "dependencies": {
    "@console/dynamic-plugin-sdk": "<version pinned by template>"
  },
  "extensions": [
    {
      "type": "console.navigation/section",
      "properties": {
        "id": "mas-nav-section",
        "name": "IBM Maximo"
      }
    },
    {
      "type": "console.navigation/item",
      "properties": {
        "id": "mas-nav-overview",
        "section": "mas-nav-section",
        "name": "Overview",
        "to": "/mas/overview"
      }
    },
    {
      "type": "console.page/route",
      "properties": {
        "exact": true,
        "path": "/mas/overview",
        "component": { "$codeRef": "MasOverviewPage" }
      }
    }
  ]
}
```

Notes:
- No `perspective` on the nav section → appears in both Administrator and Developer navs.
  Add `"perspective": "admin"` to restrict to Administrator.
- `$codeRef: MasOverviewPage` maps to the module exposed in webpack config (the template
  demonstrates the mapping with `ExamplePage` — mirror it exactly).

### `src/pages/mas-overview.tsx` (shape)

```tsx
import * as React from 'react';
import { useK8sWatchResource } from '@openshift-console/dynamic-plugin-sdk';
import { Alert, Card, CardBody, Spinner, Title } from '@patternfly/react-core';
import { Table, Tbody, Td, Th, Thead, Tr } from '@patternfly/react-table';

interface MASCondition { type: string; status: string; reason?: string; message?: string }
interface MASSuite {
  metadata: { name: string; namespace: string; creationTimestamp?: string };
  status?: { versions?: { reconciled?: string }; conditions?: MASCondition[] };
}

const MasOverviewPage: React.FC = () => {
  // No `namespaces` field => cluster-wide list/watch
  const [suites, loaded, loadError] = useK8sWatchResource<MASSuite[]>({
    groupVersionKind: { group: 'core.mas.ibm.com', version: 'v1', kind: 'Suite' },
    isList: true,
  });

  if (loadError) {
    return <Alert variant="danger" title="Unable to load MAS Suites" >{String(loadError)}</Alert>;
  }
  if (!loaded) return <Spinner />;

  return (
    <>
      <Title headingLevel="h1">IBM Maximo Application Suite</Title>
      <Card>
        <CardBody>
          {suites.length === 0 ? (
            <Alert variant="info" title="No MAS instances found" isInline />
          ) : (
            <Table>
              <Thead>
                <Tr>
                  <Th>Instance</Th><Th>Namespace</Th><Th>Version</Th><Th>Status</Th><Th>Created</Th>
                </Tr>
              </Thead>
              <Tbody>
                {suites.map((s) => (
                  <Tr key={s.metadata.name}>
                    <Td>{s.metadata.name}</Td>
                    <Td>{s.metadata.namespace}</Td>
                    <Td>{s.status?.versions?.reconciled ?? '—'}</Td>
                    <Td>{s.status?.conditions?.find((c) => c.type === 'Ready')?.status ?? 'Unknown'}</Td>
                    <Td>{s.metadata.creationTimestamp ?? '—'}</Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          )}
        </CardBody>
      </Card>
    </>
  );
};

export default MasOverviewPage;
```

## Container build

### `Dockerfile` (multi-stage)

```dockerfile
FROM registry.access.redhat.com/ubi9/nodejs-20 AS build
WORKDIR /opt/app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginxinc/nginx-unprivileged:stable
COPY --from=build /opt/app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 9443
```

### `nginx.conf`

```nginx
worker_processes auto;
error_log /dev/stderr;
events { worker_connections 1024; }
http {
  include /etc/nginx/mime.types;
  server {
    listen 9443 ssl;
    ssl_certificate     /etc/pki/tls/tls.crt;   # mounted from service-serving cert secret
    ssl_certificate_key /etc/pki/tls/tls.key;
    root /usr/share/nginx/html;
    location / { try_files $uri $uri/ =404; }
  }
}
```

Build: `npm install && npm run build` locally to validate the webpack output, then
`podman build` / `docker build` for the image.

## Cluster manifests

### `manifests/namespace.yaml`

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: mas-console-plugin
  labels:
    app: mas-console-plugin
```

### `manifests/service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: mas-console-plugin
  namespace: mas-console-plugin
  labels:
    app: mas-console-plugin
  annotations:
    service.beta.openshift.io/serving-cert-secret-name: mas-console-plugin-tls
spec:
  ports:
    - name: https
      port: 9443
      targetPort: 9443
      protocol: TCP
  selector:
    app: mas-console-plugin
```

### `manifests/deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mas-console-plugin
  namespace: mas-console-plugin
  labels:
    app: mas-console-plugin
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mas-console-plugin
  template:
    metadata:
      labels:
        app: mas-console-plugin
    spec:
      containers:
        - name: mas-console-plugin
          # set in deploy step (internal registry reference)
          image: IMAGE_PLACEHOLDER
          imagePullPolicy: IfNotPresent
          ports:
            - name: https
              containerPort: 9443
          volumeMounts:
            - name: plugin-tls
              mountPath: /etc/pki/tls
              readOnly: true
          readinessProbe:
            httpGet:
              scheme: HTTPS
              path: /consolePlugin.manifest.json
              port: 9443
      volumes:
        - name: plugin-tls
          secret:
            secretName: mas-console-plugin-tls
```

### `manifests/consoleplugin.yaml`

```yaml
apiVersion: console.openshift.io/v1
kind: ConsolePlugin
metadata:
  name: mas-console-plugin
spec:
  displayName: IBM Maximo
  backend:
    type: Service
    service:
      name: mas-console-plugin
      namespace: mas-console-plugin
      port: 9443
      basePath: /
```

### `manifests/rbac.yaml`

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: mas-console-plugin-suite-reader
rules:
  - apiGroups: ["core.mas.ibm.com"]
    resources: ["suites"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: mas-console-plugin-suite-reader
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: mas-console-plugin-suite-reader
subjects:
  - kind: Group
    name: cluster-admins
    apiGroup: rbac.authorization.k8s.io
```

Notes:
- `kube:admin` / `system:cluster-admins` can already read everything — this binding makes the
  view work for regular OpenShift users in the `cluster-admins` group. Swap the subject for a
  different group / `system:authenticated` as desired.
- Suites live in many namespaces (`mas-<id>-core`), hence ClusterRole rather than namespaced Role.

## Deploying the PoC to a running cluster

### Prerequisites

- A running OpenShift cluster (any recent 4.x); **MAS does not need to be installed** —
  the page just shows the empty state (handy for first iteration)
- `oc` logged in as cluster-admin
- `podman` or `docker`, `node`/`npm` (node 20+)
- Check the OCP version to confirm template/SDK compatibility:
  `oc get clusterversion` — if the plugin fails to render on a much older/newer console,
  re-scaffold from the template revision matching that OCP version

### Step 0 — Sanity-check the data (on a MAS cluster)

```bash
oc get suites.core.mas.ibm.com -A
oc get suite <name> -n mas-<id>-core -o yaml | less   # confirm condition types / status fields
```

### Step 1 — Build and push the image

Push to the cluster's internal registry (no external registry needed):

```bash
# in mas-console-plugin/
podman build -t mas-console-plugin:0.0.1 .

oc registry login
REGISTRY=$(oc get route default-route -n openshift-image-registry -o jsonpath='{.spec.host}')
podman tag mas-console-plugin:0.0.1 "$REGISTRY/mas-console-plugin/mas-console-plugin:0.0.1"
podman push "$REGISTRY/mas-console-plugin/mas-console-plugin:0.0.1"
```

Then set the image in the deployment to the **internal service name** (worker nodes pull via
the internal endpoint; the default-route hostname is only for external push):

```bash
INTERNAL_IMAGE=image-registry.openshift-image-registry.svc:5000/mas-console-plugin/mas-console-plugin:0.0.1
sed "s|IMAGE_PLACEHOLDER|$INTERNAL_IMAGE|" manifests/deployment.yaml | oc apply -f -
```

(Alternative: push to quay.io or any external registry the cluster can reach and reference that
directly.)

### Step 2 — Apply the manifests

```bash
oc apply -f manifests/namespace.yaml
oc apply -f manifests/service.yaml
oc apply -f manifests/consoleplugin.yaml
oc apply -f manifests/rbac.yaml
# deployment was applied in step 1 (or apply it here after fixing the image ref)
```

### Step 3 — Enable the plugin on the console

```bash
# If no plugins are enabled yet:
oc patch consoles.operator.openshift.io cluster --type json \
  -p '[{"op":"add","path":"/spec/plugins","value":["mas-console-plugin"]}]'

# If other plugins are already enabled, APPEND instead (the first form replaces the list):
oc patch consoles.operator.openshift.io cluster --type json \
  -p '[{"op":"add","path":"/spec/plugins/-","value":"mas-console-plugin"]}]'
```

### Step 4 — Wait for the console to redeploy and verify

Enabling a plugin causes the console operator to roll the console pods (1–2 minutes):

```bash
oc -n openshift-console rollout status deploy/console
oc -n mas-console-plugin get pods          # plugin pod Running/Ready
oc get consoleplugin mas-console-plugin    # exists, no warnings
```

Then in the browser:

1. Open the console URL and **hard-refresh** (Ctrl+Shift+R — the console aggressively caches JS)
2. Use the **Administrator** perspective
3. Expect a new nav section **IBM Maximo** → **Overview**
4. Page shows a table of Suite instances (compare with `oc get suites -A`)

### Troubleshooting

| Symptom | Check |
|---|---|
| Nav section missing | `oc get consoleplugins` + `oc get consoles.operator.openshift.io cluster -o jsonpath='{.spec.plugins}'`; hard-refresh browser |
| Console pods crashloop | `oc logs -n openshift-console deploy/console` — usually means the plugin service/TLS is bad |
| Plugin pod not ready | `oc -n mas-console-plugin describe pod`; check secret `mas-console-plugin-tls` exists (created by the service annotation — may take ~30s) and matches nginx cert paths |
| Page shows error alert | Browser devtools network tab: request to the K8s API for `suites.core.mas.ibm.com` → 403 means RBAC (Section [RBAC](#manifestsrbackyaml)); 404 means wrong GVK |
| Table renders, wrong fields | Re-check Suite CR field names with `oc get suite -o yaml` (see Step 0) |

## Uninstall

```bash
# remove from enabled plugins (careful not to remove other entries — check first with
# oc get consoles.operator.openshift.io cluster -o jsonpath='{.spec.plugins}')
oc patch consoles.operator.openshift.io cluster --type json \
  -p '[{"op":"remove","path":"/spec/plugins"}]'
oc delete consoleplugin mas-console-plugin
oc delete namespace mas-console-plugin
oc delete clusterrole,clusterrolebinding mas-console-plugin-suite-reader
```

## Acceptance criteria

- [ ] "IBM Maximo → Overview" appears in the nav of the Administrator perspective
- [ ] `/mas/overview` renders the Suite table; values match `oc get suites -A`
- [ ] Empty state on a cluster without MAS
- [ ] Live updates: `oc edit suite` / delete a Suite → table updates without refresh (watch works)
- [ ] 403 error state renders cleanly for a user without RBAC

## Local development (optional)

The template supports a hot-reload loop: run its dev server locally (port 9001, HTTPS with a
dev cert) and load it from a locally-running console instance pointed at the live cluster —
see the `console-plugin-template` README ("Development" section) for the exact commands.
For the PoC, the simpler `npm run build && podman build && oc rollout restart` loop is fine.

## Future extensions (not now)

- Tab contribution on the Suite CR's standard resource page (`console.tab`)
- Application/workspace tables (`apps.mas.ibm.com/{Manage,Monitor,...}App`)
- Deep links into the MAS UI (read the suite route/URL from the CR)
- Console server-side proxy (`spec.proxy`) for anything needing service credentials
- Ship via the mas-cli / GitOps install flow with air-gap mirroring

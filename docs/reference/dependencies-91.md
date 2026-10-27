---
widescreen: true
---
MAS 9.1 Application Dependencies
===============================================================================

<div class="mas-arch-scroll">
<div class="mas-arch-root">

  <!-- ══════════════════════════════════════════════════════════════════════
       MAS PANEL — all groups absolutely positioned by JS
       ══════════════════════════════════════════════════════════════════════ -->
  <div class="mas-arch-panel mas-arch-panel-mas" id="mas-arch-canvas">
    <span class="mas-arch-panel-title">Maximo Application Suite 9.1</span>
    <svg id="mas-arch-svg" aria-hidden="true"></svg>
    <!-- ── Group: MAS Core ──────────────────────────────────────────────── -->
    <div class="mas-arch-group" id="mas-arch-g-core">
      <div class="mas-arch-node mas-arch-mas" tabindex="0" id="mas-arch-n-core">Maximo Application Suite Core
        <span class="mas-arch-tip">
          <div class="mas-arch-tip-kind">IBM Maximo Application Suite</div>
          <div class="mas-arch-tip-name">Maximo Application Suite Core</div>
          Foundational platform providing shared services, authentication, licensing, and lifecycle management for all MAS applications.
        </span>
      </div>
      <div class="mas-arch-node mas-arch-other" tabindex="0">MongoDB
        <span class="mas-arch-tip">
          <div class="mas-arch-tip-kind">Required dependency</div>
          <div class="mas-arch-tip-name">MongoDB</div>
          NoSQL document database used for storing application configuration, user data, and operational metadata.
        </span>
      </div>
      <div class="mas-arch-node mas-arch-alt" tabindex="0">Amazon DocumentDb
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Alternative dependency</div><div class="mas-arch-tip-name">Amazon DocumentDB</div>AWS-managed document database, API-compatible with MongoDB. Substitutes MongoDB when MAS is deployed on AWS infrastructure.</span>
      </div>
      <div class="mas-arch-node mas-arch-other" tabindex="0">Suite License Service
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Required dependency</div><div class="mas-arch-tip-name">Suite License Service</div>Manages IBM MAS license entitlements and enforcement across all installed applications.</span>
      </div>
      <div class="mas-arch-node mas-arch-rhos" tabindex="0">Data Reporter Operator
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Red Hat OpenShift dependency</div><div class="mas-arch-tip-name">Data Reporter Operator</div>OpenShift operator that collects and reports software usage data to IBM License Service for compliance tracking.</span>
      </div>
      <div class="mas-arch-node mas-arch-rhos" tabindex="0">Cert-Manager
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Red Hat OpenShift dependency</div><div class="mas-arch-tip-name">Cert-Manager</div>Kubernetes add-on that automates management and issuance of TLS certificates, required for all MAS internal and external TLS communication.</span>
      </div>
    </div>
    <!-- ── Group: Maximo Visual Inspection ──────────────────────────────── -->
    <div class="mas-arch-group" id="mas-arch-g-mvi">
      <div class="mas-arch-node mas-arch-mas" tabindex="0" id="mas-arch-n-mvi">Maximo Visual Inspection
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">IBM Maximo Application Suite</div><div class="mas-arch-tip-name">Maximo Visual Inspection</div>AI-powered visual inspection application using computer vision models to automatically detect defects and anomalies from images and video streams.</span>
      </div>
      <div class="mas-arch-node mas-arch-other" tabindex="0">MongoDB
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Required dependency</div><div class="mas-arch-tip-name">MongoDB</div>Stores inspection results, model metadata, and configuration data for Visual Inspection.</span>
      </div>
      <div class="mas-arch-node mas-arch-alt" tabindex="0">Amazon DocumentDb
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Alternative dependency</div><div class="mas-arch-tip-name">Amazon DocumentDB</div>AWS-managed document database, API-compatible with MongoDB. Can substitute MongoDB when running on AWS infrastructure.</span>
      </div>
      <div class="mas-arch-node mas-arch-other" tabindex="0">NVIDIA GPU Operator
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Required dependency</div><div class="mas-arch-tip-name">NVIDIA GPU Operator</div>Kubernetes operator that automates GPU hardware management within the cluster, required for AI model training and inferencing.</span>
      </div>
      <div class="mas-arch-node mas-arch-other" tabindex="0">Node Feature Discovery Operator
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Required dependency</div><div class="mas-arch-tip-name">Node Feature Discovery Operator</div>Detects hardware features and system configuration to enable GPU and accelerator node labelling needed by the NVIDIA GPU Operator.</span>
      </div>
    </div>
    <!-- ── Group: Maximo Collaborate ────────────────────────────────────── -->
    <div class="mas-arch-group" id="mas-arch-g-col">
      <div class="mas-arch-node mas-arch-mas" tabindex="0" id="mas-arch-n-col">Maximo Collaborate
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">IBM Maximo Application Suite</div><div class="mas-arch-tip-name">Maximo Collaborate</div>Enables field technicians to collaborate through guided work instructions, augmented reality, and remote expert assistance for maintenance tasks.</span>
      </div>
      <div class="mas-arch-node mas-arch-other" tabindex="0">Cloud Object Storage
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Required dependency</div><div class="mas-arch-tip-name">Cloud Object Storage</div>S3-compatible object storage used to store work instruction media assets, images, and collaboration content.</span>
      </div>
    </div>
    <!-- ── Group: Maximo IoT ─────────────────────────────────────────────── -->
    <div class="mas-arch-group" id="mas-arch-g-iot">
      <div class="mas-arch-node mas-arch-mas" tabindex="0" id="mas-arch-n-iot">Maximo IoT
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">IBM Maximo Application Suite</div><div class="mas-arch-tip-name">Maximo IoT</div>Collects, analyses, and acts on data from IoT-connected assets. Provides device management, data ingestion pipelines, and real-time analytics for industrial equipment.</span>
      </div>
      <div class="mas-arch-node mas-arch-cpf" tabindex="0">Db2
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">IBM Cloud Pak Foundation Services</div><div class="mas-arch-tip-name">Db2</div>IBM Db2 relational database deployed via IBM Cloud Pak Foundation Services. Used for device registry, rules, and historical sensor data storage.</span>
      </div>
      <div class="mas-arch-node mas-arch-other" tabindex="0">MongoDB
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Required dependency</div><div class="mas-arch-tip-name">MongoDB</div>Stores device configuration, alert definitions, and operational state data for Maximo IoT.</span>
      </div>
      <div class="mas-arch-node mas-arch-alt" tabindex="0">Amazon DocumentDb
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Alternative dependency</div><div class="mas-arch-tip-name">Amazon DocumentDB</div>AWS-managed document database, API-compatible with MongoDB. Can substitute MongoDB when running Maximo IoT on AWS infrastructure.</span>
      </div>
      <div class="mas-arch-node mas-arch-other" tabindex="0">Apache Kafka
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Required dependency</div><div class="mas-arch-tip-name">Apache Kafka</div>Distributed event streaming platform used for high-throughput ingestion of IoT telemetry data from connected devices and sensors.</span>
      </div>
    </div>
    <!-- ── Group: Maximo Manage ──────────────────────────────────────────── -->
    <div class="mas-arch-group" id="mas-arch-g-manage">
      <div class="mas-arch-node mas-arch-mas" tabindex="0" id="mas-arch-n-manage">Maximo Manage
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">IBM Maximo Application Suite</div><div class="mas-arch-tip-name">Maximo Manage</div>Core enterprise asset management application (formerly IBM Maximo). Provides work management, asset lifecycle, procurement, and inventory management for physical infrastructure.</span>
      </div>
      <div class="mas-arch-node mas-arch-cpf" tabindex="0">Db2
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">IBM Cloud Pak Foundation Services</div><div class="mas-arch-tip-name">Db2</div>Primary relational database for Maximo Manage, storing all EAM data including assets, work orders, and inventory records.</span>
      </div>
      <div class="mas-arch-node mas-arch-alt" tabindex="0">Oracle Database
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Alternative dependency</div><div class="mas-arch-tip-name">Oracle Database</div>Oracle RDBMS can substitute Db2 as the primary database for Maximo Manage, for organisations already standardised on Oracle infrastructure.</span>
      </div>
      <div class="mas-arch-node mas-arch-alt" tabindex="0">SQL Server
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Alternative dependency</div><div class="mas-arch-tip-name">Microsoft SQL Server</div>SQL Server can substitute Db2 as the primary database for Maximo Manage, for organisations already standardised on Microsoft data infrastructure.</span>
      </div>
      <div class="mas-arch-node mas-arch-opt" tabindex="0">Watson Studio Local<br><span class="mas-arch-sub">For Maximo Health</span>
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Optional dependency</div><div class="mas-arch-tip-name">Watson Studio Local (For Maximo Health)</div>Required only when the Maximo Health module is enabled. Provides AI/ML model training and scoring for asset health.</span>
      </div>
      <div class="mas-arch-node mas-arch-opt" tabindex="0">Apache Kafka
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Optional dependency</div><div class="mas-arch-tip-name">Apache Kafka</div>Optionally required by Maximo Manage when event-driven integrations or real-time data streaming scenarios are configured.</span>
      </div>
    </div>
    <!-- ── Group: Maximo Optimizer ───────────────────────────────────────── -->
    <div class="mas-arch-group" id="mas-arch-g-opt">
      <div class="mas-arch-node mas-arch-mas" tabindex="0" id="mas-arch-n-opt">Maximo Optimizer
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">IBM Maximo Application Suite</div><div class="mas-arch-tip-name">Maximo Optimizer</div>AI-driven work order and resource scheduling optimisation for Maximo Manage, maximising workforce productivity and minimising travel time and costs.</span>
      </div>
      <div class="mas-arch-node mas-arch-other" tabindex="0">MongoDB
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Required dependency</div><div class="mas-arch-tip-name">MongoDB</div>Stores optimisation scenarios, configurations, and scheduling results for Maximo Optimizer.</span>
      </div>
      <div class="mas-arch-node mas-arch-alt" tabindex="0">Amazon DocumentDb
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Alternative dependency</div><div class="mas-arch-tip-name">Amazon DocumentDB</div>AWS-managed document database, API-compatible with MongoDB. Can substitute MongoDB for Maximo Optimizer when running on AWS infrastructure.</span>
      </div>
    </div>
    <!-- ── Group: Maximo Real Estate and Facilities ──────────────────────── -->
    <div class="mas-arch-group" id="mas-arch-g-ref">
      <div class="mas-arch-node mas-arch-mas" tabindex="0" id="mas-arch-n-ref">Maximo Real Estate and Facilities
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">IBM Maximo Application Suite</div><div class="mas-arch-tip-name">Maximo Real Estate and Facilities</div>Manages real estate portfolios, space planning, facility maintenance, and lease administration. Extends Maximo Manage with real-estate-specific asset classes and workflows.</span>
      </div>
      <div class="mas-arch-node mas-arch-cpf" tabindex="0">Db2
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">IBM Cloud Pak Foundation Services</div><div class="mas-arch-tip-name">Db2</div>IBM Db2 relational database used for storing real estate, space, and facilities management data.</span>
      </div>
      <div class="mas-arch-node mas-arch-alt" tabindex="0">Oracle Database
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Alternative dependency</div><div class="mas-arch-tip-name">Oracle Database</div>Oracle RDBMS can substitute Db2 as the database backend for Maximo Real Estate and Facilities.</span>
      </div>
      <div class="mas-arch-node mas-arch-alt" tabindex="0">SQL Server
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Alternative dependency</div><div class="mas-arch-tip-name">Microsoft SQL Server</div>SQL Server can substitute Db2 as the database backend for Maximo Real Estate and Facilities.</span>
      </div>
    </div>
    <!-- ── Group: Maximo Predict ─────────────────────────────────────────── -->
    <div class="mas-arch-group" id="mas-arch-g-predict">
      <div class="mas-arch-node mas-arch-mas" tabindex="0" id="mas-arch-n-predict">Maximo Predict
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">IBM Maximo Application Suite</div><div class="mas-arch-tip-name">Maximo Predict</div>Uses AI and machine learning to predict asset failures before they occur, enabling condition-based and predictive maintenance strategies to reduce unplanned downtime.</span>
      </div>
      <div class="mas-arch-node mas-arch-cpf" tabindex="0">Db2
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">IBM Cloud Pak Foundation Services</div><div class="mas-arch-tip-name">Db2</div>IBM Db2 relational database used for storing model data, predictions, and historical asset data within Maximo Predict.</span>
      </div>
      <div class="mas-arch-node mas-arch-other" tabindex="0">Watson Studio Local
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Required dependency</div><div class="mas-arch-tip-name">Watson Studio Local</div>IBM Watson Studio deployed locally on OpenShift. Provides the ML model development, training, and deployment environment required by Maximo Predict.</span>
      </div>
      <div class="mas-arch-node mas-arch-other" tabindex="0">Watson Machine Learning
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Required dependency</div><div class="mas-arch-tip-name">Watson Machine Learning</div>IBM Watson Machine Learning service used to deploy, score, and manage predictive models for asset failure prediction.</span>
      </div>
      <div class="mas-arch-node mas-arch-other" tabindex="0">Watson Analytics Service
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Required dependency</div><div class="mas-arch-tip-name">Watson Analytics Service</div>Provides advanced analytics and reporting capabilities used within Maximo Predict for insights and model performance monitoring.</span>
      </div>
      <div class="mas-arch-node mas-arch-opt" tabindex="0">IBM SPSS Modeler
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Optional dependency</div><div class="mas-arch-tip-name">IBM SPSS Modeler</div>Optional statistical and predictive analytics tool. When installed, can be used within Maximo Predict for advanced statistical model building.</span>
      </div>
    </div>
    <!-- ── Group: Maximo Monitor ─────────────────────────────────────────── -->
    <div class="mas-arch-group" id="mas-arch-g-monitor">
      <div class="mas-arch-node mas-arch-mas" tabindex="0" id="mas-arch-n-monitor">Maximo Monitor
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">IBM Maximo Application Suite</div><div class="mas-arch-tip-name">Maximo Monitor</div>Provides real-time monitoring of IoT-connected assets with anomaly detection, threshold alerting, and dashboards to help operations teams respond to asset condition changes.</span>
      </div>
      <div class="mas-arch-node mas-arch-cpf" tabindex="0">Db2
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">IBM Cloud Pak Foundation Services</div><div class="mas-arch-tip-name">Db2</div>IBM Db2 relational database used for storing alert history, metric data, and dashboard configuration for Maximo Monitor.</span>
      </div>
      <div class="mas-arch-node mas-arch-other" tabindex="0">MongoDB
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Required dependency</div><div class="mas-arch-tip-name">MongoDB</div>Stores real-time metric time-series data, alert state, and operational event data for Maximo Monitor.</span>
      </div>
      <div class="mas-arch-node mas-arch-alt" tabindex="0">Amazon DocumentDb
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Alternative dependency</div><div class="mas-arch-tip-name">Amazon DocumentDB</div>AWS-managed document database, API-compatible with MongoDB. Can substitute MongoDB for Maximo Monitor when deployed on AWS infrastructure.</span>
      </div>
      <div class="mas-arch-node mas-arch-other" tabindex="0">Apache Kafka
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Required dependency</div><div class="mas-arch-tip-name">Apache Kafka</div>Distributed event streaming platform used for high-throughput real-time ingestion of IoT asset metric data from Maximo IoT pipelines.</span>
      </div>
    </div>
  </div><!-- /mas-arch-canvas -->

  <!-- Dashed connector: Integrates with -->
  <div class="mas-arch-connector" title="Integrates with">◀ ─ ─</div>

  <!-- ══════════════════════════════════════════════════════════════════════
       RIGHT PANEL — Maximo AI Service 9.1
       ══════════════════════════════════════════════════════════════════════ -->
  <div class="mas-arch-panel mas-arch-panel-ai">
    <div class="mas-arch-panel-ai-title">Maximo AI Service 9.1</div>
    <div class="mas-arch-ai-col">
      <div class="mas-arch-node mas-arch-mas" tabindex="0">Maximo AI Service
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">IBM Maximo Application Suite</div><div class="mas-arch-tip-name">Maximo AI Service</div>Provides AI inference services and model management capabilities across the Maximo Application Suite, enabling AI-powered features in connected applications.</span>
      </div>
      <div class="mas-arch-node mas-arch-cpd" tabindex="0">Open Data Hub
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">IBM Cloud Pak for Data</div><div class="mas-arch-tip-name">Open Data Hub</div>Open Data Hub (OpenShift AI) provides the ML platform infrastructure — including model serving and pipelines — that Maximo AI Service depends on.</span>
      </div>
      <div class="mas-arch-node mas-arch-rhos" tabindex="0">Data Reporter Operator
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Red Hat OpenShift dependency</div><div class="mas-arch-tip-name">Data Reporter Operator</div>OpenShift operator that collects and reports software usage data to IBM License Service for compliance tracking.</span>
      </div>
      <div class="mas-arch-node mas-arch-other" tabindex="0">Minio
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Required dependency</div><div class="mas-arch-tip-name">Minio</div>High-performance, S3-compatible object storage used for storing AI model artefacts, training datasets, and inference outputs.</span>
      </div>
      <div class="mas-arch-node mas-arch-other" tabindex="0">Suite License Service
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Required dependency</div><div class="mas-arch-tip-name">Suite License Service</div>Manages IBM MAS license entitlements. Required by Maximo AI Service to verify and enforce software licensing.</span>
      </div>
      <div class="mas-arch-node mas-arch-cpf" tabindex="0">Db2
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">IBM Cloud Pak Foundation Services</div><div class="mas-arch-tip-name">Db2</div>IBM Db2 relational database deployed via IBM Cloud Pak Foundation Services, used for storing model registry, metadata, and operational data.</span>
      </div>
    </div>
  </div>

</div><!-- /mas-arch-root -->

<!-- Legend -->
<div class="mas-arch-legend">
  <div class="mas-arch-li"><div class="mas-arch-lb" style="border-color:#6cb4e4;background:#e8f4fd;"></div>IBM Maximo Application Suite</div>
  <div class="mas-arch-li"><div class="mas-arch-lb" style="border-color:#9c27b0;background:#fff;"></div>IBM Cloud Pak for Data</div>
  <div class="mas-arch-li"><div class="mas-arch-lb" style="border-color:#00897b;background:#fff;"></div>IBM Cloud Pak Foundation Services</div>
  <div class="mas-arch-li"><div class="mas-arch-lb" style="border-color:#e8606a;background:#fff;"></div>Red Hat OpenShift Container Platform</div>
  <div class="mas-arch-li"><div class="mas-arch-lb" style="border-color:#555;background:#fff;"></div>Other required dependency</div>
  <div class="mas-arch-li"><div class="mas-arch-lb" style="border-color:#555;background:#fff;border-style:dashed;"></div>Optional / Alternative dependency</div>
  <div class="mas-arch-li"><span style="font-size:14px;">◆ ─ ─</span>&nbsp;Alternatives</div>
  <div class="mas-arch-li"><span style="font-size:14px;">◀ ─ ─</span>&nbsp;Integrates with</div>
</div>
</div><!-- /mas-arch-scroll -->

<script>
(function () {
  var NS = 'http://www.w3.org/2000/svg';

  /* ── Layout constants ───────────────────────────────────────────────────
     All measurements in px.  Groups are positioned by their top-left corner.

     Column centres (cx) and left edges (col_x) for each group:
       col width = 185px, gap between columns = 28px → stride = 213px

     Two horizontal rows:
       ROW_TOP  = 32px  (below panel title)
       ROW_BOT  = computed after we know the tallest top-row group height
                  + VERT_GAP between rows

     Routing buses:
       TOP_BUS  = 18px  — horizontal line above all top-row nodes, used by
                          Core→MVI/Collaborate/IoT arrows
       BOT_BUS  = ROW_BOT - 22px — horizontal line in the gap just above
                          bottom-row nodes, used by Manage→child arrows
  ─────────────────────────────────────────────────────────────────────── */
  /* ── Placement constants — tweak these to adjust the diagram ─────────────
     COL_W    : width of every app+deps column in px
     COL_GAP  : horizontal space between columns
     PAD      : inner padding on all sides of the MAS panel
     ROW_TOP  : y of the Core/top-anchor group (below the panel title)
     VERT_GAP : vertical space between the bottom of the tallest top-row group
                and the top of the bottom-row groups  ← controls arrow corridor
  ─────────────────────────────────────────────────────────────────────────── */
  var COL_W    = 185;  // column width (px) — matches .mas-arch-group CSS width
  var COL_GAP  = 28;   // horizontal gap between columns
  var STRIDE   = COL_W + COL_GAP;
  var PAD      = 14;   // panel inner padding (left/right/bottom)
  var ROW_TOP  = 32;   // top-row anchor y (below panel title)
  var VERT_GAP = 56;   // gap between rows — arrows route through this space

  /* ── Column x positions (left edge) ──────────────────────────────────────
     col 0 : Core (top row only)
     col 1 : MVI / Optimizer  (top / bottom)
     col 2 : Collaborate / RE&F
     col 3 : IoT / Predict
     col 4 : Monitor
     Manage has no column — its x is resolved at runtime as the midpoint
     between Core's right edge and MVI's left edge.                         */
  var COL = [
    PAD,               // col 0 — Core
    PAD + STRIDE,      // col 1 — MVI / Optimizer
    PAD + STRIDE * 2,  // col 2 — Collaborate / RE&F
    PAD + STRIDE * 3,  // col 3 — IoT / Predict
    PAD + STRIDE * 4   // col 4 — Monitor
  ];

  /* ── Group placement ──────────────────────────────────────────────────────
     Top row: Core at col 0, MVI/Col/IoT at cols 1-3 with yOffset:36 so the
     top-bus corridor sits cleanly above their headers.

     Bottom row: the entire row is shifted right by BOT_OFFSET (computed in
     layout() as the difference between manageX and COL[0]).  Each group
     stores its logical col index within the bottom row — layout() adds
     BOT_OFFSET to COL[col] when placing them.  Manage is col 0 of that row
     (logical), children are cols 1-4.  Children use yOffset:36 so the
     bot-bus corridor sits above their headers.
  ─────────────────────────────────────────────────────────────────────────── */
  var GROUPS = [
    { id:'mas-arch-g-core',    col:0, row:0, yOffset:0  },
    { id:'mas-arch-g-mvi',     col:1, row:0, yOffset:36 },
    { id:'mas-arch-g-col',     col:2, row:0, yOffset:36 },
    { id:'mas-arch-g-iot',     col:3, row:0, yOffset:36 },
    { id:'mas-arch-g-manage',  col:0, row:1, yOffset:0  },  // logical col 0 of bottom row
    { id:'mas-arch-g-opt',     col:1, row:1, yOffset:36 },
    { id:'mas-arch-g-ref',     col:2, row:1, yOffset:36 },
    { id:'mas-arch-g-predict', col:3, row:1, yOffset:36 },
    { id:'mas-arch-g-monitor', col:4, row:1, yOffset:36 }
  ];

  /* Arrow definitions — each arrow knows its endpoints by node id */
  var ARROWS = [
    /* Core → top-row apps: exit Core right-mid, down to topBusY, right, drop */
    { from:'mas-arch-n-core', to:'mas-arch-n-mvi',     type:'top-bus'  },
    { from:'mas-arch-n-core', to:'mas-arch-n-col',     type:'top-bus'  },
    { from:'mas-arch-n-core', to:'mas-arch-n-iot',     type:'top-bus'  },
    /* Core → Manage: exit Core right-mid, right to manage.cx, drop to Manage top */
    { from:'mas-arch-n-core', to:'mas-arch-n-manage',  type:'core-manage' },
    /* Manage → child apps: exit Manage right-mid, down to botBusY, right, drop */
    { from:'mas-arch-n-manage', to:'mas-arch-n-opt',     type:'bot-bus' },
    { from:'mas-arch-n-manage', to:'mas-arch-n-ref',     type:'bot-bus' },
    { from:'mas-arch-n-manage', to:'mas-arch-n-predict', type:'bot-bus' },
    { from:'mas-arch-n-manage', to:'mas-arch-n-monitor', type:'bot-bus' },
    /* Predict → Monitor: direct horizontal */
    { from:'mas-arch-n-predict', to:'mas-arch-n-monitor', type:'right'       },
    /* IoT → Monitor: exit IoT right, right to Monitor cx, drop to Monitor top */
    { from:'mas-arch-n-iot',     to:'mas-arch-n-monitor', type:'iot-monitor' }
  ];

  /* ── Position groups and size the canvas ──────────────────────────────── */
  function layout() {
    var canvas = document.getElementById('mas-arch-canvas');
    if (!canvas) return;

    /* First pass: position all top-row groups */
    var topMaxBottom = 0;
    GROUPS.forEach(function (g) {
      var el = document.getElementById(g.id);
      if (!el || g.row !== 0) return;
      var y = ROW_TOP + (g.yOffset || 0);
      el.style.left = COL[g.col] + 'px';
      el.style.top  = y + 'px';
      var bottom = y + el.offsetHeight;
      if (bottom > topMaxBottom) topMaxBottom = bottom;
    });

    /* Bottom-row baseline */
    var ROW_BOT = topMaxBottom + VERT_GAP;

    /* BOT_OFFSET: shifts the entire bottom row so Manage's centre sits in the
       gap between Core's right edge and MVI's left edge.
       manageX (left edge) = midpoint of gap − half col width
       BOT_OFFSET           = manageX − COL[0]
       All bottom-row groups use COL[g.col] + BOT_OFFSET as their left edge. */
    var manageX   = Math.round((COL[0] + COL_W + COL[1]) / 2 - COL_W / 2);
    var BOT_OFFSET = manageX - COL[0];

    /* Second pass: position bottom-row groups */
    var botMaxBottom = 0;
    GROUPS.forEach(function (g) {
      var el = document.getElementById(g.id);
      if (!el || g.row !== 1) return;
      var y = ROW_BOT + (g.yOffset || 0);
      el.style.left = (COL[g.col] + BOT_OFFSET) + 'px';
      el.style.top  = y + 'px';
      var bottom = y + el.offsetHeight;
      if (bottom > botMaxBottom) botMaxBottom = bottom;
    });

    /* Size canvas — bottom row extends further right due to BOT_OFFSET */
    var topMaxCol = Math.max.apply(null, GROUPS.filter(function(g){ return g.row===0; }).map(function(g){ return g.col; }));
    var botMaxCol = Math.max.apply(null, GROUPS.filter(function(g){ return g.row===1; }).map(function(g){ return g.col; }));
    var canvasW = Math.max(COL[topMaxCol] + COL_W, COL[botMaxCol] + BOT_OFFSET + COL_W) + PAD;
    var canvasH = botMaxBottom + PAD;
    canvas.style.width  = canvasW + 'px';
    canvas.style.height = canvasH + 'px';

    drawArrows(ROW_BOT);
  }

  /* ── Draw SVG arrows ──────────────────────────────────────────────────── */
  function drawArrows(ROW_BOT) {
    var svg = document.getElementById('mas-arch-svg');
    if (!svg) return;
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    var canvas   = document.getElementById('mas-arch-canvas');
    var canvasR  = canvas.getBoundingClientRect();

    /* resolve arrow colour from the active Carbon theme */
    var arrowCol = getComputedStyle(document.querySelector('.mas-arch-scroll') || document.body)
                    .getPropertyValue('--mas-arch-arrow').trim() || '#525252';

    /* arrowhead marker */
    var defs   = mkEl('defs', {});
    var marker = mkEl('marker', { id:'mas-arch-ah', markerWidth:'8', markerHeight:'8',
                                  refX:'7', refY:'3', orient:'auto' });
    marker.appendChild(mkEl('path', { d:'M0,0 L0,6 L8,3 z', fill:arrowCol }));
    defs.appendChild(marker);
    svg.appendChild(defs);

    /* convert a node id to a panel-relative bounding box */
    function box(id) {
      var el = document.getElementById(id);
      if (!el) return null;
      var r = el.getBoundingClientRect();
      return {
        cx: r.left - canvasR.left + r.width  / 2,
        cy: r.top  - canvasR.top  + r.height / 2,
        t:  r.top  - canvasR.top,
        b:  r.top  - canvasR.top  + r.height,
        l:  r.left - canvasR.left,
        r:  r.left - canvasR.left + r.width
      };
    }

    var core   = box('mas-arch-n-core');
    var manage = box('mas-arch-n-manage');
    if (!core || !manage) return;

    /* topBusY: corridor used by Core→MVI/Col/IoT top-bus arrows.
       Sits 55% through the gap between core.b and the tops of the
       yOffset:36 top-row groups (MVI/Col/IoT). */
    var mvi = box('mas-arch-n-mvi');
    var topBusY = mvi ? (core.b + (mvi.t - core.b) * 0.55) : (core.b + 18);

    /* draw a path with arrowhead */
    function arrow(d) {
      var p = mkEl('path', { d:d, fill:'none', stroke:arrowCol,
                             'stroke-width':'1.5', 'marker-end':'url(#mas-arch-ah)' });
      svg.appendChild(p);
    }
    /* draw a path without arrowhead (shared bus stub) */
    function stub(d) {
      svg.appendChild(mkEl('path', { d:d, fill:'none', stroke:arrowCol, 'stroke-width':'1.5' }));
    }

    /* Top-bus stub: Core right-mid → right to IoT cx (rightmost top-bus target),
       then the individual branches drop from that horizontal line.
       No vertical drop before the horizontal — exit right first. */
    var iot = box('mas-arch-n-iot');
    var busRight = iot ? iot.cx : core.r;
    stub('M' + core.r + ',' + core.cy + ' L' + busRight + ',' + core.cy);

    ARROWS.forEach(function (def) {
      var f = box(def.from);
      var t = box(def.to);
      if (!f || !t) return;
      var d;

      switch (def.type) {
        case 'top-bus':
          /* Horizontal at core.cy → drop to t.t (arrowhead at target top) */
          d = 'M' + core.r + ',' + core.cy +
              ' L' + t.cx  + ',' + core.cy +
              ' L' + t.cx  + ',' + t.t;
          break;

        case 'core-manage':
          /* Core right-mid → right to manage.cx → down to manage.t */
          d = 'M' + core.r    + ',' + core.cy +
              ' L' + manage.cx + ',' + core.cy +
              ' L' + manage.cx + ',' + manage.t;
          break;

        case 'bot-bus':
          /* Manage right-mid → right to t.cx → down to t.t */
          d = 'M' + manage.r + ',' + manage.cy +
              ' L' + t.cx    + ',' + manage.cy +
              ' L' + t.cx    + ',' + t.t;
          break;

        case 'right':
          /* Direct horizontal: Predict right → Monitor left */
          d = 'M' + f.r + ',' + f.cy +
              ' L' + t.l + ',' + t.cy;
          break;

        case 'iot-monitor':
          /* IoT right-mid → right to Monitor cx+20 → down to Monitor top
             Offset 20px right of centre so it is visually distinct from
             the Manage→Monitor arrow which lands at Monitor cx. */
          d = 'M' + f.r        + ',' + f.cy +
              ' L' + (t.cx+20) + ',' + f.cy +
              ' L' + (t.cx+20) + ',' + t.t;
          break;
      }
      if (d) arrow(d);
    });
  }

  function mkEl(tag, attrs) {
    var el = document.createElementNS(NS, tag);
    Object.keys(attrs).forEach(function (k) { el.setAttribute(k, attrs[k]); });
    return el;
  }

  /* ── Run layout + arrows, redraw on resize or theme change ───────────── */
  function run() { layout(); }

  if (document.readyState === 'complete') { run(); }
  else { window.addEventListener('load', run); }
  window.addEventListener('resize', run);

  /* Redraw arrows when the Carbon theme toggle changes data-carbon-theme
     on <html> so arrow/arrowhead colours update immediately. */
  new MutationObserver(function (mutations) {
    mutations.forEach(function (m) {
      if (m.attributeName === 'data-carbon-theme') { run(); }
    });
  }).observe(document.documentElement, { attributes: true });

  /* ── Tooltip logic ──────────────────────────────────────────────────────── */
  var nodes = document.querySelectorAll('.mas-arch-node');

  nodes.forEach(function (el) {
    el.addEventListener('mouseenter', function () { reposition(el); });
    el.addEventListener('click', function (e) {
      e.stopPropagation();
      var was = el.classList.contains('mas-arch-pinned');
      nodes.forEach(function (n) { n.classList.remove('mas-arch-pinned'); });
      if (!was) { el.classList.add('mas-arch-pinned'); reposition(el); }
    });
  });

  document.addEventListener('click', function () {
    nodes.forEach(function (n) { n.classList.remove('mas-arch-pinned'); });
  });

  function reposition(el) {
    var tip = el.querySelector('.mas-arch-tip');
    if (!tip) return;
    tip.classList.remove('mas-arch-tip-up');
    var rect = el.getBoundingClientRect();
    /* Flip upward if: viewport bottom is close, OR the node sits inside the
       canvas and a below-tooltip would overflow the canvas bottom edge.     */
    var canvas = document.getElementById('mas-arch-canvas');
    var canvasBottom = canvas ? canvas.getBoundingClientRect().bottom : window.innerHeight;
    var flipUp = (rect.bottom + 180 > window.innerHeight) ||
                 (rect.bottom + 180 > canvasBottom);
    if (flipUp) tip.classList.add('mas-arch-tip-up');
    var TIP_W = 240, MARGIN = 8;
    var scroll = el.closest('.mas-arch-scroll') || document.body;
    var sR = scroll.getBoundingClientRect();
    var nodeC = rect.left - sR.left + rect.width / 2;
    var ideal = rect.width / 2 - TIP_W / 2;
    var lo = ideal - (nodeC - TIP_W / 2 - MARGIN);
    var hi = ideal + (sR.width - nodeC - TIP_W / 2 - MARGIN);
    var left = Math.max(lo, Math.min(ideal, hi));
    tip.style.left = left + 'px';
    tip.style.setProperty('--caret', (rect.width / 2 - left) + 'px');
  }
})();
</script>

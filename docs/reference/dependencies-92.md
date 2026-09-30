---
widescreen: true
---
Maximo Application Suite 9.2
===============================================================================

<div class="mas-arch-scroll">
<div class="mas-arch-root">

  <!-- ══════════════════════════════════════════════════════════════════════
       MAS PANEL — all groups absolutely positioned by JS
       ══════════════════════════════════════════════════════════════════════ -->
  <div class="mas-arch-panel mas-arch-panel-mas" id="mas-arch-canvas">
    <span class="mas-arch-panel-title">Maximo Application Suite 9.2</span>
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
      <div class="mas-arch-node mas-arch-mas" tabindex="0" id="mas-arch-n-mmf">Maximo Manage Foundation
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">IBM Maximo Application Suite</div><div class="mas-arch-tip-name">Maximo Manage Foundation</div>Base layer required alongside MAS Core for all MAS application deployments. Provides foundational Manage services consumed by MVI, IoT, and all child applications.</span>
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
      <div class="mas-arch-node mas-arch-cpf" tabindex="0">Db2
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">IBM Cloud Pak Foundation Services</div><div class="mas-arch-tip-name">Db2</div>Primary relational database for Maximo Manage, storing all EAM data including assets, work orders, and inventory records.</span>
      </div>
      <div class="mas-arch-node mas-arch-alt" tabindex="0">Oracle Database
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Alternative dependency</div><div class="mas-arch-tip-name">Oracle Database</div>Oracle RDBMS can substitute Db2 as the primary database for Maximo Manage, for organisations already standardised on Oracle infrastructure.</span>
      </div>
      <div class="mas-arch-node mas-arch-alt" tabindex="0">SQL Server
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Alternative dependency</div><div class="mas-arch-tip-name">Microsoft SQL Server</div>SQL Server can substitute Db2 as the primary database for Maximo Manage, for organisations already standardised on Microsoft data infrastructure.</span>
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
    <!-- ── Group: Maximo Monitor ─────────────────────────────────────────── -->
    <div class="mas-arch-group" id="mas-arch-g-monitor">
      <div class="mas-arch-node mas-arch-mas" tabindex="0" id="mas-arch-n-monitor">Maximo Monitor
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">IBM Maximo Application Suite</div><div class="mas-arch-tip-name">Maximo Monitor</div>Provides real-time monitoring of IoT-connected assets with anomaly detection, threshold alerting, and dashboards to help operations teams respond to asset condition changes.</span>
      </div>
      <div class="mas-arch-node mas-arch-cpf" tabindex="0">Db2
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">IBM Cloud Pak Foundation Services</div><div class="mas-arch-tip-name">Db2</div>IBM Db2 relational database used for storing alert history, metric data, and dashboard configuration for Maximo Monitor.</span>
      </div>
      <div class="mas-arch-node mas-arch-opt" tabindex="0">Apache Kafka
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Optional dependency</div><div class="mas-arch-tip-name">Apache Kafka</div>Distributed event streaming platform used for high-throughput real-time ingestion of IoT asset metric data from Maximo IoT pipelines.</span>
      </div>
    </div>
    <!-- ── Group: Maximo IoT ─────────────────────────────────────────────── -->
    <div class="mas-arch-group" id="mas-arch-g-iot">
      <div class="mas-arch-node mas-arch-mas" tabindex="0" id="mas-arch-n-iot">Maximo IoT
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">IBM Maximo Application Suite</div><div class="mas-arch-tip-name">Maximo IoT</div>Collects, analyses, and acts on data from IoT-connected assets. Provides device management, data ingestion pipelines, and real-time analytics for industrial equipment.</span>
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
      <div class="mas-arch-node mas-arch-opt mas-arch-cpd" tabindex="0">Watson Studio Local<br><span class="mas-arch-sub">For Maximo Health</span>
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Optional dependency</div><div class="mas-arch-tip-name">Watson Studio Local (For Maximo Health)</div>Required only when the Maximo Health module is enabled. Provides AI/ML model training and scoring for asset health.</span>
      </div>
      <div class="mas-arch-node mas-arch-opt" tabindex="0">Apache Kafka
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Optional dependency</div><div class="mas-arch-tip-name">Apache Kafka</div>Optionally required by Maximo Manage when event-driven integrations or real-time data streaming scenarios are configured.</span>
      </div>
      <div class="mas-arch-node mas-arch-opt" tabindex="0">Cloud Object Storage
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Required dependency</div><div class="mas-arch-tip-name">Cloud Object Storage</div>S3-compatible object storage used to store work instruction media assets, images, and collaboration content.</span>
      </div>
      <div class="mas-arch-node mas-arch-opt mas-arch-cpd" tabindex="0">Cognos Analytics
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Optional dependency</div><div class="mas-arch-tip-name">IBM Cognos</div>IBM Cognos Analytics can substitute BIRT as the reporting engine for Maximo Manage, providing enterprise-grade dashboards and self-service reporting capabilities.</span>
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
      <div class="mas-arch-node mas-arch-cpd" tabindex="0">Watson Studio Local
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">IBM Cloud Pak for Data</div><div class="mas-arch-tip-name">Watson Studio Local</div>IBM Watson Studio deployed locally on OpenShift. Provides the ML model development, training, and deployment environment required by Maximo Predict.</span>
      </div>
      <div class="mas-arch-node mas-arch-cpd" tabindex="0">Watson Machine Learning
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">IBM Cloud Pak for Data</div><div class="mas-arch-tip-name">Watson Machine Learning</div>IBM Watson Machine Learning service used to deploy, score, and manage predictive models for asset failure prediction.</span>
      </div>
      <div class="mas-arch-node mas-arch-cpd" tabindex="0">Watson Analytics Service
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">IBM Cloud Pak for Data</div><div class="mas-arch-tip-name">Watson Analytics Service</div>Provides advanced analytics and reporting capabilities used within Maximo Predict for insights and model performance monitoring.</span>
      </div>
    </div>
  </div><!-- /mas-arch-canvas -->

  <!-- Dashed connector: Integrates with -->
  <div class="mas-arch-connector" title="Integrates with">◀ ─ ─</div>

  <!-- ══════════════════════════════════════════════════════════════════════
       RIGHT PANEL — Maximo AI Service 9.2
       ══════════════════════════════════════════════════════════════════════ -->
  <div class="mas-arch-panel mas-arch-panel-ai">
    <div class="mas-arch-panel-ai-title">Maximo AI Service 9.2</div>
    <div class="mas-arch-ai-col">
      <div class="mas-arch-node mas-arch-mas" tabindex="0">Maximo AI Service
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">IBM Maximo Application Suite</div><div class="mas-arch-tip-name">Maximo AI Service</div>Provides AI inference services and model management capabilities across the Maximo Application Suite, enabling AI-powered features in connected applications.</span>
      </div>
      <div class="mas-arch-node mas-arch-cpf" tabindex="0">Db2
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">IBM Cloud Pak Foundation Services</div><div class="mas-arch-tip-name">Db2</div>IBM Db2 relational database deployed via IBM Cloud Pak Foundation Services, used for storing model registry, metadata, and operational data.</span>
      </div>
      <div class="mas-arch-node mas-arch-other" tabindex="0">Cloud Object Storage
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Required dependency</div><div class="mas-arch-tip-name">Cloud Object Storage</div>High-performance, S3-compatible object storage used for storing AI model artefacts, training datasets, and inference outputs.</span>
      </div>
      <div class="mas-arch-node mas-arch-other" tabindex="0">Suite License Service
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Required dependency</div><div class="mas-arch-tip-name">Suite License Service</div>Manages IBM MAS license entitlements. Required by Maximo AI Service to verify and enforce software licensing.</span>
      </div>
      <div class="mas-arch-node mas-arch-rhos" tabindex="0">Data Reporter Operator
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Red Hat OpenShift dependency</div><div class="mas-arch-tip-name">Data Reporter Operator</div>OpenShift operator that collects and reports software usage data to IBM License Service for compliance tracking.</span>
      </div>
      <div class="mas-arch-node mas-arch-rhos" tabindex="0">Cert-Manager
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Red Hat OpenShift dependency</div><div class="mas-arch-tip-name">Cert-Manager</div>Kubernetes add-on that automates management and issuance of TLS certificates, required for all MAS internal and external TLS communication.</span>
      </div>
      <div class="mas-arch-node mas-arch-rhos" tabindex="0">AI Platform
        <span class="mas-arch-tip"><div class="mas-arch-tip-kind">Red Hat OpenShift dependency</div><div class="mas-arch-tip-name">AI Platform</div>RedHat OpenShift AI provides the ML platform infrastructure, including model serving and pipelines, that Maximo AI Service depends on.</span>
      </div>
    </div>
  </div>

</div><!-- /mas-arch-root -->

<!-- Legend -->
<div class="mas-arch-legend">
  <div class="mas-arch-li"><div class="mas-arch-lb mas-arch-lb-mas"></div>IBM Maximo Application Suite</div>
  <div class="mas-arch-li"><div class="mas-arch-lb mas-arch-lb-cpd"></div>IBM Cloud Pak for Data</div>
  <div class="mas-arch-li"><div class="mas-arch-lb mas-arch-lb-cpf"></div>IBM Cloud Pak Foundation Services</div>
  <div class="mas-arch-li"><div class="mas-arch-lb mas-arch-lb-rhos"></div>Red Hat OpenShift Container Platform</div>
  <div class="mas-arch-li"><div class="mas-arch-lb mas-arch-lb-other"></div>Other required dependency</div>
  <div class="mas-arch-li"><div class="mas-arch-lb mas-arch-lb-opt"></div>Optional / Alternative dependency</div>
  <div class="mas-arch-li"><span class="mas-arch-legend-icon">◆ ─ ─</span>&nbsp;Alternatives</div>
  <div class="mas-arch-li"><span class="mas-arch-legend-icon">◀ ─ ─</span>&nbsp;Integrates with</div>
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
       TOP_BUS  = horizontal line at pairExitY, used by {Core+MMF}→MVI/IoT arrows
       BOT_BUS  = ROW_BOT - 22px — horizontal line in the gap just above
                  bottom-row nodes, used by Manage→child arrows

     Paired source (Core + Maximo Manage Foundation):
       Each of Core and MMF emits a short horizontal stub of JOIN_STUB px to
       the right, meeting a vertical join line at joinX = core.r + JOIN_STUB.
       The outbound bus exits from (joinX, pairExitY) where pairExitY is the
       vertical midpoint of the join segment (midpoint between core.cy and
       mmf.cy).  MVI/IoT use a larger yOffset so their tops sit below pairExitY,
       leaving a clean corridor for the horizontal bus.
  ─────────────────────────────────────────────────────────────────────── */
  /* ── Placement constants — tweak these to adjust the diagram ─────────────
     COL_W            : width of every app+deps column in px
     COL_GAP          : horizontal space between columns
     PAD              : inner padding on all sides of the MAS panel
     ROW_TOP          : y of the Core/top-anchor group (below the panel title)
     VERT_GAP         : vertical space between the bottom of the tallest top-row group
                        and the top of the bottom-row groups  ← controls arrow corridor
     JOIN_STUB        : horizontal distance Core/MMF nodes travel right before the
                        vertical bracket join line.  joinX = COL[0] + COL_W + JOIN_STUB.
     MANAGE_BUS_TRAVEL: additional horizontal distance the bus travels right from joinX
                        before dropping down to Manage.
                        manageDropX = joinX + MANAGE_BUS_TRAVEL
                        This produces the shape:
                          Core  ──┐
                                  │ (joinX)
                          MMF   ──┘
                                  └──────────── bus ──────────→
                                        │                 │
                                      Manage             MVI …
     TOP_SHIFT        : extra horizontal offset applied to top-row cols ≥ 1 (MVI, IoT)
                        and all bottom-row child cols ≥ 1 (Optimizer…Monitor).
  ─────────────────────────────────────────────────────────────────────────── */
  var COL_W             = 185;  // column width (px) — matches .mas-arch-group CSS width
  var COL_GAP           = 28;   // horizontal gap between columns
  var STRIDE            = COL_W + COL_GAP;
  var PAD               = 14;   // panel inner padding (left/right/bottom)
  var ROW_TOP           = 32;   // top-row anchor y (below panel title)
  var VERT_GAP          = 56;   // gap between rows — arrows route through this space
  var JOIN_STUB         = 24;   // px each paired node travels right before the vertical join
  var MANAGE_BUS_TRAVEL = 36;   // px the bus travels right from joinX before dropping to Manage
  var TOP_SHIFT         = 120;  // extra px shift applied to top-row and child bottom-row cols ≥ 1

  /* ── Column x positions (left edge) ──────────────────────────────────────
     col 0 : Core             (not shifted — also anchor for Manage in bottom row)
     col 1 : RE&F / Optimizer — shifted right by TOP_SHIFT
     col 2 : MVI / Predict    — shifted right by TOP_SHIFT
     col 3 : Monitor          — shifted right by TOP_SHIFT
     col 4 : IoT              — shifted right by TOP_SHIFT (top row only)
     Manage has no column — its cx = joinX + MANAGE_BUS_TRAVEL, resolved in layout(). */
  var COL = [
    PAD,                          // col 0 — Core
    PAD + STRIDE + TOP_SHIFT,     // col 1 — RE&F / Optimizer
    PAD + STRIDE * 2 + TOP_SHIFT, // col 2 — MVI / Predict
    PAD + STRIDE * 3 + TOP_SHIFT, // col 3 — Monitor
    PAD + STRIDE * 4 + TOP_SHIFT  // col 4 — IoT (top row only)
  ];

  /* ── Group placement ──────────────────────────────────────────────────────
     Top row (left→right): Core(0), RE&F(1), MVI(2), Monitor(3), IoT(4)
       yOffset:0 for Core; yOffset:80 on cols 1-4 so their tops sit below
       pairExitY, giving the top bus a clear right-then-down routing path.

     Bottom row: Manage(0), Optimizer(1), Predict(2)
       Manage cx = joinX + MANAGE_BUS_TRAVEL (via BOT_OFFSET in layout()).
       Child groups use COL[1..2] + BOT_OFFSET, aligning under top-row peers.
       yOffset:36 so the bot-bus corridor sits above their headers.
  ─────────────────────────────────────────────────────────────────────────── */
  var GROUPS = [
    { id:'mas-arch-g-core',    col:0, row:0, yOffset:0  },
    { id:'mas-arch-g-ref',     col:1, row:0, yOffset:60 },  // Facilities — top row col 1
    { id:'mas-arch-g-mvi',     col:2, row:0, yOffset:60 },  // MVI        — top row col 2
    { id:'mas-arch-g-monitor', col:3, row:0, yOffset:60 },  // Monitor    — top row col 3
    { id:'mas-arch-g-iot',     col:4, row:0, yOffset:60 },  // IoT        — top row col 4
    { id:'mas-arch-g-manage',  col:0, row:1, yOffset:0  },  // logical col 0 of bottom row
    { id:'mas-arch-g-opt',     col:1, row:1, yOffset:40 },
    { id:'mas-arch-g-predict', col:2, row:1, yOffset:40 }
  ];

  /* Arrow definitions — each arrow knows its endpoints by node id */
  var ARROWS = [
    /* {Core+MMF} → top-row apps: bus drops at each app's cx */
    { from:'mas-arch-n-core', to:'mas-arch-n-ref',     type:'top-bus' },
    { from:'mas-arch-n-core', to:'mas-arch-n-mvi',     type:'top-bus' },
    { from:'mas-arch-n-core', to:'mas-arch-n-monitor', type:'top-bus' },
    /* {Core+MMF} → Manage: bus drops at manage.cx */
    { from:'mas-arch-n-core', to:'mas-arch-n-manage',  type:'core-manage' },
    /* Manage → child apps: bot-bus drops */
    { from:'mas-arch-n-manage', to:'mas-arch-n-opt',     type:'bot-bus' },
    { from:'mas-arch-n-manage', to:'mas-arch-n-predict', type:'bot-bus' },
    /* Monitor → IoT: Monitor right-mid → IoT left-mid (Monitor is left of IoT) */
    { from:'mas-arch-n-monitor', to:'mas-arch-n-iot', type:'right' }
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

    /* Manage is positioned so its centre (cx) = joinX + MANAGE_BUS_TRAVEL.
       joinX        = COL[0] + COL_W + JOIN_STUB  (mirrors the drawArrows formula)
       manageDropX  = joinX + MANAGE_BUS_TRAVEL   (where the bus drops to Manage)
       manageX      = manageDropX − COL_W / 2     (left edge of Manage group)
       BOT_OFFSET   = manageX − COL[0]
       Bottom-row child groups use COL[g.col] (which includes TOP_SHIFT) +
       BOT_OFFSET as their left edge, placing them under their top-row peers. */
    var joinX_layout  = COL[0] + COL_W + JOIN_STUB;
    var manageDropX   = joinX_layout + MANAGE_BUS_TRAVEL;
    var manageX       = Math.round(manageDropX - COL_W / 2);
    var BOT_OFFSET    = manageX - COL[0];

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
    var marker = mkEl('marker', { id:'mas-arch-ah', markerWidth:'5', markerHeight:'5',
                                  refX:'4', refY:'2', orient:'auto' });
    marker.appendChild(mkEl('path', { d:'M0,0 L0,4 L5,2 z', fill:arrowCol }));
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
    var mmf    = box('mas-arch-n-mmf');
    var manage = box('mas-arch-n-manage');
    if (!core || !manage) return;

    /* joinX: x position of the vertical bracket join line.
       Each node emits a horizontal stub of JOIN_STUB px to the right before
       the vertical join segment. */
    var joinX = core.r + JOIN_STUB;

    /* pairExitY: vertical midpoint between Core's cy and MMF's cy.
       This is where the outbound horizontal bus exits the bracket join.
       Falls back to core.cy if MMF is absent. */
    var pairExitY = mmf ? (core.cy + mmf.cy) / 2 : core.cy;

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

    /* Paired-source bracket:
         Core right-mid  → horizontal stub → joinX at core.cy
         MMF  right-mid  → horizontal stub → joinX at mmf.cy
         vertical join segment from core.cy down to mmf.cy at joinX */
    if (mmf) {
      stub('M' + core.r + ',' + core.cy + ' L' + joinX + ',' + core.cy);
      stub('M' + mmf.r  + ',' + mmf.cy  + ' L' + joinX + ',' + mmf.cy);
      stub('M' + joinX  + ',' + core.cy + ' L' + joinX + ',' + mmf.cy);
    }

    /* Top-bus stub: (joinX, pairExitY) → right to the rightmost top-bus target.
       Collect all top-bus and core-manage target cx values to find the rightmost. */
    var topBusTargets = ARROWS
      .filter(function(a){ return a.type === 'top-bus' || a.type === 'core-manage'; })
      .map(function(a){ var b = box(a.to); return b ? b.cx : 0; });
    var busRight = topBusTargets.length ? Math.max.apply(null, topBusTargets) : joinX;
    stub('M' + joinX + ',' + pairExitY + ' L' + busRight + ',' + pairExitY);

    ARROWS.forEach(function (def) {
      var f = box(def.from);
      var t = box(def.to);
      if (!f || !t) return;
      var d;

      var GAP = 5; /* px gap between arrowhead tip and target box top edge */
      switch (def.type) {
        case 'top-bus':
          /* Vertical drop only — the horizontal bus is already drawn by the stub above */
          d = 'M' + t.cx + ',' + pairExitY +
              ' L' + t.cx + ',' + (t.t - GAP);
          break;

        case 'core-manage':
          /* Vertical drop only — the horizontal bus is already drawn by the stub above */
          d = 'M' + manage.cx + ',' + pairExitY +
              ' L' + manage.cx + ',' + (manage.t - GAP);
          break;

        case 'bot-bus':
          /* Manage right-mid → right to t.cx → down to t.t */
          d = 'M' + manage.r + ',' + manage.cy +
              ' L' + t.cx    + ',' + manage.cy +
              ' L' + t.cx    + ',' + (t.t - GAP);
          break;

        case 'right':
          /* Direct horizontal left-to-right: f right → t left */
          d = 'M' + f.r + ',' + f.cy +
              ' L' + (t.l - GAP) + ',' + t.cy;
          break;

        case 'left':
          /* Direct horizontal right-to-left: f left → t right (f is to the right of t). */
          d = 'M' + f.l + ',' + f.cy +
              ' L' + (t.r + GAP) + ',' + t.cy;
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

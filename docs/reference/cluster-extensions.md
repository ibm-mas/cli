# Cluster Extentions
The tables below detail the cluster extensions (ClusterResourceDefinitions, or CRDs) that will be added to a cluster as part of a Maximo Application suite install, the exact set of extensions installed will vary based on which applications & dependencies are being installed in the cluster.

## Maximo Application Suite
<table class="clusterExtensions">
  <tr><th style="width:300px">Package</th><th style="width:300px">API Group</th><th style="width:300px">Kind</th></tr>
  <tr><td rowspan="18">ibm-mas</td><td rowspan="2">core.mas.ibm.com</td><td>suite</td></tr>
  <tr><td>workspace</td></tr>
  <tr><td rowspan="11">config.mas.ibm.com</td><td>mongocfg</td></tr>
  <tr><td>kafkacfg</td></tr>
  <tr><td>jdbccfg</td></tr>
  <tr><td>smtpcfg</td></tr>
  <tr><td>idpcfg</td></tr>
  <tr><td>bascfg</td></tr>
  <tr><td>objectstoragecfg</td></tr>
  <tr><td>pushnotificationcfg</td></tr>
  <tr><td>scimcfg</td></tr>
  <tr><td>slscfg</td></tr>
  <tr><td>watsonstudiocfg</td></tr>
  <tr><td>internal.mas.ibm.com</td><td>coreidp</td></tr>
  <tr><td rowspan="4">addons.mas.ibm.com</td><td>appconnect</td></tr>
  <tr><td>humai</td></tr>
  <tr><td>mviedge</td></tr>
  <tr><td>replicadbs</td></tr>

  <tr class="alt"><td rowspan="4">ibm-mas-assist</td><td rowspan="4">apps.mas.ibm.com</td><td>assistapp</td></tr>
  <tr class="alt"><td>assistbackup</td></tr>
  <tr class="alt"><td>assistrestore</td></tr>
  <tr class="alt"><td>assistworkspace</td></tr>

  <tr><td rowspan="19">ibm-mas-iot</td><td rowspan="2">iot.ibm.com</td><td>iot</td></tr>
  <tr><td>iotworkspace</td></tr>
  <tr><td rowspan="17">components.iot.ibm.com</td><td>actions</td></tr>
  <tr><td>auth</td></tr>
  <tr><td>datapower</td></tr>
  <tr><td>devops</td></tr>
  <tr><td>dm</td></tr>
  <tr><td>dsc</td></tr>
  <tr><td>edgeconfig</td></tr>
  <tr><td>fpl</td></tr>
  <tr><td>guardian</td></tr>
  <tr><td>mbgx</td></tr>
  <tr><td>mfgx</td></tr>
  <tr><td>monitor</td></tr>
  <tr><td>orgmgmt</td></tr>
  <tr><td>provision</td></tr>
  <tr><td>registry</td></tr>
  <tr><td>state</td></tr>
  <tr><td>webui</td></tr>

  <tr class="alt"><td rowspan="13">ibm-mas-manage</td><td rowspan="13">apps.mas.ibm.com</td><td>builddatainterpreter</td></tr>
  <tr class="alt"><td>healthapp</td></tr>
  <tr class="alt"><td>healthextworkspace</td></tr>
  <tr class="alt"><td>healthworkspace</td></tr>
  <tr class="alt"><td>imagestitching</td></tr>
  <tr class="alt"><td>manageapp</td></tr>
  <tr class="alt"><td>managebuild</td></tr>
  <tr class="alt"><td>managedeployment</td></tr>
  <tr class="alt"><td>manageofflineupgraderequest</td></tr>
  <tr class="alt"><td>manageserverbundle</td></tr>
  <tr class="alt"><td>managestatuschecker</td></tr>
  <tr class="alt"><td>manageworkspace</td></tr>
  <tr class="alt"><td>opentelemetrydeployment</td></tr>

  <tr><td rowspan="2">ibm-mas-monitor</td><td rowspan="2">apps.mas.ibm.com</td><td>monitorapp</td></tr>
  <tr><td>monitorworkspace</td></tr>

  <tr class="alt"><td rowspan="2">ibm-mas-optimizer</td><td rowspan="2">apps.mas.ibm.com</td><td>optimizerapp</td></tr>
  <tr class="alt"><td>optimizerworkspace</td></tr>

  <tr><td rowspan="2">ibm-mas-predict</td><td rowspan="2">apps.mas.ibm.com</td><td>predictapp</td></tr>
  <tr><td>predictworkspace</td></tr>

  <tr class="alt"><td rowspan="2">ibm-mas-visualinspection</td><td rowspan="2">apps.mas.ibm.com</td><td>visualinspectionapp</td></tr>
  <tr class="alt"><td>visualinspectionworkspace</td></tr>

</table>

## IBM Utilities
<table class="clusterExtensions">
  <tr><th style="width:300px">Package</th><th style="width:300px">API Group</th><th style="width:300px">Kind</th></tr>

  <tr class="alt"><td rowspan="2">ibm-data-dictionary</td><td rowspan="2">asset-data-dictionary.ibm.com</td><td>assetdatadictionary</td></tr>
  <tr class="alt"><td>datadictionaryworkspace</td></tr>

  <tr><td rowspan="2">ibm-sls</td><td rowspan="2">sls.ibm.com</td><td>licenseservice</td></tr>
  <tr><td>licenseclient</td></tr>

  <tr class="alt"><td>ibm-truststore-mgr</td><td>truststore-mgr.ibm.com</td><td>truststore</td></tr>

</table>

## IBM Cloud Pak Foundational Services
<table class="clusterExtensions">
  <tr><th style="width:300px">Package</th><th style="width:300px">API Group</th><th style="width:300px">Kind</th></tr>

  <tr class="alt"><td>ibm-common-service-operator</td><td>operator.ibm.com</td><td>commonservice</td></tr>

  <tr><td>ibm-management-ingress-operator</td><td>operator.ibm.com</td><td>managementingresses</td></tr>

  <tr class="alt"><td>ibm-ingress-nginx-operator</td><td>operator.ibm.com</td><td>nginxingresses</td></tr>

  <tr><td>ibm-mongodb-operator</td><td>operator.ibm.com</td><td>mongodb</td></tr>

  <tr class="alt"><td rowspan="3">ibm-user-data-services-operator</td><td rowspan="3">uds.ibm.com</td><td>analyticsproxy</td></tr>
  <tr class="alt"><td>analyticsproxywithsubmodules</td></tr>
  <tr class="alt"><td>generatekey</td></tr>

  <tr><td rowspan="7">ibm-iam-operator</td><td rowspan="7">operator.ibm.com</td><td>authentication</td></tr>
  <tr><td>oidcclientwatcher</td></tr>
  <tr><td>pap</td></tr>
  <tr><td>policycontroller</td></tr>
  <tr><td>policydecision</td></tr>
  <tr><td>secretwatcher</td></tr>
  <tr><td>securityonboarding</td></tr>

  <tr class="alt"><td rowspan="4">operand-deployment-lifecycle-manager</td><td rowspan="4">operator.ibm.com</td><td>operandbindinginfo</td></tr>
  <tr class="alt"><td>operandconfig</td></tr>
  <tr class="alt"><td>operandregistry</td></tr>
  <tr class="alt"><td>operandrequest</td></tr>

  <tr><td rowspan="5">ibm-licensing-operator</td><td rowspan="5">operator.ibm.com</td><td>ibmlicensing</td></tr>
  <tr><td>ibmlicensingreporter</td></tr>
  <tr><td>ibmlicensingdefinition</td></tr>
  <tr><td>ibmlicensingmetadata</td></tr>
  <tr><td>ibmlicensingquerysource</td></tr>

  <tr class="alt"><td rowspan="3">ibm-commonui-operator</td><td rowspan="2">operators.ibm.com</td><td>commonwebui</td></tr>
  <tr class="alt"><td>licenseclient</td></tr>
  <tr class="alt"><td>foundation.ibm.com</td><td>navconfiguration</td></tr>

  <tr><td rowspan="9">ibm-events-operator</td><td rowspan="9">ibmevents.ibm.com</td><td>kafkabridge</td></tr>
  <tr><td>kafkaconnector</td></tr>
  <tr><td>kafkaconnect</td></tr>
  <tr><td>kafkamirrormaker</td></tr>
  <tr><td>kafkamirrormaker2</td></tr>
  <tr><td>kafkarebalance</td></tr>
  <tr><td>kafka</td></tr>
  <tr><td>kafkatopic</td></tr>
  <tr><td>kafkauser</td></tr>

  <tr class="alt"><td>ibm-platform-api-operator</td><td>operator.ibm.com</td><td>platformapi</td></tr>

  <tr><td>ibm-namespace-scope-operator</td><td>operator.ibm.com</td><td>namespacescope</td></tr>

</table>

## IBM Cloud Pak for Data
<table class="clusterExtensions">
  <tr><th style="width:300px">Package</th><th style="width:300px">API Group</th><th style="width:300px">Kind</th></tr>

  <tr class="alt"><td rowspan="17">ibm-watson-discovery-operator</td><td>oppy.ibm.com</td><td>temporarypatch</td></tr>
  <tr class="alt"><td rowspan="16">discovery.watson.ibm.com</td><td>watsondiscovery</td></tr>
  <tr class="alt"><td>watsondiscoveryapi</td></tr>
  <tr class="alt"><td>watsondiscoverycnm</td></tr>
  <tr class="alt"><td>watsondiscoverycoreapi</td></tr>
  <tr class="alt"><td>watsondiscoverydf</td></tr>
  <tr class="alt"><td>watsondiscoveryfoundation</td></tr>
  <tr class="alt"><td>watsondiscoveryhdp</td></tr>
  <tr class="alt"><td>watsondiscoveryingestion</td></tr>
  <tr class="alt"><td>watsondiscoverymigration</td></tr>
  <tr class="alt"><td>watsondiscoveryorchestrator</td></tr>
  <tr class="alt"><td>watsondiscoveryquery</td></tr>
  <tr class="alt"><td>watsondiscoverysdu</td></tr>
  <tr class="alt"><td>watsondiscoverystatelessapi</td></tr>
  <tr class="alt"><td>watsondiscoverytooling</td></tr>
  <tr class="alt"><td>watsondiscoverywire</td></tr>
  <tr class="alt"><td>watsondiscoverywksml</td></tr>

  <tr><td rowspan="2">ibm-model-train-operator</td><td rowspan="2">modeltrain.ibm.com</td><td>modeltrain</td></tr>
  <tr><td>modeltraindynamicworkflow</td></tr>

  <tr class="alt"><td rowspan="2">ibm-zen-operator</td><td rowspan="2">zen.cpd.ibm.com</td><td>zenservice</td></tr>
  <tr class="alt"><td>zenextension</td></tr>

  <tr><td rowspan="2">ibm-ca-operator</td><td rowspan="2">ca.cpd.ibm.com</td><td>caserviceinstance</td></tr>
  <tr><td>caservice</td></tr>

  <tr class="alt"><td>ibm-minio-operator</td><td>minio.opencontent.ibm.com</td><td>miniocluster</td></tr>

  <tr><td>ibm-rabbitmq-operator</td><td>rabbitmq.opencontent.ibm.com</td><td>rabbitmqcluster</td></tr>

  <tr class="alt"><td>ibm-elasticsearch-operator</td><td>elasticsearch.opencontent.ibm.com</td><td>elasticsearchcluster</td></tr>

  <tr><td>ibm-etcd-operator</td><td>etcd.database.coreos.com</td><td>etcdcluster</td></tr>

  <tr class="alt"><td>ibm-cpd-ws-runtimes</td><td>ws.cpd.ibm.com</td><td>notebookruntime</td></tr>

  <tr><td>ibm-cpd-wsl</td><td>ws.cpd.ibm.com</td><td>ws</td></tr>

  <tr class="alt"><td>ibm-cpd-wos</td><td>wos.cpd.ibm.com</td><td>woservice</td></tr>

  <tr><td>ibm-cps-ae</td><td>ae.cpd.ibm.com</td><td>analyticsengine</td></tr>

  <tr class="alt"><td>ibm-cpd-datarefinery</td><td>datarefinery.cpd.ibm.com</td><td>datarefinery</td></tr>

  <tr><td>ibm-cpd-spss</td><td>spssmodeler.cpd.ibm.com</td><td>spss</td></tr>

  <tr class="alt"><td>ibm-cpd-wml-operator</td><td>wml.cpd.ibm.com</td><td>wmlbase</td></tr>

  <tr><td>cpd-platform-operator</td><td>cpd.ibm.com</td><td>ibmcpd</td></tr>

  <tr class="alt"><td>ibm-watson-gateway-operator</td><td>watson-gateway.watson.ibm.com</td><td>watsongateway</td></tr>

  <tr><td rowspan="2">ibm-cpd-ccs</td><td>runtimes.ibm.com</td><td>runtimeassembly</td></tr>
  <tr><td>ccs.cpd.ibm.com</td><td>ccs</td></tr>

</table>

## IBM Db2 Universal Operator
<table class="clusterExtensions">
  <tr><th style="width:300px">Package</th><th style="width:300px">API Group</th><th style="width:300px">Kind</th></tr>
  <tr><td rowspan="11">db2u-operator</td><td rowspan="8">db2u.databases.ibm.com</td><td>bigsql</td></tr>
  <tr><td>db2ucluster</td></tr>
  <tr><td>db2uengine</td></tr>
  <tr><td>db2uhadr</td></tr>
  <tr><td>db2uhelmmigration</td></tr>
  <tr><td>db2uinstance</td></tr>
  <tr><td>formationlock</td></tr>
  <tr><td>formation</td></tr>
  <tr><td rowspan="3">db2ubnr.databases.ibm.com</td><td>db2ubackup</td></tr>
  <tr><td>db2ulogstream</td></tr>
  <tr><td>db2urestore</td></tr>
</table>

## IBM AppConnect
<table class="clusterExtensions">
  <tr><th style="width:300px">Package</th><th style="width:300px">API Group</th><th style="width:300px">Kind</th></tr>
  <tr><td rowspan="8">ibm-appconnect</td><td rowspan="8">appconnect.ibm.com</td><td>configuration</td></tr>
  <tr><td>dashboard</td></tr>
  <tr><td>designerauthorings</td></tr>
  <tr><td>integrationflows</td></tr>
  <tr><td>integrationruntimes</td></tr>
  <tr><td>integrationservers</td></tr>
  <tr><td>switchservers</td></tr>
  <tr><td>traces</td></tr>
</table>

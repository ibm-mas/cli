mas.devops
----------

Example
=======

.. code:: python

   from openshift import dynamic
   from kubernetes import config
   from kubernetes.client import api_client

   from mas.devops.ocp import createNamespace
   from mas.devops.tekton import installOpenShiftPipelines, updateTektonDefinitions, launchUpgradePipeline

   instanceId = "mymas"
   pipelinesNamespace = f"mas-{instanceId}-pipelines"

   # Create an OpenShift client
   dynClient = dynamic.DynamicClient(
       api_client.ApiClient(configuration=config.load_kube_config())
   )

   # Install OpenShift Pipelines Operator
   success = installOpenShiftPipelines(dynamicClient)
   assert success is True

   # Create the pipelines namespace and install the MAS tekton definitions
   createNamespace(dynamicClient, pipelinesNamespace)
   updateTektonDefinitions(pipelinesNamespace)

   # Launch the upgrade pipeline and print the URL to view the pipeline run
   pipelineURL = launchUpgradePipeline(self.dynamicClient, instanceId)
   print(pipelineURL)

Uninstall
===============================================================================

Uninstall Overview
-------------------------------------------------------------------------------
Uninstall will remove an entire MAS installation from a cluster, including all installed applications.

1 Uninstall Maximo Application Suite
-------------------------------------------------------------------------------
Run `mas uninstall` and select the MAS installation instance that you want to uninstall.

```bash
mas uninstall
```

The command can also be ran non-interactive.

```bash
mas uninstall -i @@MAS_INSTANCE@@ --no-confirm
```

The command can be ran in a prebuilt CLI docker container.

```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas uninstall
```

Note: If you are not already connected to an OpenShift cluster you will be prompted to provide the server URL & token, and whether to verify the server certificate or not,  If you are already connected to a cluster you will be given the option to change to another cluster.


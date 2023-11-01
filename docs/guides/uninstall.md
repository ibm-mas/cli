Uninstall
===============================================================================

Uninstall Overview
-------------------------------------------------------------------------------
Uninstall will remove an entire MAS installation from a cluster, including all installed applications.

1 Uninstall Maximo Application Suite
-------------------------------------------------------------------------------
Run `mas uninstall` and select the MAS installation instance that you want to uninstall.

```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas uninstall
```


The command can also be ran non-interactive.

```bash
mas uninstall -i @@MAS_INSTANCE@@ --no-confirm
```

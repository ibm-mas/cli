Choosing the Right Catalog
===============================================================================

!!! important
    In all cases we **strongly discourage the use of manual update approval strategy for operator subscriptions**.  In our experience it leads to overly complicated updates requiring significant administrative effort when taking into account the range of operators running in a cluster across numerous namespaces. **If you desire control over when updates are introduced to your cluster, we highly recommend the use of our static operator catalogs.** This not only provides more control but also allows for the use of [`mas update`](./update.md) to manage MAS and update MAS dependencies.

Automatic Updates
-------------------------------------------------------------------------------
- Goal: I want to receive updates automatically as soon as they are available
- Solution: Use the **dynamic catalogs and automatic update approval strategy**

The content in this catalog is updated regularly. Multiple installations at different times will not necessarily be identical because package updates are being delivered to the channels.

- Only security updates and bug fixes will be delivered this way (software updates).
- Software upgrades require the user to explicitly change a subscription channel.
- Automatic updates delivered do not include updates to MAS dependencies and hence have to be done manually.

User-Controlled Updates
-------------------------------------------------------------------------------
- Goal: I want to control when updates are introduced into my cluster
- Solution: Use the **static catalogs and automatic update approval strategy**

The packages available in these catalogs are fixed. Multiple installations at different times will always result in exactly the same version of all operators being installed.

When you are ready to apply updates you simply modify the CatalogSource installed in your cluster, changing it from e.g. `@@MAS_PREVIOUS_CATALOG@@` to `@@MAS_LATEST_CATALOG@@`.  No further action is required, after a brief delay all installed operators will update automatically to the latest versions in the new catalog source.


Multi-Cluster Version Equivalency
-------------------------------------------------------------------------------
- Goal: I want to maintain **exact** version alignment across multiple OpenShift clusters, for instance in a development, staging, production setup
- Solution: Use the **static catalogs and automatic update approval strategy**

The packages available in these catalogs are fixed. Multiple installations at different times will always result in exactly the same version of all operators being installed.  By choosing the same static catalog across multiple clusters the customer will be guaranteed that their installations are identical, right down to the patch level of the operators installed.  Updates can be rolled out in a controlled manner, and the upgrade path between two catalog versions will always be identical regardless of how much time passes between upgrades in different cluster.


Disconnected Install
-------------------------------------------------------------------------------
- Goal: I want to run a disconnected environment using a private mirror registry
- Solution: Use the **static catalogs and automatic approval strategy**

The MAS CLI `mirror-images` command accepts the name of a static catalog to control what is mirrored to your registry, it will mirror all of the necessary images for the latest version of each package in that catalog are mirrored to your private registry.  Once the images are mirrored simply run the `configure-mirror` command to install the IBM Maximo Application Suite ImageContentSourcePolicy, and the rest of your installation experience is identical to a connected environment.

!!! important
    To apply updates in a disconnected cluster, run the `mirror-images` command with the name of the new static catalog you wish to update to **before** updating the CatalogSource in your cluster

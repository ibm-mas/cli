Migration from EAM 7 to MAS 9
===============================================================================

This example demonstrates how to migrate from EAM 7 to Maximo Manage v9 running on [Red Hat OpenShift on IBM Cloud](https://www.ibm.com/products/openshift) (ROKS).

- For this demo we are using an existing database instance that is configured without TLS enabled (so we do not need to worry about providing the certificates in the configuration)
- Normally you would take a backup of the database and use that, but for the purpose of this example we are going to take over the database currently in use, if you wish to follow this example using a restored backup of your database simply skip step 2.


Prerequisites
-------------------------------------------------------------------------------

**1 An IBMCloud API Key**

- Login in your IBM Cloud account
- Go to **Manage** menu and select **Access (IAM)**
- Go to **API keys** menu, click **Create an IBM Cloud API key**
- Enter a name and description for your API Key and click **Create**

**2 A MAS License File**

Access [IBM License Key Center](https://licensing.flexnetoperations.com/), on the **Get Keys** menu select **IBM AppPoint Suites**. Select **IBM MAXIMO APPLICATION SUITE AppPOINT LIC** and on the next page fill in the information as below:

| Field          | Content |
| -------------- | ------- |
| Number of Keys | How many AppPoints to assign to the license file |
| Host ID Type   | Set to Ethernet Address |
| Host ID        | Enter any 12 digit hexadecimal string |
| Hostname       | Set to the hostname of your OCP instance, but this can be any value really |
| Port           | Set to 27000 |

Create a new folder `mas9demo` in your home directory and save this file there as `~/mas9demo/entitlement.lic`

**3 An IBM Entitlement Key**

Access [IBM Container Software Library](https://myibm.ibm.com/products-services/containerlibrary) using your IBMId to obtain your entitlement key.


Step 1 - Provision OpenShift
-------------------------------------------------------------------------------
We are going to provision the cluster using **Red Hat OpenShift on IBM Cloud** via the MAS CLI container image.  Ensure that you set the `IBMCLOUD_APIKEY` environment variable to the key you obtained from the [IBM Container Software Library](https://myibm.ibm.com/products-services/containerlibrary).


```bash
export IBMCLOUD_APIKEY=x

docker run -e IBMCLOUD_APIKEY -ti --rm -v ~:/mnt/home --pull always quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ \
  mas provision-roks -r mas-development -c mas9demo -v 4.14_openshift \
  --worker-count 3 --worker-flavor b3c.8x32 --worker-zone lon02 \
  --no-confirm
```

This will provision an OpenShift cluster with three 8x32 worker nodes. It will take approximately **1 hour** to provision the cluster.

!!! note
    At time of writing the cost of this three node OpenShift cluster on IBMCloud is $1.61 per hour (which works out as just under $1'200 per month).  Billing is hourly and to complete this example we will only need the cluster for a few hours; the entire demo can be complete on IBMCloud for as little as $10.


Step 2 - Backup Database
-------------------------------------------------------------------------------
We must stop EAM because we are going to create a backup of it's database; log into the WebSphere administrative console and stop the servers.

![Shutdown EAM in the WebSphere Application Server administrative console](images/shutdown_eam.png)


Step 3 - Create new Database
-------------------------------------------------------------------------------
TODO: Write me


Step 4 - Prepare the JDBCCfg
-------------------------------------------------------------------------------
IBM Maximo Application Suite (MAS) configuration is held in Kubernetes resources, when we install MAS we will tell the installer to apply this configuration as part of the installation.

```yaml
---
apiVersion: v1
kind: Secret
type: Opaque
metadata:
  name: "jdbc-demo-credentials"
  namespace: "mas-dev-core"
stringData:
  username: "{DB_USERNAME}"
  password: "{DB_PASSWORD}"
---
apiVersion: config.mas.ibm.com/v1
kind: JdbcCfg
metadata:
  name: "dev-jdbc-wsapp-demo-manage"
  namespace: "mas-dev-core"
  labels:
    "mas.ibm.com/configScope": "workspace-application"
    "mas.ibm.com/instanceId": "dev"
    "mas.ibm.com/workspaceId": "demo"
    "mas.ibm.com/applicationId": "manage"
spec:
  displayName: "JDBC (IBM Db2)"
  config:
    url: "{JDBC_URL}"
    sslEnabled: false
    credentials:
      secretName: "jdbc-demo-credentials"
```

Replace `{JDBC_URL}`, `{DB_USERNAME}`, and `{DB_PASSWORD}` with the actual values for your database, for example:

- **JDBC_URL** = `jdbc:db2://1.2.3.4:50005/maxdb76:sslConnection=false;`
- **DB_USERNAME** = `maximo`
- **DB_PASSWORD** = `maximo`

Save this file into the same directory where we saved the MAS entitlement file, as `~/mas9demo/mas9demo-jdbc.yaml`

Validate that the JDBC URL and username/password are correct by running the command `SELECT VARNAME, VARVALUE FROM MAXIMO.MAXVARS WHERE VARNAME='MAXUPG';`, which will confirm the database is currently running at version 7.

![Using DBeaver to view the MAXUPG value in the Maximo database](images/dbeaver.png)


Step 5 - Prepare the SMTPCfg
-------------------------------------------------------------------------------
When existing users are migrated into MAS a new password will be generated for each, to recieve this password we must configure SMTP for MAS.  If you don't have your own SMTP server, and do have a [Gmail](https://mail.google.com/mail/) account then can configure MAS as below:

```yaml
---
apiVersion: v1
kind: Secret
type: Opaque
metadata:
  name: "smtp-demo-credentials"
  namespace: "mas-dev-core"
stringData:
  username: "{GMAIL_ADDRESS}"
  password: "{GMAIL_PASSWORD}"
---
apiVersion: config.mas.ibm.com/v1
kind: SmtpCfg
metadata:
  name: "dev-smtp-system"
  namespace: "mas-dev-core"
  labels:
    "mas.ibm.com/configScope": "system"
    "mas.ibm.com/instanceId": "dev"
spec:
  displayName: "SMTP (Gmail)"
  config:
    hostname: smtp.gmail.com
    port: 587
    security: SSL
    authentication: true
    defaultSenderEmail: "{GMAIL_ADDRESS}"
    defaultSenderName: "IBM Maximo Application Suite (Do Not Respond)"
    defaultRecipientEmail: "{GMAIL_ADDRESS}"
    defaultShouldEmailPasswords: true
    credentials:
      secretName: "smtp-demo-credentials"
```

Save this file into the same directory where we saved the MAS entitlement file, as `~/mas9demo/mas9demo-smtp.yaml`


Step 6 - Install MAS
-------------------------------------------------------------------------------
Ensure the following environment variables are all set:

- `IBMCLOUD_APIKEY` (see [prerequisites](#prerequisites))
- `SUPERUSER_PASSWORD` (choose the password for the MAS superuser account)
- `IBM_ENTITLEMENT_KEY` (see [prerequisites](#prerequisites))

We will install MAS in **non-production mode**, with an instance ID of `dev` and a workspace ID of `demo` using the latest (at time of writing) catalog update.

!!! note
    When we launch the CLI container we are mounting your home directory into the container image, this is how the installer will access the `entitlement.lic` and `mas9demo-jdbc.yaml` files that you created earlier.

```bash
export IBMCLOUD_APIKEY=x
export SUPERUSER_PASSWORD=x
export IBM_ENTITLEMENT_KEY=x

docker run -e IBMCLOUD_APIKEY -ti --rm -v ~:/mnt/home --pull always quay.io/ibmmas/cli:@@CLI_LATEST_VERSION@@ bash -c "
  CLUSTER_TYPE=roks CLUSTER_NAME=mas9demo ROLE_NAME=ocp_login ansible-playbook ibm.mas_devops.run_role &&
  mas install \
  --non-prod \
  --mas-instance-id dev \
  --mas-workspace-id demo \
  --mas-workspace-name 'EAM Migration Demo' \
  --mas-catalog-version @@MAS_LATEST_CATALOG@@ \
  --mas-channel @@MAS_LATEST_CHANNEL@@ \
  --manage-channel @@MAS_LATEST_CHANNEL_MANAGE@@ \
  --manage-jdbc workspace-application \
  --manage-components base=latest \
  --additional-configs /mnt/home/mas9demo \
  --license-file /mnt/home/mas9demo/entitlement.lic \
  --uds-email parkerda@uk.ibm.com \
  --uds-firstname David \
  --uds-lastname Parker \
  --storage-class-rwo ibmc-block-gold \
  --storage-class-rwx ibmc-file-gold-gid \
  --storage-pipeline ibmc-file-gold-gid \
  --storage-accessmode ReadWriteMany \
  --superuser-username superuser \
  --superuser-password '$SUPERUSER_PASSWORD' \
  --ibm-entitlement-key '$IBM_ENTITLEMENT_KEY' \
  --accept-license \
  --no-confirm
"
```

The install itself is performed on the cluster, the CLI merely prepares the installation pipeline, you will be presented with a URL to view the install pipeline in the OpenShift Console.

!!! tip
    You can either monitor the install in the OpenShift Console or go get lunch, the install will take approximately 2-3 hours depending on network conditions.

![Tekon Pipeline for Maximo Application Suite installation](images/install-pipeline.png)

Once the installation has completed you will be able to log into Maximo Application Suite & Maximo Manage using any user from the original EAM, for convenience the installer adds a link to the Maximo Application Suite Administrator Dashboard to the OpenShift Console's **Application Menu**, and we can log into MAS using the superuser username and password supplied during install:

![Application Menu extension in the OpenShift Console for Maximo Application Suite](images/dashboard-link.png)

!!! note
    In this demo we have not configured integration to an SMTP server, as a result we must manually set a new password for the migrated users (including **maxadmin**) before they can be used.

    If e-mail services are enabled during the MAS install then a new password would be generated automatically for each migrated user and a welcome e-mail containing their new Maximo Application Suite password would be sent.

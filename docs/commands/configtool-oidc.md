Manage OpenID client for Configuration Tool
===============================================================================

Overview
-------------------------------------------------------------------------------
Configuration Tool can be used to configure and customize MAS apps through OIDC authentication since MAS 8.10.  
This quick guide is as a reference for customer administrator to register/unregister/update OIDC client for this tool.  

Usage
-------------------------------------------------------------------------------
`mas oidc [register|unregister|update|-h|--help] [options]`

### Cluster Credentials (Required):
- `-t|--token CLUSTER_TOKEN`                     Cluster's token
- `-s|--server CLUSTER_SERVER`                   Cluster server

### MAS OIDC Information (Required):
- `-m|--mas-home MAS_HOME`                      MAS Home Url
- `-p|--ui-prefix TRUST_UI_PREFIX`              Trust UI prefix to receive OIDC callback
- `-i|--instance-id`                            MAS Instance id specified if not derived from MAS_HOME url (Optional)

Examples
-------------------------------------------------------------------------------
### Interactive Mode
```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas oidc register
```

### Non-Interactive Mode
```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas oidc register \
  -t sha256~dOnviPZtgCfJqUfUFLiSlsmXjzxtXpedhdxyXZ0F0X4 -s https://c118-e.us-south.containers.cloud.ibm.com:30221 \
  -m masdev.home.mobfound1.masdev.suite.maximo.com -p "http://localhost:3000, http://localhost:3001" -i "mobfnd"
```
```bash
export CLUSTER_TOKEN=sha256~COA8-2Hd6G45rUN0HZLLh47sFByoX8QCC8j92jWB3to  
export CLUSTER_SERVER=https://c130-e.us-south.containers.cloud.ibm.com:32250
export MAS_HOME=masdev.home.mobfound1.masdev.suite.maximo.com  
export TRUST_UI_PREFIX="http://localhost:3000, http://localhost:3001"
export MAS_INSTANCE_ID=mobfnd
docker run -ti --rm --pull always quay.io/ibmmas/cli mas oidc register \
  -t $CLUSTER_TOKEN -s $CLUSTER_SERVEr -m $MAS_HOME -p $TRUEST_UI_PREFIX -i $MAS_INSTANCE_ID
```

Appendix
-------------------------------------------------------------------------------
### 1. Cluster Credentials.  
Log in to your cluster with your IBMid by using the following method, browse to the OpenShift web console. 
From the dropdown menu in the upper right of the page, click Copy Login Command.  
example: `oc login --token=sha256~COA8-2Hd6G45rUN0HZLLh47sFByoX8QCC8j92jWB3to --server=https://c130-e.us-south.containers.cloud.ibm.com:32250`    
   
- CLUSTER_TOKEN=sha256~COA8-2Hd6G45rUN0HZLLh47sFByoX8QCC8j92jWB3to  
- CLUSTER_SERVER=https://c130-e.us-south.containers.cloud.ibm.com:32250    

### 2. MAS OIDC Information
- MAS_HOME=main.home.ivt15rel89.ivt.suite.maximo.com
- TRUST_UI_PREFIX="http://localhost:3000, http://localhost:3001"
- MAS_INSTANCE_ID=ivt15xx
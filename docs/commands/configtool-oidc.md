Manage OpenID client for Configration Tool
===============================================================================

Overview
-------------------------------------------------------------------------------
Configuration Tool can be used to configure and customize MAS apps through OIDC authentication since MAS 8.10.  
This quick guide is as a reference for customer admininstrator to register/unregister/update OIDC client for this tool.  
At present, script is not integrated into mas command line.

Pre-reqs
-------------------------------------------------------------------------------
### 1. Connect to MAS Cluster via CLI.  
Log in to your cluster with your IBMid by using the following method, browse to the OpenShift web console. 
From the dropdown menu in the upper right of the page, click Copy Login Command. Paste the copied command in your local terminal.  
For example: `oc login --token=sha256~COA8-2Hd6G45rUN0HZLLh47sFByoX8QCC8j92jWB3to --server=https://c130-e.us-south.containers.cloud.ibm.com:32250`  

### 2. Provide MAS home URL
- `export MAS_HOME=[mas_home]`
- example: `main.home.ivt15rel89.ivt.suite.maximo.com`

### 3. Copy Shell Script
Choose a local folder for example `/opt/configtool/`, copy below code snippet to a new script file `configtool-oidc`.  
Make sure this script executable, for reference to use `chmod 777 configtool-oidc`.
```
#!/bin/bash
#instance name and domain
echo preparing for $MAS_HOME...
if [[ -z $MAS_HOME ]]; then
    echo "MAS_HOME must be provided and not empty. sample: export MAS_HOME=\"masdev.home.mobfound1.masdev.suite.maximo.com\""
    exit 0
fi
MAS_PARTS=(`echo $MAS_HOME | tr "." " "`)
DOT="."
DOMAIN_SUFFIX=""
i=1
for ELE in "${MAS_PARTS[@]}"
do
    if [[ $i -eq 3 ]]; then
        INSTANCE_NAME=$ELE
    fi
    if [[ $i -gt 3 && $i -lt ${#MAS_PARTS[@]} ]]; then
        DOMAIN_SUFFIX+=$ELE$DOT
    elif [[ $i -eq ${#MAS_PARTS[@]} ]]; then
        DOMAIN_SUFFIX+=$ELE
    fi
    i=$((i + 1))
done
if [[ $i -lt 4 ]]; then
    echo "MAS_HOME is incorrect. sample: \"masdev.home.mobfound1.masdev.suite.maximo.com\""
    exit 0
fi

#OAUTH information
CLIENT_CONFIGTOOL="configtoolpkce"
OAUTH_URL="https://auth.$INSTANCE_NAME.$DOMAIN_SUFFIX/oidc/endpoint/MaximoAppSuite/registration"
OAUTH_URL_CONFIGTOOL="$OAUTH_URL/$CLIENT_CONFIGTOOL"
LOGOUT_URL="https://auth.$INSTANCE_NAME.$DOMAIN_SUFFIX/oidc/endpoint/MaximoAppSuite/logout"

oc project mas-${INSTANCE_NAME}-core
OAUTH_ADMIN_USERNAME=`oc get secret ${INSTANCE_NAME}-credentials-oauth-admin -o jsonpath="{.data['oauth-admin-username']}" | base64 -d`
OAUTH_ADMIN_PWD=`oc get secret ${INSTANCE_NAME}-credentials-oauth-admin -o jsonpath="{.data['oauth-admin-password']}" | base64 -d`

#unregister
echo checking if $CLIENT_CONFIGTOOL existed
status_code=`curl -w %{http_code} -s -o /dev/null -I --user $OAUTH_ADMIN_USERNAME:$OAUTH_ADMIN_PWD -H 'Content-Type: application/json' $OAUTH_URL_CONFIGTOOL`
echo "status_code: $status_code"
echo running $1
if [[ "$status_code" -eq 200 ]] ; then
    curl -w %{http_code} -s -o /dev/null -I --user $OAUTH_ADMIN_USERNAME:$OAUTH_ADMIN_PWD -H 'Content-Type: application/json' -X DELETE $OAUTH_URL_CONFIGTOOL
    if [[ "$1" == "unregister" ]]; then
        echo "$1" Client $CLIENT_CONFIGTOOL.
        exit 0
    fi
elif [[ "$status_code" -eq 404 ]] ; then
    if [[ "$1" == "unregister" ]]; then
        echo Client $CLIENT_CONFIGTOOL NOT FOUND, no need "$1".
        exit 0
    fi
else
    echo Some issue occurred in MAS OIDC server. Please try again later.
    exit 0
fi

#trust ui prefix
echo TRUST_UI_PREFIX: $TRUST_UI_PREFIX
if [[ -z $TRUST_UI_PREFIX ]]; then
    echo "TRUST_UI_PREFIX must be provided and not empty. sample: export TRUST_UI_PREFIX=\"http://localhost:3000,http://localhost:3001\""
    exit 0
fi
TRUST_UI_PARTS=(`echo $TRUST_UI_PREFIX | tr "," " "`)
if [[ ${#TRUST_UI_PARTS[@]} -eq 0 ]]; then
    echo "TRUST_UI_PREFIX is empty, at least define one URL. \"http://localhost:3000\""
    exit 0
fi
CALLBACK="/auth/callback"
TRUST_UIS="["
REDIRECT_UIS="["
j=1
for ELE in "${TRUST_UI_PARTS[@]}"
do
    if [[ j -lt ${#TRUST_UI_PARTS[@]} ]]; then
        TRUST_UIS+="\""$ELE"\","
        REDIRECT_UIS+="\""$ELE$CALLBACK"\","
    else
        TRUST_UIS+="\""$ELE"\""
        REDIRECT_UIS+="\""$ELE$CALLBACK"\""
    fi
    j=$((j + 1))
done 
TRUST_UIS+="]"
REDIRECT_UIS+="]"

#register or update (the same as register)
if [[ "$1" == "register" || "$1" == "update" ]]; then
    echo "$1" Client $CLIENT_CONFIGTOOL.
    curl --user $OAUTH_ADMIN_USERNAME:$OAUTH_ADMIN_PWD \
    -H 'Accept: application/json' \
    -H 'Content-type: application/json' \
    -X POST $OAUTH_URL \
    -d @<(cat <<EOF
{
  "client_id": "$CLIENT_CONFIGTOOL",
  "publicClient": true,
  "proofKeyForCodeExchange": true,
  "token_endpoint_auth_method":"client_secret_basic",
  "scope":"openid profile email general",
  "grant_types":[
      "authorization_code",
      "client_credentials",
      "implicit",
      "refresh_token",
      "urn:ietf:params:oauth:grant-type:jwt-bearer"
  ],
  "response_types":[
      "code",
      "token",
      "id_token token"
  ],
  "application_type":"web",
  "subject_type":"public",
  "post_logout_redirect_uris": ["$LOGOUT_URL"],
  "preauthorized_scope":"openid profile email general",
  "introspect_tokens": true,
  "trusted_uri_prefixes": $TRUST_UIS,
  "redirect_uris": $REDIRECT_UIS
}
EOF
)
```

Usage
-------------------------------------------------------------------------------

### Register OIDC client
If client ever registered, it will be deleted firstly.  
- `export TRUST_UI_PREFIX="['http://localhost:3000', 'http://localhost:3001']"`  
```
configtool-oidc register
```

### Update OIDC client
So far onlyh trust ui prefix is supported to update. Same as register command.  
- `export TRUST_UI_PREFIX="['http://192.168.0.2:3000', 'http://192.168.0.2:3001']"`  
```
configtool-oidc update
```

### Unregister OIDC client
```
configtool-oidc unregister
```

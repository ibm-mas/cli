#!/bin/bash
# -----------------------------------------------------------
# Licensed Materials - Property of IBM
# 5737-M66, 5900-AAA
# (C) Copyright IBM Corp. 2023 All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication, or disclosure
# restricted by GSA ADP Schedule Contract with IBM Corp.
# -----------------------------------------------------------


function backupSingleResource {
    RESOURCE_KIND=$1
    RESOURCE_NAME=$2
	NAMESPACE=$3
    
    echo "Backing up $RESOURCE_KIND/$RESOURCE_NAME in the $NAMESPACE namespace..."
    echo "Saving $RESOURCE_KIND/$RESOURCE_NAME to $BACKUP_FOLDER/$RESOURCE_KIND-$RESOURCE_NAME.yaml"
    oc get $RESOURCE_KIND  $RESOURCE_NAME -n $NAMESPACE -o yaml | yq 'del(.metadata.creationTimestamp, .metadata.ownerReferences, .metadata.generation,  .metadata.resourceVersion, .metadata.uid, .metadata.annotations["kubectl.kubernetes.io/last-applied-configuration"], .status)' >  $BACKUP_FOLDER/$RESOURCE_KIND-$RESOURCE_NAME.yaml
}

function backupResources {
    RESOURCES=$1
	NAMESPACE=$2

    echo "Backing up all $RESOURCES resources in the $MAS_MANAGE_NAMESPACE namespace..."
    
    numberOfItems=`(oc get $RESOURCES -n $NAMESPACE -o yaml | yq '.items | length')`
    
    for (( i = 0; i < $numberOfItems; i++ ))
    do
        resourceYaml=`(oc get $RESOURCES  -n $NAMESPACE -o yaml | yq .items[$i])`
        resourceKind=`(echo "$resourceYaml" | yq .kind)`
        resourceName=`(echo "$resourceYaml" | yq .metadata.name)`
        specYaml=`(echo "$resourceYaml" | yq .spec)`
		
	secretList=`(echo "$specYaml" | yq '[.. | select(has("secretName"))]')`
	echo "secretList are $secretList"
	numberOfSecrets=`(echo "$secretList" | yq 'length')`
	for (( j = 0; j < $numberOfSecrets; j++ ))
	do
	    secretName=`(echo "$secretList" | yq .[$j].secretName)`
	    echo "secret $secret"
	    backupSingleResource Secret $secretName $NAMESPACE
	done

        echo "Saving "$resourceKind" named $resourceName to $BACKUP_FOLDER/$resourceKind-$resourceName.yaml"
        echo "$resourceYaml" |  yq 'del(.metadata.creationTimestamp, .metadata.ownerReferences, .metadata.generation,  .metadata.resourceVersion, .metadata.uid, .metadata.annotations["kubectl.kubernetes.io/last-applied-configuration"], .status)' >  $BACKUP_FOLDER/$resourceKind-$resourceName.yaml
    done
}

function checkForManualCertMgmt {

    echo "Determining if Manual Certificate Management is enabled..."
    
    suiteYaml=`(oc get Suite  $MAS_INSTANCE_ID -n $MAS_CORE_NAMESPACE -o yaml)`
    hasCertMgmt=`(echo "$suiteYaml" |  yq '.spec.settings | has("manualCertMgmt")')`
    
    if [ "$hasCertMgmt" == "true" ]; then
        hasCertMgmtValue=`(echo "$suiteYaml" | yq .spec.settings.manualCertMgmt)`
        if [ "$hasCertMgmtValue" == "true" ]; then
            backupSingleResource Secret $MAS_INSTANCE_ID-$MAS_WORKSPACE_ID-cert-public-81
        fi
    fi

}


# =============================================================================
# MAS Manage Namespace Backup and Restore
# =============================================================================
# Process command line arguments
while [[ $# -gt 0 ]]
do
    key="$1"
    shift
    case $key in
        -w|--mas-workspace-id)
        MAS_WORKSPACE_ID=$1
        shift
        ;;

        -i|--mas-instance-id)
        MAS_INSTANCE_ID=$1
        shift
        ;;

        -f|--backup-folder)
        BACKUP_FOLDER=$1
        shift
        ;;	

        -m|--mode)
        MODE=$1
        shift
        ;;

        -h|--help)
        echo "IBM Maximo Application Suite ManageNamespace Backup and Restore "
        echo "---------------------------------------------------------------"
        echo "  mas-backup-restore.sh -i MAS_INSTANCE_ID -f BACKUP_FOLDER -m backup|restore"
        echo ""
        echo "Example usage: "
        echo "  mas-backup-restore.sh -i dev -f ./ -m backup"
        echo "  mas-backup-restore.sh -i dev -f ./ -m restore"
        echo ""
        echo "  -w, --mas-workspace-id  The Manage workspace id that should be backed up or restored to"
        echo "  -i, --mas-instance-id   The MAS instance id that should be backed up or restored to"
        echo "  -f, --backup-folder     The folder where backup artifacts should be written to or read from"
        echo "  -m, --mode              Whether to backup or restore. Valid values are backup or restore"
        echo ""
        exit 0
        ;;

        *)
        # unknown option
        echo -e "\nUsage Error: Unsupported flag \"${key}\"\n\n"
        exit 1
        ;;
    esac
done

: ${MAS_WORKSPACE_ID?"Need to set -w|--mas-workspace-id argument argument"}
: ${MAS_INSTANCE_ID?"Need to set -i|--mas-instance-id argument argument"}
: ${BACKUP_FOLDER?"Need to set -f|--backup-folder argument"}
: ${MODE?"Need to set -m|--mode argument backup|restore"}

MAS_MANAGE_NAMESPACE=mas-$MAS_INSTANCE_ID-manage
MAS_CORE_NAMESPACE=mas-$MAS_INSTANCE_ID-core

# 2. Pre-req checks
# -----------------------------------------------------------------------------
command -v oc >/dev/null 2>&1 || { echo >&2 "Required executable \"oc\" not found on PATH.  Aborting."; exit 1; }
command -v yq >/dev/null 2>&1 || { echo >&2 "Required executable \"yq\" not found on PATH.  Aborting."; exit 1; }


oc whoami &> /dev/null
if [[ "$?" == "1" ]]; then
  echo "You must be logged in to your OpenShift cluster to proceed (oc login)"
  exit 1
fi

if [ "$MODE" == "backup" ]; then
    echo "Starting MAS Managebackup using the instance id $MAS_INSTANCE_ID to $BACKUP_FOLDER"
    mkdir -p $BACKUP_FOLDER
    backupSingleResource Subscription ibm-mas-manage $MAS_MANAGE_NAMESPACE
    OPERATOR_GROUP=$(oc get operatorgroup -n mas-$MAS_INSTANCE_ID-manage)
    echo "OPERATOR_GROUP $OPERATOR_GROUP"
    backupSingleResource OperatorGroup $OPERATOR_GROUP $MAS_MANAGE_NAMESPACE
    backupSingleResource Secret ibm-entitlement $MAS_MANAGE_NAMESPACE
    backupSingleResource Secret $MAS_WORKSPACE_ID-manage-encryptionsecret $MAS_MANAGE_NAMESPACE
    backupSingleResource Secret $MAS_WORKSPACE_ID-manage-encryptionsecret-operator $MAS_MANAGE_NAMESPACE
    backupSingleResource ManageApp $MAS_INSTANCE_ID $MAS_MANAGE_NAMESPACE
    backupResources ManageWorkspace $MAS_MANAGE_NAMESPACE
    backupResources jdbccfgs $MAS_CORE_NAMESPACE 
    checkForManualCertMgmt
elif [ "$MODE" == "restore" ]; then
     echo "Starting MAS Managerestore of theinstance id $MAS_INSTANCE_ID from $BACKUP_FOLDER"
    if [ -d "$BACKUP_FOLDER" ]; then
        oc new-project $MAS_MANAGE_NAMESPACE
        for yamlFile in $BACKUP_FOLDER/*.yaml; do
            echo "Applying recouce from $yamlFile"
            oc apply -f $yamlFile
        done
    else 
        echo "MAS Managerestore cannot complete. The folder $BACKUP_FOLDER does not exist."
    fi
else
    echo "Unknown mode $MODE specified. Valid values for mode are backup or restore."
fi



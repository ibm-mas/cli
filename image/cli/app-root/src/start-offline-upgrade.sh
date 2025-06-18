#!/usr/bin/env bash

set -e

echo
echo "================================================================================"
echo "Check if we need to set the ManageOfflineUpgradeRequest stage to Requested"
echo "================================================================================"
echo

MAS_APP_NAMESPACE=mas-${MAS_INSTANCE_ID}-manage

MANAGE_WORKSPACE_NAME=$(oc get ManageWorkspace -n ${MAS_APP_NAMESPACE} -l mas.ibm.com/instanceId=${MAS_INSTANCE_ID} -o name)

# Check ManageWorkspace Exists
if [[ -n $MANAGE_WORKSPACE_NAME ]]; then
	MANAGE_UPGRADE_TYPE=$(oc get -n ${MAS_APP_NAMESPACE} ${MANAGE_WORKSPACE_NAME} -o=jsonpath="{.spec.settings.db.upgrade.upgradeType}")

	# Check if upgrade type of manage is online upgrade or regular upgrade
	if [[ $MANAGE_UPGRADE_TYPE == *"onlineUpgrade"* ]]; then
		ONLINE_UPDATE_DONE_MSG="Database online upgrade portion is done, waiting for offline request."
		MANAGE_DEPLOYMENTREADY_MSG=$(oc get -n ${MAS_APP_NAMESPACE} ${MANAGE_WORKSPACE_NAME} -o=jsonpath="{.status.conditions[?(@.type=='DeploymentReady')].message}")
		RETRIES_USED=1
		MAX_RETRIES=45
		DELAY=120
		PATCH_DONE=false

		# Check if online upgrade is completed and workspace is ready for offline upgrade
		while [[ $MANAGE_DEPLOYMENTREADY_MSG == *"$ONLINE_UPDATE_DONE_MSG"* && $RETRIES_USED -le $MAX_RETRIES ]]
			if [[ $MANAGE_DEPLOYMENTREADY_MSG == *"$ONLINE_UPDATE_DONE_MSG"* ]]; then
				echo "Status found is: ${MANAGE_DEPLOYMENTREADY_MSG}"
				echo "ManageWorkspace indicates it is ready for offline upgrade, patching manageofflineupgraderequest CR to requested, and removing old status if present"
				UPGRADE_REQUEST_STATUS=$(oc get -n ${MAS_APP_NAMESPACE} manageofflineupgraderequest.apps.mas.ibm.com -l mas.ibm.com/instanceId=${MAS_INSTANCE_ID} -o=jsonpath="{.status}")
				if [[ -n $UPGRADE_REQUEST_STATUS ]]; then 
						oc patch -n ${MAS_APP_NAMESPACE} manageofflineupgraderequest.apps.mas.ibm.com -l mas.ibm.com/instanceId=${MAS_INSTANCE_ID} --subresource status --type=json -p="[{'op': 'remove', 'path': '/status'}]"
				fi
				oc patch -n ${MAS_APP_NAMESPACE} manageofflineupgraderequests.apps.mas.ibm.com -l mas.ibm.com/instanceId=${MAS_INSTANCE_ID} --type merge -p $'spec:\n stage: requested'
				echo "Patch complete for manageofflineupgraderequest CR"
				PATCH_DONE=true
			else
				echo "[${RETRIES_USED}/${MAX_RETRIES}] ManageWorkspace status does not indicate it is ready for offlineupgrade. Waiting ${DElAY} seconds before checking again."
				sleep 120
				RETRIES_USED=$((RETRIES_USED + 1))
				MANAGE_DEPLOYMENTREADY_MSG=$(oc get -n ${MAS_APP_NAMESPACE} ${MANAGE_WORKSPACE_NAME} -o=jsonpath="{.status.conditions[?(@.type=='DeploymentReady')].message}")
			fi
		done
		
		# Check the status of offline upgrade if the patch is completed
		if [[ $PATCH_DONE = false ]]; then
			echo "The ManageWorkspace Status does not indicate it is ready for offlineupgrade even after ${MAX_RETRIES} retries (${DELAY}s delay), so do nothing"
			echo "Final Status found is: ${MANAGE_DEPLOYMENTREADY_MSG}"
		else
			RETRIES_USED=1
			MAX_RETRIES=45
			DELAY=120
			READY_STATUS=$(oc get -n ${MAS_APP_NAMESPACE} ${MANAGE_WORKSPACE_NAME} -o=jsonpath="{.status.conditions[?(@.type=='Ready')].reason}")
			while [[ $READY_STATUS == *"Ready"* && $RETRIES_USED -le $MAX_RETRIES ]]
				if [[ $READY_STATUS == *"Ready"* ]]; then
					echo "Status found is: ${READY_STATUS}"
					echo "Online and Offline upgrade complete. Server bundles are up and running."
					exit 0
				else
					echo "[${RETRIES_USED}/${MAX_RETRIES}] ManageWorkspace status does not indicate it is ready for offlineupgrade. Waiting ${DElAY} seconds before checking again."
					sleep 120
					RETRIES_USED=$((RETRIES_USED + 1))
					READY_STATUS=$(oc get -n ${MAS_APP_NAMESPACE} ${MANAGE_WORKSPACE_NAME} -o=jsonpath="{.status.conditions[?(@.type=='Ready')].reason}")
				fi
			done
		fi
	else
		echo "Upgrade type is: ${MANAGE_UPGRADE_TYPE}."
		echo "Upgrade type for manage is not onlineUpgrade, so skipping the step to patch manageofflineupgraderequest CR."
	fi
else
	echo "ManageWorkspace not found with instance id: ${MAS_INSTANCE_ID} in namespace: ${MAS_APP_NAMESPACE}, so skipping the step to patch manageofflineupgraderequest CR."
fi

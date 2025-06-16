#!/bin/sh
#
# Licensed Materials - Property of IBM
#
# Restricted Materials of IBM
#
# (C) COPYRIGHT IBM CORP. 2014.  All Rights Reserved.
#
# configure DB2 instance for use by TRIRIGA
# put instance into ORA mode
# set other instance level settings
#
# requirements 
# instUser must be a valid user and instance
# port must be the port for the instance
# must be logged in as the instance user
#
# db2configinst.sh instUser port db2InstDir

# validate usage

echo "Validating usage and user..."

if [ "$#" -ne 3 ]; then
    echo "Invalid usage - db2configinst.sh instUser port db2InstDir"
    echo "instUser - instance to be configured"
    echo "port - port for the user"
	echo "db2InstDir - DB2 installation directory"
    exit 1
fi

INST_USER=${1}
DB2_PORT=${2}
DB2_HOME=${3}

# validate instance user exist

instHome=`perl -e "@user=getpwnam ${INST_USER};" -e "print @user[7];"`

if [ -z "$instHome" ]; then
    echo "Error: The DB2 instance user $INST_USER does not exist!"
    exit 1
fi
if [ ! -d "$instHome" ] ; then
    echo "Error: The DB2 instance user $INST_USER, home directory does not exist."
    exit 1
fi

# validate running as instance user

if [[ `whoami` != "$INST_USER" ]]; then
	echo "Error: this script needs to be run as the instance user, $INST_USER"
	exit 1
fi

ok=0

# run instance profile 

echo "Execute the instance profile..."
echo ". ${instHome}/sqllib/db2profile"
. ${instHome}/sqllib/db2profile
rc=$?
if [ "$rc" -ne "0" ]; then
    echo "Error unable to execute the instance profile, rc = $rc"
    ok=$rc
else
	echo "Return code for execute the instance profile is $rc"
fi

# set instance to autostart - not required

echo "Set instance to autostart..."
echo "${instHome}/sqllib/bin/db2iauto -on $INST_USER"
${instHome}/sqllib/bin/db2iauto -on $INST_USER
rc=$?
if [ "$rc" -ne "0" ]; then
    echo "Error unable set instance to autostart, rc = $rc"
    ok=$rc
else
	echo "Return code for set instance to autostart is $rc"
fi

# set the instance level properties - all required

echo "Set instance level properties..."
echo "$DB2_HOME/bin/db2 update dbm config using SVCENAME $DB2_PORT DEFERRED"
$DB2_HOME/bin/db2 update dbm config using SVCENAME $DB2_PORT DEFERRED
rc=$?
if [ "$rc" -ne "0" ]; then
    echo "Error unable to set dbm SVCENAME for instance, rc = $rc"
    ok=$rc
else
	echo "Return code for dbm SVCENAME is $rc"
fi

echo "$DB2_HOME/adm/db2set DB2_COMPATIBILITY_VECTOR=ORA"
$DB2_HOME/adm/db2set DB2_COMPATIBILITY_VECTOR=ORA
rc=$?
if [ "$rc" -ne "0" ]; then
    echo "Error unable to db2set ORA mode for instance, rc = $rc"
    ok=$rc
else
	echo "Return code for db2set ORA mode is $rc"
fi

echo "$DB2_HOME/adm/db2set DB2_DEFERRED_PREPARE_SEMANTICS=YES"
$DB2_HOME/adm/db2set DB2_DEFERRED_PREPARE_SEMANTICS=YES
rc=$?
if [ "$rc" -ne "0" ]; then
    echo "Error unable to db2set DB2_DEFERRED_PREPARED_SEMANTICS, rc = $rc"
    ok=$rc
else
    echo "Return code for db2set DB2_DEFERRED_PREPARE_SEMANTICS is $rc"
fi

echo "$DB2_HOME/adm/db2set DB2_ATS_ENABLE=YES"
$DB2_HOME/adm/db2set DB2_ATS_ENABLE=YES
rc=$?
if [ "$rc" -ne "0" ]; then
    echo "Error unable to db2set DB2_ATS_ENABLED, rc = $rc"
    ok=$rc
else
    echo "Return code for db2set DB2_ATS_ENABLE is $rc"
fi

echo "$DB2_HOME/adm/db2set DB2COMM=tcpip"
$DB2_HOME/adm/db2set DB2COMM=tcpip
rc=$?
if [ "$rc" -ne "0" ]; then
    echo "Error unable to db2set DB2COMM, rc = $rc"
    ok=$rc
else
    echo "Return code for db2set DB2COMM is $rc"
fi

echo "$DB2_HOME/adm/db2set DB2_USE_ALTERNATE_PAGE_CLEANING=ON"
$DB2_HOME/adm/db2set DB2_USE_ALTERNATE_PAGE_CLEANING=ON
rc=$?
if [ "$rc" -ne "0" ]; then
    echo "Error unable to db2set DB2_USE_ALTERNATE_PAGE_CLEANING, rc = $rc"
    ok=$rc
else 
    echo "Return code for db2set DB2_USE_ALTERNATE_PAGE_CLEANING is $rc"
fi

# stop the instance

echo "Stop and restart instance to make sure all instance properties are set for use..."
echo "db2stop force"
db2stop force
rc=$?
if [ "$rc" -ne "0" ]; then
	if [ "$rc" -ne "1" ]; then
		echo "Error stopping instance $INST_USER for some reason, rc = $rc"
    	ok=$rc
    else
    	echo "Return code for stopping instance $INST_USER is $rc"
    fi
else
	echo "Return code for stopping instance $INST_USER is $rc"
fi

# start the instance
echo "db2start"
db2start
rc=$?
if [ "$rc" -ne "0" ]; then
	echo "Error starting instance $INST_USER for some reason, rc = $rc"
    ok=$rc
else
	echo "Return code for starting instance $INST_USER is $rc"
fi

if [ $ok -ne "0" ]; then
    echo "Instance $INST_USER is NOT configured correctly, check return codes to determine failed operation before continuing with database installation."
else 
    echo "Instance $INST_USER has been configured successfully and started on $DB2_PORT."
fi
exit $ok
#!/bin/sh
# 
# Licensed Materials - Property of IBM
# 
# Restricted Materials of IBM
# 
# (C) COPYRIGHT IBM CORP. 2025.  All Rights Reserved.
# 
# create DB2 database for use by TRIRIGA
# set database level performance and other settings
# 
# requirements -
# database name must not be used on the server
# instance must be valid and started
# territory must be valid with UTF-8 code set
# must be run as DB2 instance user
# tririga user must be a valid user on the system

# db2createdb name instance territory installDir tririgaUser

echo "Validating request..." 
if [ "$#" -ne "5" ]; then
    echo "Invalid usage - db2createdb name instance territory installDir tririgaUser"
	echo "name - database to be created"
	echo "instance - instance to create the database for"
	echo "territory - territory, must be consistent with UTF-8"
	echo "installDir - DB2 installation directory"
	echo "tririgaUser - tririga user name - user must exist"
	exit 1
fi

# set parameters used in the script

DB2_DBNAME=${1}
DB2_INSTNAME=${2}
DB2_TERRITORY=${3}
DB2_HOME=${4}
DB2_USER=${5}

# validate running as instance user

if [[ `whoami` != "$DB2_INSTNAME" ]]; then
	echo "Error: this script needs to be run as the instance user, $DB2_INSTNAME"
	exit 1
fi

# start the instance

echo "Starting the instance, $DB2_INSTNAME if it is not already started..."
echo "db2start"
db2start
rc=$?
if [ $rc -ne "0" ]; then
	if [ $rc -ne "1" ]; then
    	echo "Error unable to start instance $DB2_INSTNAME for some reason = $rc.  Cannot continue and create the database."
    	exit 1
	fi
fi
echo "Return code for starting instance $DB2_INSTNAME is $rc"

ok=0

# Create the database - pagesize of 32 K required, UTF-8 required if any MBCS data will be used

echo "Processing batch command file has started please wait..."
echo "$DB2_HOME/bin/db2 create db $DB2_DBNAME ALIAS $DB2_DBNAME using codeset UTF-8 territory $DB2_TERRITORY pagesize 32 K"
$DB2_HOME/bin/db2 create db $DB2_DBNAME ALIAS $DB2_DBNAME using codeset UTF-8 territory $DB2_TERRITORY pagesize 32 K
rc=$?
if [ $rc -ne "0" ]; then
	echo "Unable to create database for some reason = $rc"
	echo "Possible errors include invalid parameters passed into the script, database name in use, or not running as the $DB2_INSTNAME user"
	exit $rc
else
	echo "Return code for creating the database is $rc"
fi

# connect to the newly created database - required 

echo "$DB2_HOME/bin/db2 connect to $DB2_DBNAME"
$DB2_HOME/bin/db2 connect to $DB2_DBNAME
rc=$?
if [ $rc -ne "0" ]; then
	echo "Unable to connect to $DB2_NAME for some reason = $rc"
	exit $rc
fi
echo "Return code from CONNECT is $rc"

# set CODEUNITS32 - required if want to store any MBCS data

echo "$DB2_HOME/bin/db2 update db cfg for $DB2_DBNAME using string_units CODEUNITS32"
$DB2_HOME/bin/db2 update db cfg for $DB2_DBNAME using string_units CODEUNITS32
rc=$?
if [ $rc -ne "0" ]; then
	ok=$rc
fi
echo "Return code from db cfg for CODEUNITS32 is $rc"

# grant access to the tririga user - all permissions required

echo "$DB2_HOME/bin/db2 GRANT DBADM ON DATABASE TO USER $DB2_USER"
$DB2_HOME/bin/db2 GRANT DBADM ON DATABASE TO USER $DB2_USER
rc=$?
if [ $rc -ne "0" ]; then
	ok=$rc
fi
echo "Return code from GRANT DBADM is $rc"

echo "$DB2_HOME/bin/db2 GRANT SECADM ON DATABASE TO USER $DB2_USER"
$DB2_HOME/bin/db2 GRANT SECADM ON DATABASE TO USER $DB2_USER
rc=$?
if [ $rc -ne "0" ]; then
	ok=$rc
fi
echo "Return code from GRANT SECADM is $rc"

echo "$DB2_HOME/bin/db2 GRANT ACCESSCTRL ON DATABASE TO USER $DB2_USER"
$DB2_HOME/bin/db2 GRANT ACCESSCTRL ON DATABASE TO USER $DB2_USER
rc=$?
if [ $rc -ne "0" ]; then
	ok=$rc
fi
echo "Return code from GRANT ACCESSCTRL is $rc"

echo "$DB2_HOME/bin/db2 GRANT DATAACCESS ON DATABASE TO USER $DB2_USER"
$DB2_HOME/bin/db2 GRANT DATAACCESS ON DATABASE TO USER $DB2_USER
rc=$?
if [ $rc -ne "0" ]; then
	ok=$rc
fi
echo "Return code from GRANT DATAACCESS is $rc"

# performance settings - all required

echo "$DB2_HOME/bin/db2 bind '$DB2_HOME/bnd/db2clipk.bnd' collection NULLIDR1"
$DB2_HOME/bin/db2 bind \'$DB2_HOME/bnd/db2clipk.bnd\' collection NULLIDR1
rc=$?
if [ $rc -ne "0" ]; then
	ok=$rc
fi
echo "Return code from bind is $rc"

echo "$DB2_HOME/bin/db2 update dbm cfg using RQRIOBLK 65535"
$DB2_HOME/bin/db2 update dbm cfg using RQRIOBLK 65535
rc=$?
if [ $rc -ne "2" ]; then
	ok=$rc
fi
echo "Return code from update dbm cfg RQRIOBLK is $rc"

echo "$DB2_HOME/bin/db2 update dbm cfg using AGENT_STACK_SZ 1024"
$DB2_HOME/bin/db2 update dbm cfg using AGENT_STACK_SZ 1024
rc=$?
if [ $rc -ne "2" ]; then
	ok=$rc
fi
echo "Return code from update dbm cfg AGENT_STACK_SZ is $rc"

echo "$DB2_HOME/bin/db2 update db cfg for $DB2_DBNAME using STMT_CONC OFF"
$DB2_HOME/bin/db2 update db cfg for $DB2_DBNAME using STMT_CONC OFF
rc=$?
if [ $rc -ne "0" ]; then
	ok=$rc
fi
echo "Return code from update db cfg STMT_CONC is $rc"

# database transaction and catalog cache settings - all suggested, but not required

echo "$DB2_HOME/bin/db2 update db cfg for $DB2_DBNAME using LOGPRIMARY 23"
$DB2_HOME/bin/db2 update db cfg for $DB2_DBNAME using LOGPRIMARY 23
rc=$?
if [ $rc -ne "2" ]; then
	ok=$rc
fi
echo "Return code from update db cfg LOGPRIMARY is $rc"

echo "$DB2_HOME/bin/db2 update db cfg for $DB2_DBNAME using LOGFILSIZ 32768"
$DB2_HOME/bin/db2 update db cfg for $DB2_DBNAME using LOGFILSIZ 32768
rc=$?
if [ $rc -ne "2" ]; then
	ok=$rc
fi
echo "Return code from update db cfg LOGFILSIZ is $rc"

echo "$DB2_HOME/bin/db2 update db cfg for $DB2_DBNAME using LOGSECOND 12"
$DB2_HOME/bin/db2 update db cfg for $DB2_DBNAME using LOGSECOND 12
rc=$?
if [ $rc -ne "0" ]; then
	ok=$rc
fi
echo "Return code from update db cfg LOGSECOND is $rc"

echo "$DB2_HOME/bin/db2" update db cfg for $DB2_DBNAME using LOGBUFSZ 8192"
$DB2_HOME/bin/db2" update db cfg for $DB2_DBNAME using LOGBUFSZ 8192
rc=$?
if [ $rc -ne "2" ]; then
	ok=$rc
fi
echo "Return code from update db cfg LOGBUFSZ is $rc"

echo "$DB2_HOME/bin/db2 update db cfg for $DB2_DBNAME using LOCKTIMEOUT 30"
$DB2_HOME/bin/db2 update db cfg for $DB2_DBNAME using LOCKTIMEOUT 30
rc=$?
if [ $rc -ne "2" ]; then
	ok=$rc
fi
echo "Return code from update db cfg LOCKTIMEOUT is $rc"

echo "$DB2_HOME/bin/db2 update db cfg for $DB2_DBNAME using catalogcache_sz 2048"
$DB2_HOME/bin/db2 update db cfg for $DB2_DBNAME using catalogcache_sz 2048
rc=$?
if [ $rc -ne "0" ]; then
	ok=$rc
fi
echo "Return code from update db cfg catalogcache_sz is $rc"

# cleanup/restart

echo "$DB2_HOME/bin/db2 connect reset"
$DB2_HOME/bin/db2 connect reset
rc=$?
if [ $rc -ne "0" ]; then
	ok=$rc
fi
echo "Return code from connect reset is $rc"

echo "db2stop force"
db2stop force
rc=$?
if [ $rc -ne "0" ]; then
	ok=$rc
fi
echo "Return code from db2stop is $rc"

echo "db2start"
db2start
rc=$?
if [ $rc -ne "0" ]; then
	ok=$rc
fi
echo "Return code from db2start is $rc"

if [ $ok -ne "0" ]; then
	echo "Database $DB2_DBNAME is NOT configured correctly on $DB2_INSTNAME, check return codes to determine failed configuration setting and fix before continuing with TRIRIGA installation."
	exit $ok
fi

echo "Database $DB2_DBNAME has been created successfully on $DB2_INSTNAME."
exit 0 
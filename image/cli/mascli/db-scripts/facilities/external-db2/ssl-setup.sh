#!/bin/sh
# 
# Licensed Materials - Property of IBM
# 
# Restricted Materials of IBM
# 
# (C) COPYRIGHT IBM CORP. 2025.  All Rights Reserved.
# 


INST_USER=${1}

instHome=`perl -e "@user=getpwnam ${INST_USER};" -e "print @user[7];"`


# Add gskit libraries in the PATH
export PATH="$instHome/sqllib/gskit/bin:$PATH"

# Generate Key Database and Certificate:
mkdir dbcerts
cd dbcerts
gsk8capicmd_64 -keydb -create -db "mydbserver.kdb" -pw "purisaab" -stash
gsk8capicmd_64 -cert -create -db "mydbserver.kdb" -pw "purisaab" -label "myselfsigned" -dn "CN=myhost.mycompany.com,O=myOrganization,OU=myOrganizationUnit,L=myLocation,ST=ON,C=CA"
gsk8capicmd_64 -cert -extract -db "mydbserver.kdb" -pw "purisaab" -label "myselfsigned" -target "mydbserver.arm" -format ascii -fips

# Update DB2 settings
db2 update dbm cfg using SSL_SVR_KEYDB $instHome/dbcerts/mydbserver.kdb
db2 update dbm cfg using SSL_SVR_STASH $instHome/dbcerts/mydbserver.sth
db2 update dbm cfg using SSL_SVR_LABEL myselfsigned
db2 update dbm cfg using SVCENAME 50000
db2 update dbm cfg using SSL_SVCENAME 50001
db2 update dbm cfg using SSL_VERSIONS TLSV12
db2set -i $INST_USER DB2COMM=SSL

# Check DB2 configuration
db2 get dbm config | grep SSL

# Start & Stop for changes to take effect
db2stop
db2start

# Display Certificate
cat mydbserver.arm

exit 0
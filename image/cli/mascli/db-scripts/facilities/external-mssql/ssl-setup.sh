#!/bin/sh

# Generate Certificate
openssl req -x509 -nodes -newkey rsa:2048 -subj '/CN=tririga' -keyout mssql.key -out mssql.pem -days 365

# Create folder structure for Certs
chmod 755 mssql.key mssql.pem
mkdir -p /etc/ssl/private
chmod 755 /etc/ssl/private
mv mssql.key /etc/ssl/private
mv mssql.pem /etc/ssl/certs

# Configure MSSQL
systemctl stop mssql-server 
cat /var/opt/mssql/mssql.conf 
/opt/mssql/bin/mssql-conf set network.tlscert /etc/ssl/certs/mssql.pem
/opt/mssql/bin/mssql-conf set network.tlskey /etc/ssl/private/mssql.key
/opt/mssql/bin/mssql-conf set network.tlsprotocols 1.2
/opt/mssql/bin/mssql-conf set network.forceencryption 1
systemctl restart mssql-server
cat /var/opt/mssql/mssql.conf 

# Display Certificate
cat /etc/ssl/certs/mssql.pem

exit 0
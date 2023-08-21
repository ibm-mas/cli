#!/bin/bash

# Install Mongo Shell
set -e

curl "https://downloads.mongodb.com/compass/mongodb-mongosh-shared-openssl11-1.10.5.x86_64.rpm" -o mongodb-mongosh-shared-openssl11-1.10.5.x86_64.rpm
rpm -i mongodb-mongosh-shared-openssl11-1.10.5.x86_64.rpm

mongosh --version
rm mongodb-mongosh-shared-openssl11-1.10.5.x86_64.rpm

# Install Mongo Tools
curl "https://fastdl.mongodb.org/tools/db/mongodb-database-tools-rhel80-x86_64-100.8.0.tgz" -o mongodb-database-tools-rhel80-x86_64-100.8.0.tgz
tar xvfz mongodb-database-tools-rhel80-x86_64-100.8.0.tgz

mv mongodb-database-tools-rhel80-x86_64-100.8.0/bin/* /usr/local/bin/
rm -rf mongodb-database-tools-rhel80-x86_64-100.8.0
rm mongodb-database-tools-rhel80-x86_64-100.8.0.tgz

mongodump --version

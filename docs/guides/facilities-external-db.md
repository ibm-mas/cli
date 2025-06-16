Facilities External DB
===============================================================================
Databases for Maximo Real Estate and Facilities (MREF) needs to be prepared before deployed in Maximo Suite. In all scenarios, 
it requires to run the following script:

```
podman run -it --pull always quay.io/ibmmas/cli
```

DB2 Database
-------------------------------------------------------------------------------
Inside the container, run 

```
scp -P <port> /db-scripts/facilities/external-db2 <username>@<DB2 domain>:/<target path>
```

Connect to the target DB2 database server through SSH and go to the path where the files were copied. Give the scripts permission to execute by running:

```
chmod +x /<target path>/*.sh
```

The first step is to configure SSL by running

```
./ssl-setup.sh "<target instance db2 name>"
```

After the SSL is configured, create the user that will be granted permissions for the MREF database. After that, run

```
./db2configinst.sh "<instance to be configured>" "<database port>" "<DB2 installation directory>"
```

Which configure the instance for MREF. The next step is to create the database by running

```
./db2createdb.sh "<name of the database to be created>" "<database instance>" "<territory>" "<Db2 installation directory>" "<Db2 user>"
```

The territory needs to be UTF-8 standard. The last step is to create the the tablespaces for DB2. This step can be performed by running:

```
db2 connect to <DB name>
db2 -tf ./create-ts.sql
```


Oracle Database
-------------------------------------------------------------------------------
Inside the container, run

```
scp -P <port> /db-scripts/facilities/external-oracle <username>@<Oracle domain>:/<target path>
```

Connect to the target Oracle database server through SSH and go to the path where the files were copied. Replace the username and password from `./createuser.sql` and run 

```
exit | sqlplus -S <admin username>/password@<JDBC url> @createuser.sql
```

With the user created, create the tablespaces by running

```
exit | sqlplus -S <username created>/password@<JDBC url> @create-ts.sql
```

Microsoft Server Database
-------------------------------------------------------------------------------
Inside the container, run

```
scp -P <port> /db-scripts/facilities/external-mssql <username>@<Microsoft Server domain>:/<target path>
```

Connect to the target Microsoft database server through SSH and go to the path where the files were copied. Give the scripts permission to execute by running:

```
chmod +x /<target path>/*.sh
```

In the target path, run
```
./ssl-setup.sh
```

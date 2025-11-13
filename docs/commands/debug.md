Debug
===============================================================================

Usage
-------------------------------------------------------------------------------
`mas debug [command] [options]`

### Commands
- `coredump` generate and collect a javacore and a system dump from a mas or manage pod running liberty server
- `threaddump` generate and collect one or more threaddump / javacore from a mas or manage pod running liberty server


### Destination
- `-d|--dir` Directory where the collected files will be saved, defaults to `/tmp`

### Pod selection (define Liberty pod(s) where the files are generated)
- `--namespace` Specify namespace where the liberty server is running
- `-s|--pod-selector` Pod-selector can be serverBundle, <bundle name>, coreidp
- `-p|--pod-name` Gives the pod where the java dump needs to be created, this overwrites -s if specified.

### Coredump specific actions (One of those three actions needs to be specified when using the coredump command)
- `-g|--generate` Generate a coredump for the liberty server according to the pod selector then copies it to the local machine where the script is running
- `-c|--collect` Copy all the coredump files from the node to where the liberty server specified is running to the local machine where the script is running
- `-r|--rm` Remove all the coredump files from the node where the liberty server specified is running
                           This command will remove the content of /var/lib/systemd/coredump/ on the node  


### Threaddump specific parameters
- `-t` Time between collection of javacore (default is 10 seconds)
- `-n` How many javacores will be collected (default is 1)
- `-r|--rm` Remove all the javacores files present in the targeted pod

### Other Options
- `-h|--help`    Show this help message



Usage
-------------------------------------------------------------------------------
As with other CLI functions, the debug commands will run against the currently connected cluster, use `oc login` to connect to a cluster before running `mas debug <commmand> <options>`.

```bash
# Start the container in docker
docker run -ti --rm -v /~:/mnt/home --pull always quay.io/ibmmas/cli
# Login to the cluster and run the must-gather, which will be available in the home directory on the local system
oc login --token=xxx --server=https://xxx:xxx
mas debug threaddump  --namespace mas-test-manage -p test-testws-foundation-54956ff9d7-bzmgb -d /mnt/home -t 10 -n 5
```

```bash
# Start the container in podman
podman run -ti --rm -v /~:/mnt/home:z --pull always quay.io/ibmmas/cli
# Login to the cluster and run the must-gather, which will be available in the home directory on the local system
oc login --token=xxx --server=https://xxx:xxx
mas debug threaddump  --namespace mas-test-manage -p test-testws-foundation-54956ff9d7-bzmgb -d /mnt/home -t 10 -n 5
```


Examples
-------------------------------------------------------------------------------

**Coredump for pod:** Generate a coredump for a particular pod in the manage namespace:
```bash
mas debug coredump  --namespace mas-test-manage -p test-testws-foundation-54956ff9d7-bzmgb -g -d /mnt/home
```

**Coredump for server bundle:** Generate a coredump for the ui server bundle, copies it localy and removes it from the node where it was generated:
```bash
mas debug coredump --namespace mas-test-manage -s ui -g -d /mnt/home
```

**Coredump collection only:** Collect all the coredumps present on the node where ui server bundle is running:
```bash
mas debug coredump --namespace mas-test-manage -s ui -c
```

**Coredump deletion only:** Remove all the coredumps present on the node where the ui server bundle is running:
```bash
mas debug coredump --namespace mas-test-manage -s ui -r
```

**Javacore creation for pod:** Generate 5 javacore, 1 every 10 seconds for a particular pod in the manage namespace:
```bash
mas debug threaddump  --namespace mas-test-manage -p test-testws-foundation-54956ff9d7-bzmgb -d /mnt/home -t 10 -n 5
```

**Javacore creation for server bundle:** Generate a coredump for the ui server bundle, copies it localy and removes it from the node where it was generated:
```bash
mas debug threaddump --namespace mas-test-manage -s ui -d /mnt/home -t 10 -n 5
```

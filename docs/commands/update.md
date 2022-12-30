Update
===============================================================================

Usage
-------------------------------------------------------------------------------
`mas update [options]`

### Maximo Operator Catalog Selection
- `-c|--catalog MAS_CATALOG_VERSION` Maximo Operator Catalog Version to mirror (e.g. v8-221129)

### Other Options
- `--no-confirm` Mirror images without prompting for confirmation
- `-h|--help` Show help message


Examples
-------------------------------------------------------------------------------
### Interactive Update
```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas update
```

### Non-Interactive Update
```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas update -c v8-220927-amd64 --no-confirm
```

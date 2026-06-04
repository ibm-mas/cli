Provision OpenShift on AWS
===============================================================================

Overview
-------------------------------------------------------------------------------
The MAS CLI provides automated provisioning of OpenShift clusters on AWS using Installer Provisioned Infrastructure (IPI).


Provisioning Modes
-------------------------------------------------------------------------------

### Interactive Mode
Interactive mode guides you through the provisioning process with prompts for all configuration options.

```bash
docker run -ti --rm --pull always quay.io/ibmmas/cli mas provision-aws
```

The interactive session will:

1. Verify AWS credentials
2. Request cluster configuration details
3. Configure instance specifications
4. Set up networking options
5. Display a summary and request confirmation

### Non-Interactive Mode
Non-interactive mode is ideal for automation and scripting. All required parameters must be provided via command-line arguments or environment variables.

!!! note
    Detailed non-interactive parameters are available via `mas provision-aws --help`

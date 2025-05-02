Image Validation
===============================================================================
MAS container images are digitally signed, and their signatures can be verified using the MAS public key. The private key is used to generate the signature, while the corresponding public key enables anyone to validate the signature, ensuring both the integrity and authenticity of the content. To begin the verification process, the customer must have the following items:

- [PRD0010163key.pub.asc](https://github.com/ibm-mas/cli/blob/master/image/cli/mascli/image-validation/PRD0010163key.pub.asc) - the MAS public key that should be used to validate image signatures
- [PRD0010163key.pem.cer](https://github.com/ibm-mas/cli/blob/master/image/cli/mascli/image-validation/PRD0010163key.pem.cer) - the MAS public certificate associated with the public key 
- [PRD0010163key.pem.chain](https://github.com/ibm-mas/cli/blob/master/image/cli/mascli/image-validation/PRD0010163key.pem.chain) - a certificate chain that may be used to validate the MAS public certificate is authentic


Tools such as [skopeo](https://github.com/containers/skopeo), [podman](https://podman.io/) and [signature verification policy files](https://github.com/containers/image/blob/main/docs/containers-policy.json.5.md) may be used to help with MAS container signature validation.

Preparation
-------------------------------------------------------------------------------
### IBM Entitlement Key
Access [Container Software Library](https://myibm.ibm.com/products-services/containerlibrary) using your IBMId to obtain your entitlement key.


Validating images during image pull:
------------------------------------
The [skopeo](https://github.com/containers/skopeo) CLI  can be used in combination with a [signature verification policy file](https://github.com/containers/image/blob/main/docs/containers-policy.json.5.md) to validate MAS container signatures:

```bash
skopeo copy --policy ~/policy.json docker://cp.icr.io/cp/mas/image-name@sha256:abc123... dir:/var/lib/docker --src-creds cp:<IBM Entitlement key>
```
A sample [policy.json](https://github.com/ibm-mas/cli/blob/master/image/cli/mascli/image-validation/policy.json) has been provided as a convenience and should be used as a guide when creating signature verification policy files that will be used to validate MAS container images. 

The following is an example of how to validate MAS container signatures using a container image name and digest. To emphasize the `skopeo` CLI and the `policy.json` file are built into the MAS CLI container. 

```bash
[ibmmas/cli:13.18.0]mascli$ skopeo copy --policy ~/policy.json docker://cp.icr.io/cp/mas coreapi@sha256:99a8066af64a298a14364b217fa36add2e607e7aba88c81ae4c5ef5b0e94d8e6 dir:/var/lib/docker --src-creds cp:<IBM Entitlement Key>

 Getting image source signatures
 Checking if image destination supports signatures
 Copying blob d849bfe684ef done   | 
 Copying blob 2923e04ba5db done   | 
 Copying blob 318ff0aed3a3 done   | 
 Copying config bb4a868cff done   | 
 Writing manifest to image destination
 Storing signatures
```

Images can be validated outside MAS CLI container using podman and an applicable policy.json file in one of the paths ($HOME/.config/containers/policy.json or /etc/containers/policy.json)
    
 ```bash
 podman pull cp.icr.io/cp/mas/image-name@sha256:abc123...
 ```

A more detailed example is:

```bash
 podman pull cp.icr.io/cp/mas/coreapi@sha256:99a8066af64a298a14364b217fa36add2e607e7aba88c81ae4c5ef5b0e94d8e6

 Trying to pull cp.icr.io/cp/mas/coreapi@sha256:99a8066af64a298a14364b217fa36add2e607e7aba88c81ae4c5ef5b0e94d8e6...
 Getting image source signatures
 Checking if image destination supports signatures
 Copying blob sha256:d849bfe684ef268bbed3ffbad07ba1e7ade6311d96ab4a3f4124ad33ba629227
 Copying blob sha256:318ff0aed3a36bed3edfb9dbbb1a01b7840c46c805be3dc9276856299aabea2c
 Copying blob sha256:2923e04ba5db0463883fd4d8138b8b5ae3286fc51a95d9fe5a86effe9bd128af
 Copying config sha256:bb4a868cffc9e2e1a77e56eeb9a5427e5c4ec1d56315a002eae2e49c81c79afe
 Writing manifest to image destination
 Storing signatures
 bb4a868cffc9e2e1a77e56eeb9a5427e5c4ec1d56315a002eae2e49c81c79afe
```

Validate the Chain of Trust for the MAS Signing Certificate:
------------------------------------------------------------
To validate the public key owner is IBM, examine the certificate and ensure it contains the public key.  The MAS signing certificate is renewed every two years.

```bash
openssl x509 -text -in /mascli/image-validation/PRD0010163key.pem.cer  # shows the certificate details, e.g. it is signed by IBM and Digicert 

gpg2 -v --list-packets /mascli/image-validation/PRD0010163key.pub.asc  # shows the public key details
```

Verify the Validity of the MAS Container Signing Certificate:
------------------------------------------------------------

```bash
openssl ocsp -no_nonce -issuer /mascli/image-validation/PRD0010163key.pem.chain -cert /mascli/image-validation/PRD0010163key.pem.cer -VAfile /mascli/image-validation/PRD0010163key.pem.chain -text -url http://ocsp.digicert.com -respout ocsptest
```

If the certificate is valid, the output will be: Response verify OK


Image Validation
===============================================================================
MAS images are signed and verified using a public-private key pair. The private key is used to sign the content, and the corresponding public key is used by anyone to verify the signature and ensure the content's integrity and authenticity. The customer must have below items to start verification. 

1. CertAlias.pub.asc 
2. CertAlias.pem.cer 
3. Signing Image.

skopeo and podman uses a policy.json file to describe the signature validation policy.Trust is defined in /etc/containers/policy.json and is enforced when a user attempts to pull a remote image from a registry. The trust policy in policy.json describes a registry scope (registry and/or repository) for the trust. This trust can use public keys for signed images.

Preparation
-------------------------------------------------------------------------------
### IBM Entitlement Key
Access [Container Software Library](https://myibm.ibm.com/products-services/containerlibrary) using your IBMId to obtain your entitlement key.

All the required certs and policy.json are placed in mascli/image-validation 

Validating images during image pull:
------------------------------------
- Inside MAS CLI container images can be validated using skopeo command by specifying the policy file.

```bash
skopeo copy --policy ~/policy.json docker://cp.icr.io/cpopen/image-name@sha256:abc123... dir:/var/lib/docker --src-creds cp:<IBM Entitlement key>
```

Here’s an example of validating using skopeo copy to a local temp directory in Mas CLI:

[ibmmas/cli:13.18.0-pre.imagevalidation]mascli$ skopeo copy --policy ~/policy.json docker://cp.icr.io/cp/mas/coreapi@sha256:99a8066af64a298a14364b217fa36add2e607e7aba88c81ae4c5ef5b0e94d8e6 dir:/var/lib/docker --src-creds cp:<IBM Entitlement Key>

Getting image source signatures

Checking if image destination supports signatures

Copying blob d849bfe684ef done   | 

Copying blob 2923e04ba5db done   | 

Copying blob 318ff0aed3a3 done   | 

Copying config bb4a868cff done   | 

Writing manifest to image destination

Storing signatures

- Images can be validated outside CLI container using the podman and the user would need to provide the policy.json file in one of the paths ($HOME/.config/containers/policy.json or /etc/containers/policy.json)

Here’s an example of validating image using podman pull outside MAS CLI:

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


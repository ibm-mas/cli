Image Validation
===============================================================================
skopeo and podman uses a policy.json file to describe the signature validation policy.Trust is defined in /etc/containers/policy.json and is enforced when a user attempts to pull a remote image from a registry. The trust policy in policy.json describes a registry scope (registry and/or repository) for the trust. This trust can use public keys for signed images.

Preparation
-------------------------------------------------------------------------------
### IBM Entitlement Key
Access [Container Software Library](https://myibm.ibm.com/products-services/containerlibrary) using your IBMId to obtain your entitlement key.

Install skopeo locally by following the instructions in the document: https://github.com/containers/skopeo/blob/main/install.md

Validating images during image pull:
-------------------------------------------------------------------------------
1. Copy the policy.json file into /etc/containers
2. Validate using skopeo copy to a local temp directory
skopeo copy docker://cp.icr.io/cpopen/<image-name>@<digest> dir:/var/lib/docker --src-creds cp:<IBM Entitlement key>

Validate the Chain of Trust:
-------------------------------------------------------------------------------
As a Customer on customer env to validate the public key owner is IBM, Customer can compare the certificate to contain the public key. This is once in 2 years when ever they receive new PRD0010163key.pub.asc key from IBM Dev team.

1. openssl x509 -text -in /mascli/image-validation/PRD0010163key.pem.cer 

# shows the certificate details, e.g. it is signed by IBM and Digicert 

2. gpg2 -v --list-packets /mascli/image-validation/PRD0010163key.pub.asc 

# shows the public key details

Customer can check the IBM certificate validity
-------------------------------------------------------------------------------
1. openssl ocsp -no_nonce -issuer /mascli/image-validation/PRD0010163key.pem.chain -cert /mascli/image-validation/PRD0010163key.pem.cer -VAfile /mascli/image-validation/PRD0010163key.pem.chain -text -url http://ocsp.digicert.com -respout ocsptest

# If the certificate is valid, the output will be: Response verify OK


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
1. Copy the file public key PRD0010163key.pub.asc in the path image/cli/mascli/image-validation/ into local path
2. Copy the policy.json file in the path image/cli/mascli/image-validation into /etc/containers/
3. Update the policy.json with the public key path copied in step 1
4. Validate using skopeo copy to a local temp directory
skopeo copy docker://cp.icr.io/cpopen/ibm-mas@sha256:c148d5a9ba21009495a9c3fb94a561aab9e31789cadb3b7a2af6e2b4bd2f6f34 dir:/var/lib/docker --src-creds cp:<IBM Entitlement key>

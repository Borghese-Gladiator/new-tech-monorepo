# Sigstore
Sigstore is a solution for signing, verifying, and securing software. This is a tool to increase trust in your software's prevenance

## Usage
How to sign a container and store the signature in the registry

1. Install `cosign` CLI
2. "Identity Based Signing" - sign into OIDC Identity Provider (GitHub, Google, or MIcrosoft)
   - uses OAUTH to create identity token at env `SIGSTORE_ID_TOKEN`
3. `cosign sign $IMAGE` signs artifact and stores signature in registry
   - You can try these commands with `ttl.sh` which offers free, short-lived (hours) anonymous container image hosting to try commands out
    ```
    $ IMAGE_NAME=$(uuidgen)
    $ IMAGE=ttl.sh/$IMAGE_NAME:1h
    $ cosign copy alpine $IMAGE
    ```
    - `$ cosign sign [--key <key path>|<kms uri>] [--payload <path>] [-a key=value] [--upload=true|false] [-f] [-r] <image uri>`
    - [Signing Containers](https://docs.sigstore.dev/cosign/signing/signing_with_containers/#sign-with-a-local-key-pair)
    - [Signing Blobs](https://docs.sigstore.dev/cosign/signing/signing_with_blobs/)

Since you can sign anything in a registry, you can technically use this to sign Helm Charts, Tekton Pipelines, and anything else using OCI registries for distribution.

### Under the Hood
[verifying identity and signing the artifact](https://docs.sigstore.dev/cosign/signing/overview/#verifying-identity-and-signing-the-artifact)
- An in-memory public/private keypair is created.
- The identity token is retrieved.
- Sigstore’s certificate authority verifies the identity token of the user signing the artifact and issues a certificate attesting to their identity. The identity is bound to the public key. Decrypting with the public key will prove the identity of the private keyholder.
- For security, the private key is destroyed shortly after and the short-lived identity certificate expires. Users who wish to verify the software will use the transparency log entry, rather than relying on the signer to safely store and manage the private key.

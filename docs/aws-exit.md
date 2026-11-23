# Mentee API AWS exit audit

Before F212, the Pipfile and lock pinned API Utils 1.0.4 from CodeArtifact.
The README’s 1.0.3 reference and the retired 1.0.1 tasks describe earlier versions.

| Surface | Current dependency | Migration |
| --- | --- | --- |
| `Pipfile`, `Pipfile.lock`, `scripts/pipenv-install.sh`, `scripts/pipenv-lock.sh` | CodeArtifact index and AWS CLI authentication | F212 moves third-party packages to public PyPI and pins the exact public API Utils wheel URI and SHA-256. Use `pipenv run install` to sync the development environment and `pipenv lock` to refresh the lock. |
| `Dockerfile`, `scripts/docker-build.sh` | Authenticated `PIP_INDEX_URL` build argument populated by AWS CLI | F213 uses the committed runtime lock with hashes and public package sources. Preserve the image name and runtime entry point. |
| `.github/workflows/docker-push.yml` | AWS OIDC role and CodeArtifact token/index setup | F214 removes AWS authentication, keeps main-branch GHCR publishing, and adds read-only pull request validation. |
| `README.md`, `tasks/_PLANNING.md` | Developer setup references CodeArtifact | F215 documents locked installation and records final acceptance. |

The public [API Utils 1.0.5 wheel](https://github.com/mentor-forge/mentorhub_api_utils/releases/download/v1.0.5/api_utils-1.0.5-py3-none-any.whl)
downloaded without credentials and matched the published SHA-256
`79de3829e2baa294497e08925908645bcea53cdf497d02b6bed71322a503d952`.
The PyPI project with the same distribution name is unrelated. Use the exact
wheel URL and digest together. For a later rollback, restore the previously
verified wheel pin and its matching lock, then repeat clean-install and
packaged acceptance. Version 1.0.5 is the first verified GitHub-hosted rollback
floor.

## Runtime contracts

The Mentee API service in Developer Edition configures MongoDB, JWT validation,
logging, and service ports. Tracked application and test sources contain no
Cognito, AWS SDK, or AWS endpoint references. Existing identity-bearing data
does not introduce a runtime AWS service dependency. Preserve JWT validation
and role checks and retain MongoIO for database access. No OpenAPI, schema,
or production identity-provider changes are needed for this migration.

The wheel's token factory requires a `profile_id` and uses the JWT
`display_name` claim for the normalized application field. The Mentee test
persona already emits both. The current Event E2E assertion also checks
`context.display_name`. The retired F209/F210 notes record a historical
`context.name` failure. Verify the Event case in the packaged gate.

The wheel exposes `MongoIO.get_document(collection_name, document_id)` and
`get_documents(collection_name, match, project, sort_by, skip, limit)`.
Its update method accepts the existing document ID, match, set, push and pull
arguments. The Mentee service uses the shared `encode_document` helper for
ObjectId and date conversion. Preserve these interfaces and the current
service ownership through the dependency and build changes.

## Dependency lock verification

F212 now uses public PyPI and the hash-pinned release wheel. The legacy Pipenv
wrappers were removed. Use `pipenv run install` to sync and `pipenv lock` to
regenerate the lock. In a fresh AWS-free environment, lock regeneration, lock
verification, locked install, lint, 98 unit tests, and compilation passed. The
hashed requirements export and installed metadata retained the wheel URL and
SHA-256. Packaged validation follows the container migration.

## Container verification

The Docker build installs the committed runtime requirements using Pipenv's
hashed export and pip's hash verification. The build uses public PyPI and the
exact API Utils release wheel. Run `pipenv run container` without AWS or
GitHub credentials. The default GHCR image reference is unchanged, and
`MENTEE_API_IMAGE` selects an isolated local image tag when needed.

An ARM64 build passed with AWS variables unset, and its image history had no
CodeArtifact or index argument. Installed wheel metadata matched API Utils
1.0.5, its release URL, and the published SHA-256. In isolated seeded Developer
Edition services, docs, OpenAPI, metrics, and authenticated config returned
200, and the unauthenticated resource endpoint returned 401. All 36 packaged
end-to-end cases passed, including the Event context `display_name` assertion.

## GitHub Actions verification

Pull requests into main run a read-only validation job. It disables checkout
credential persistence, verifies and syncs the Pipenv lock, runs lint and
unit tests, compiles the application, and builds a local container image.
The job needs no package credentials and does not publish images.

The separate push-to-main workflow uses repository contents read access and
package write access to publish the existing GHCR image for Linux AMD64 and
ARM64. It uses GitHub's workflow token for GHCR, and the container downloads
the same public wheel and hashed runtime dependencies as a local build.

Local workflow checks, lock verification and sync, lint, all 98 unit tests,
compilation, and an isolated ARM64 build passed with AWS variables unset.
GitHub-hosted validation evidence is available after opening the pull request.

## Final local acceptance

A fresh checkout and virtual environment passed `pipenv verify`,
`pipenv run install`, all 98 unit tests, lint, compilation, and the ARM64
container build. The container reported API Utils 1.0.5. The packaged
acceptance harness started disposable MongoDB, seeded Developer Edition
data, and ran the built API on an isolated loopback port. All 36 end-to-end
cases passed without skips, including the Event context `display_name`
assertion. A mentee could list resources, a mentor could not create a
mentee note, and missing credentials, incorrect issuer, audience, or
signature, expired tokens, and missing profile claims returned HTTP 401
where applicable. The active Developer Edition stack was left running.

Rollback restores the verified wheel URL and hash together with their
matching lockfile, followed by a clean install, image rebuild, and packaged
test run. The migration adds no provider-specific runtime adapter. Hosted
PR checks and post-merge publication are separate from local acceptance.

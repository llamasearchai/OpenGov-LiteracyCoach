# Release Process

Author: Nik Jois

## 1) Create a release branch

```bash
BRANCH=release/v1.2.0
LATEST=v1.2.0
git checkout -b ${BRANCH}
# Ensure version bumped in pyproject.toml (currently 1.2.0)
```

## 2) Update changelog and notes

- Add/update `docs/RELEASE_NOTES_v1.2.0.md` with highlights and changes.
- Ensure README reflects any new configuration or usage.

## 3) Open PR

- Title: `Release ${LATEST}`
- Use the PR template; include release notes.
- Reviewer(s): at least 1 maintainer.

## 4) Merge PR

- Ensure CI is green.
- Squash or merge per repo policy.

## 5) Tag and push

```bash
git tag ${LATEST}
git push origin ${LATEST}
```

This triggers the GitHub Release workflow to:
- Re-run tests
- Build sdist/wheel and publish to PyPI (if `PYPI_API_TOKEN` is set)
- Build and push Docker images (if Docker Hub secrets are set)

## 6) Verify

- PyPI: package page updated with version `${LATEST}`.
- Docker Hub: images tagged with `${LATEST}`.
- GitHub Release page: artifacts and notes present.

## 7) Post-release

- Bump to next dev version (e.g., 1.2.1) on main if desired.


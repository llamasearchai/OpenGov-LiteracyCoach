#!/usr/bin/env bash
set -euo pipefail

echo "==> Running tests"
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
pytest -p pytest_cov

echo "==> Building package"
python -m pip install --upgrade build
python -m build

echo "==> Building Docker images"
docker compose build

cat <<EOF

Release artifacts built:
- dist/ (Python sdist and wheel)
- Docker images (local)

To publish:
- PyPI: use GitHub Action 'Release' with tag and PYPI_API_TOKEN secret.
- Docker: docker login and push your built images.
EOF


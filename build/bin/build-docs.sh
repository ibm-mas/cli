#!/bin/bash

# Update all the placeholders in the doc source
# Make sure not to commit these changes if you run this script locally
find docs -type f -name '*.md' -exec sed -i \
  -e 's/@@CLI_LATEST_VERSION@@/13.20.0/g' \
  -e 's/@@MAS_PREVIOUS_CHANNEL@@/8.11.x/g' \
  -e 's/@@MAS_PREVIOUS_CATALOG@@/v9-250403-amd64/g' \
  -e 's/@@MAS_LATEST_CHANNEL@@/9.0.x/g' \
  -e 's/@@MAS_LATEST_CHANNEL_MANAGE@@/9.0.x/g' \
  -e 's/@@MAS_LATEST_CATALOG@@/v9-250501-amd64/g' \
  {} \;

python -m pip install -q mkdocs mkdocs-carbon mkdocs-glightbox mkdocs-redirects
mkdocs build --clean --strict

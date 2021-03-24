#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py build-matches-db \
  data/enwiki-20200920.xml \
  data/wikidata-v1-codex.json \
  data/matches-v6-codex.db \
  --in-memory \
> log/build-matches-db_$(date +'%Y-%m-%d_%H-%M-%S').stdout &
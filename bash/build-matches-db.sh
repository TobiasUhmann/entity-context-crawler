#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py build-matches-db \
  data/enwiki-20200920.xml \
  data/wikidata-v1-2020-12-31.json \
  data/matches-v5-enwiki-20200920.db \
  --in-memory \
> log/build-matches-db_$(date +'%Y-%m-%d_%H-%M-%S').stdout &

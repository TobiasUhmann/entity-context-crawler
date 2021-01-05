#!/bin/bash

PYTHONPATH=src/ PYTHONHASHSEED=0 \
nohup python -u src/sam.py build-matches-db \
  data/enwiki-20200920.xml \
  data/wikidata-v1-2020-12-31.json \
  data/matches-v5-enwiki-20200920-dev.db \
  --limit-pages 1000 \
  --overwrite \
  --random-seed 0 \
> log/build-matches-db-dev_$(date +'%Y-%m-%d_%H-%M-%S').stdout &

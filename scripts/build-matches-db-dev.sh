#!/bin/bash

PYTHONPATH=src/ PYTHONHASHSEED=0 \
nohup python -u src/sam.py build-matches-db \
  data/entity2wikidata.json \
  data/enwiki-2018-09-text.xml \
  data/links-v1-enwiki-20200920.db \
  data/matches-v1-enwiki-20200920-dev.db \
  --limit-pages 1000 \
  --overwrite \
  --random-seed 0 \
> log/build-matches-db-dev_$(date +'%Y-%m-%d_%H-%M-%S').stdout &

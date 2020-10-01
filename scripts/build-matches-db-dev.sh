#!/bin/bash

PYTHONPATH=src/ PYTHONHASHSEED=0 \
nohup python -u src/sam.py build-matches-db \
  data/entity2wikidata.json \
  data/enwiki-2018-09-text.xml \
  data/enwiki-20200920-links.db \
  data/enwiki-20200920-matches-dev.db \
  --limit-pages 1000 \
  --overwrite \
  --random-seed 0 \
> log/build-matches-db-dev_$(date +'%Y-%m-%d_%H-%M-%S').stdout &

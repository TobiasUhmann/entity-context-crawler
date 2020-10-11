#!/bin/bash

PYTHONPATH=src/ PYTHONHASHSEED=0 \
nohup python -u src/sam.py build-links-db \
  data/entity2wikidata.json \
  data/enwiki-20200920.xml \
  data/links-v1-enwiki-20200920-dev.db \
  --limit-pages 1000 \
  --overwrite \
  --random-seed 0 \
> log/build-links-db-dev_$(date +'%Y-%m-%d_%H-%M-%S').stdout &

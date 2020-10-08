#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py build-contexts-db \
  data/entity2wikidata.json \
  data/links-v1-enwiki-20200920.db \
  data/matches-v1-enwiki-20200920.db \
  data/contexts-v1-enwiki-20200920-100-500.db \
  --context-size 500 \
  --crop-sentences \
  --csv-file data/contexts-v1-enwiki-20200920-100-500.csv \
  --limit-contexts 100 \
> log/build-contexts-db_$(date +'%Y-%m-%d_%H-%M-%S').stdout &

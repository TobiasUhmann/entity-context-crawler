#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py build-matches-db \
  data/entity2wikidata.json \
  data/enwiki-2018-09-text.xml \
  data/enwiki-20200920-links.db \
  data/enwiki-20200920-matches.db \
  --in-memory \
> log/build-matches-db_$(date +"%Y-%m-%d_%H-%M-%S").stdout &

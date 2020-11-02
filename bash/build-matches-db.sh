#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py build-matches-db \
  data/enwiki-20200920.xml \
  data/entity2wikidata.json \
  data/matches-v4-enwiki-20200920.db \
  --in-memory \
> log/build-matches-db_$(date +'%Y-%m-%d_%H-%M-%S').stdout &

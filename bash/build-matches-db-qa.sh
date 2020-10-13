#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py build-matches-db \
  data/enwiki-20200920.xml \
  data/entity2wikidata.json \
  data/matches-v2-enwiki-20200920-qa.db \
  --in-memory \
> log/build-matches-db-qa_$(date +'%Y-%m-%d_%H-%M-%S').stdout &

#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py build-matches-db \
  data/entity2wikidata.json \
  data/enwiki-2018-09-text.xml \
  data/links-v1-enwiki-20200920.db \
  data/matches-v1-enwiki-20200920-qa.db \
  --in-memory \
> log/build-matches-db-qa_$(date +'%Y-%m-%d_%H-%M-%S').stdout &

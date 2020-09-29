#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py build-matches-db \
  data/entity2wikidata.json \
  data/enwiki-2018-09-text.xml \
  data/enwiki-20200920-links.db \
  data/enwiki-20200920-matches-qa.db \
  --in-memory \
> log/build-matches-db-qa_$(date +'%Y-%m-%d_%H-%M-%S').stdout &

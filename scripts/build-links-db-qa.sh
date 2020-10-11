#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py build-links-db \
  data/entity2wikidata.json \
  data/enwiki-20200920.xml \
  data/links-v1-enwiki-20200920-qa.db \
  --in-memory \
> log/build-links-db-qa_$(date +'%Y-%m-%d_%H-%M-%S').stdout &

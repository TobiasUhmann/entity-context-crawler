#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py build-links-db \
  data/enwiki-20200920.xml \
  data/enwiki-20200920-links.db \
  --in-memory \
> log/build-links-db_$(date +'%Y-%m-%d_%H-%M-%S').stdout &

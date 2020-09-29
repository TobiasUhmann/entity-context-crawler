#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py query-es-test \
  enwiki-20200920-cw-contexts-100-500 \
  data/enwiki-20200920-ow-contexts-100-500.db \
  --limit-entities 10 \
> log/query-es-test_$(date +"%Y-%m-%d_%H-%M-%S").stdout &

#!/bin/bash

PYTHONPATH=src/ \
nohup python -u src/sam.py query-es-test \
  cw-contexts-v4-enwiki-20200920-100-500 \
  data/ow-contexts-v4-enwiki-20200920-100-500.db \
  --limit-entities 10 \
> log/query-es-test_$(date +'%Y-%m-%d_%H-%M-%S').stdout &

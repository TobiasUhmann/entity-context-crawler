set PYTHONPATH=src\
set PYTHONHASHSEED=0
python -u src\sam.py build-contexts-db ^
  data\entity2wikidata.json ^
  data\entity2id.txt ^
  data\matches-v5-enwiki-20200920.db ^
  data\contexts-v7-enwiki-20200920-100-500-dev.db ^
  --context-size 500 ^
  --crop-sentences ^
  --csv-file data\contexts-v7-enwiki-20200920-100-500-dev.csv ^
  --limit-contexts 100 ^
  --limit-entities 10 ^
  --overwrite ^
  --random-seed 0

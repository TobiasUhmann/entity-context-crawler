set PYTHONPATH=src\
python -u src\sam.py build-contexts-db ^
  data\wikidata-v1-2020-12-31.json ^
  data\qid-to-rid-v1-2020-12-31.txt ^
  data\matches-v5-enwiki-20200920.db ^
  data\contexts-v7-enwiki-20200920-100-500.db ^
  --context-size 500 ^
  --crop-sentences ^
  --csv-file data\contexts-v7-enwiki-20200920-100-500.csv ^
  --limit-contexts 100

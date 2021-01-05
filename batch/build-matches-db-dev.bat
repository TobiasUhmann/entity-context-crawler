set PYTHONPATH=src\
set PYTHONHASHSEED=0
python -u src\sam.py build-matches-db ^
  data\enwiki-20200920.xml ^
  data\wikidata-v1-2020-12-31.json ^
  data\matches-v5-enwiki-20200920-dev.db ^
  --limit-pages 1000 ^
  --overwrite ^
  --random-seed 0

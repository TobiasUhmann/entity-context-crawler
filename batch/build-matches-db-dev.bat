set PYTHONPATH=src\
set PYTHONHASHSEED=0
python -u src\sam.py build-matches-db ^
  data\enwiki-20200920.xml ^
  data\entity2wikidata.json ^
  data\matches-v4-enwiki-20200920-dev.db ^
  --limit-pages 1000 ^
  --overwrite ^
  --random-seed 0

set PYTHONPATH=src\
python -u src\sam.py build-matches-db ^
  data\enwiki-20200920.xml ^
  data\wikidata-v1-2020-12-31.json ^
  data\matches-v6-2020-12-31.db ^
  --in-memory

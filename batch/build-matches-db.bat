set PYTHONPATH=src\
python -u src\sam.py build-matches-db ^
  data\enwiki-20200920.xml ^
  data\entity2wikidata.json ^
  data\matches-v3-enwiki-20200920.db ^
  --in-memory

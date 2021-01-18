set PYTHONPATH=src\
python -u src\sam.py build-matches-db ^
  data\enwiki-20200920.xml ^
  data\wikidata-v1-codex.json ^
  data\matches-v6-codex.db ^
  --in-memory

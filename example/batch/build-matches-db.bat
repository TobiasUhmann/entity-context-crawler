set PYTHONPATH=src\
python -u src\sam.py build-matches-db ^
  data\enwiki-20200920.xml ^
  data\wikidata-codex.json ^
  data\matches-codex.db ^
  --in-memory

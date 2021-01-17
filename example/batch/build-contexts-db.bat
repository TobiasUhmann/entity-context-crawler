set PYTHONPATH=src\
python -u src\sam.py build-contexts-db ^
  data\wikidata-v1-codex.json ^
  data\qid-to-rid-v1-codex.txt ^
  data\matches-v6-codex.db ^
  data\contexts-v7-codex.db ^
  --context-size 500 ^
  --crop-sentences ^
  --csv-file data\contexts-v7-codex.csv ^
  --limit-contexts 100

set PYTHONPATH=src\
python -u src\sam.py query-es-test ^
  cw-contexts-v7-codex ^
  data\ow-contexts-v7-codex.db ^
  --limit-entities 10

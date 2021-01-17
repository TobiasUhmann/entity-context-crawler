set PYTHONPATH=src\
python -u src\sam.py query-es-test ^
  cw-contexts-codex ^
  data\ow-contexts-codex.db ^
  --limit-entities 10

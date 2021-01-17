set PYTHONPATH=src\
python -u src\sam.py build-es-test ^
  data\contexts-v7-codex.db ^
  cw-contexts-v7-codex ^
  data\ow-contexts-v7-codex.db ^
  --limit-contexts 100

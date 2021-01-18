set PYTHONPATH=src\
python -u src\sam.py build-es-test ^
  data\contexts-v8-codex.db ^
  cw-contexts-v8-codex ^
  data\ow-contexts-v8-codex.db ^
  --limit-contexts 100

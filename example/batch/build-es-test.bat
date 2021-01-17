set PYTHONPATH=src\
python -u src\sam.py build-es-test ^
  data\contexts-codex.db ^
  cw-contexts-codex ^
  data\ow-contexts-codex.db ^
  --limit-contexts 100

set PYTHONPATH=src\
set PYTHONHASHSEED=0
python -u src\sam.py build-es-test ^
  data\contexts-codex.db ^
  cw-contexts-codex-dev ^
  data\ow-contexts-codex-dev.db ^
  --limit-contexts 100 ^
  --overwrite ^
  --random-seed 0

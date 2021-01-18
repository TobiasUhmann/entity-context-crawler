set PYTHONPATH=src\
set PYTHONHASHSEED=0
python -u src\sam.py build-es-test ^
  data\contexts-v8-codex.db ^
  cw-contexts-v8-codex-dev ^
  data\ow-contexts-v8-codex-dev.db ^
  --limit-contexts 100 ^
  --overwrite ^
  --random-seed 0

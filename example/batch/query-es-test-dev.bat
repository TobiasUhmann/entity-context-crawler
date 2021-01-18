set PYTHONPATH=src\
set PYTHONHASHSEED=0
python -u src\sam.py query-es-test ^
  cw-contexts-v8-codex ^
  data\ow-contexts-v8-codex.db ^
  --limit-entities 10 ^
  --random-seed 0

set PYTHONPATH=src\
set PYTHONHASHSEED=0
python -u src\sam.py query-es-test ^
  cw-contexts-codex ^
  data\ow-contexts-codex.db ^
  --limit-entities 10 ^
  --random-seed 0

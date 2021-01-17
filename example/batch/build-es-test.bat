set PYTHONPATH=src\
python -u src\sam.py build-es-test ^
  data\contexts-v7-2020-12-31.db ^
  cw-contexts-v7-2020-12-31 ^
  data\ow-contexts-v7-2020-12-31.db ^
  --limit-contexts 100

set PYTHONPATH=src\
set PYTHONHASHSEED=0
python -u src\sam.py build-baseline ^
  data\irt.fb.irt\ ^
  baseline-irt-fb-irt-dev ^
  --output-dir 'data\' ^
  --overwrite ^
  --random-seed 0

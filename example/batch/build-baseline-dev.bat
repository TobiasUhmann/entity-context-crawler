set PYTHONPATH=src\
set PYTHONHASHSEED=0
python -u src\sam.py build-baseline ^
  data\irt.fb.irt.30.clean\ ^
  baseline-v1-irt-fb-irt-30-clean-dev ^
  --output-dir 'data\' ^
  --overwrite ^
  --random-seed 0

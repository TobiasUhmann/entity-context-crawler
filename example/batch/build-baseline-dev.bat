set PYTHONPATH=src\
set PYTHONHASHSEED=0
python -u src\sam.py build-baseline ^
  data\irt.fb.30.26041992.clean\ ^
  baseline-v1-irt-fb-30-26041992-clean-dev ^
  --output-dir 'data\' ^
  --overwrite ^
  --random-seed 0

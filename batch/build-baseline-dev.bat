set PYTHONPATH=src\
set PYTHONHASHSEED=0
python -u src\sam.py build-baseline ^
  data\oke.fb15k237_26041992_100_clean\ ^
  baseline-v1-26041992-100-clean-dev ^
  --output-dir 'data\' ^
  --overwrite ^
  --random-seed 0

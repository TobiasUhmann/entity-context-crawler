set PYTHONPATH=src\
set PYTHONHASHSEED=0
python -u src\sam.py build-baseline ^
  data\oke.fb15k237_26041992_100\ ^
  baseline-100-dev-oke.fb15k237_26041992_100 ^
  --limit-contexts 100 ^
  --output-dir 'data\' ^
  --overwrite ^
  --random-seed 0

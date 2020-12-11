set PYTHONPATH=src\
set PYTHONHASHSEED=0
python -u src\sam.py eval-model ^
  baseline ^
  data\oke.fb15k237_26041992_100_masked\ ^
  --baseline-dir 'data\' ^
  --baseline-name baseline-v1-26041992-100-masked
  --random-seed 0

set PYTHONPATH=src\
python -u src\sam.py eval-model ^
  baseline ^
  data\irt.fb.irt\ ^
  --baseline-dir 'data\baseline-irt-fb-irt\' ^
  --baseline-name baseline-irt-fb-irt

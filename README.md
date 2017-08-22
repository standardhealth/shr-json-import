# shr-json-to-cameo
This python script is used to convert the json models back into Cameo code.

From the terminal, run with:
```
python json2cameo.py sample_data/shr_spec.json
```

To choose a custom destination:
```
python json2cameo.py sample_data/shr_spec.json output/
```

From a python script, run with:
```
>>> j2c = JsonToCameo(filename='sample_data/shr_spec.json', output='out/')
>>> j2c.all_files()
```

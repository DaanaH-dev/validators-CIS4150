
## Using card as a example: 

```
pytest ./tests/card_test.py -v
```

### Check Code coverage:

```
coverage run --branch --source=validators.card -m pytest ./tests/card_test.py
coverage report -m
```

Need to change the source to be the appropriate validator in the folder

Will need to install pytest and coverage in order to run this code.

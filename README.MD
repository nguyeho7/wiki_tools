# Readme
This repo contains a set of tools to parse and convert various json formats between personal wiki projects and DayOne, a MacOS/iOS-only journalling app.

Currently plans are for:
* DayOne to TiddlyWiki5 (tw5)
  * Use spacy for entity tagging to generate potential TW5 links
  * Use Google Vision API for advanced image tagging 
* TiddlyWiki5 to DocuWiki

## DayOne to TW5
### Instalation
create a suitable virtualenv or conda env
```
pip install -r requirements.txt
```
Install spacy models (sm for unit test, md for actual use)
```
python -m spacy download en_core_web_sm 
python -m spacy download en_core_web_md
```
Run unit tests
```
python -m unittest test/dayone_to_tw5_test.py
```

### Usage
* Modify name_expand
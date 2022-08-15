import importlib
from typing import Optional
from fastapi import FastAPI, Request, Query, status
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from spacy.lang.xx import Language as XXLanguage

from deep_translator import GoogleTranslator
import requests


app = FastAPI ()

templates = Jinja2Templates(directory="templates")

translator = GoogleTranslator()

n_c = translator._languages
c_n = dict([tuple(reversed(item)) for item in n_c.items()])

spacy_languages = {"xx": XXLanguage()}

@app.get("/")
async def index_get(request: Request, source: str = Query(""), target: str = Query("en"), text: str = Query("")):
    source = get_lang(request.headers["accept-language"], c_n)
    return templates.TemplateResponse("index.html", {"request": request, "source": source, "target": target, "text": text, "languages": n_c})

@app.get("/translate/")
async def translate(request: Request, source: str = Query(...), target: str = Query(...), text: str = Query(...)):
    translator.source = source
    translator.target = target
    t = translator.translate(text)
    html_response = templates.TemplateResponse("translate_result.html", {"request": request, "result": t, "items": get_links_dict(t, target)})
    return JSONResponse({"result": t, "html": str(html_response.body.decode("utf-8"))})

def get_links_dict(text, language):
    results = []
    for i in get_tokenizer(language)(text).to_json()["tokens"]:
        token = text[i["start"]:i["end"]]
        link = f"https://en.wiktionary.org/wiki/{token.lower()}#{c_n[language].title()}"
        results.append(
            {
                "word": token,
                "link": link,
                "exist": requests.get(link).status_code == 200,
            }
        )
    return results

def get_lang(string, languages):
    for l in string.split(","):
        if ";" in l:
            l = l.split(";")[0]
        if l in languages:
            return l
    return "it"

def get_tokenizer(language):
    if language in spacy_languages:
        return spacy_languages[language].tokenizer
    try:
        module = importlib.import_module(f"spacy.lang.{language}")
        spacy_language = getattr(module, c_n[language].title())()
        spacy_languages[language] = spacy_language
        return spacy_language.tokenizer
    except ModuleNotFoundError:
        spacy_languages[language] = spacy_languages["xx"]
        return spacy_languages["xx"].tokenizer

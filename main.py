from typing import Optional
from fastapi import FastAPI, Request, Query, status
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from deep_translator import GoogleTranslator
import requests


app = FastAPI ()

templates = Jinja2Templates(directory="templates")

translator = GoogleTranslator()

n_c = translator._languages
c_n = dict([tuple(reversed(item)) for item in n_c.items()])

@app.get("/")
async def index_get(request: Request, source: str = Query(""), target: str = Query("en"), text: str = Query("")):
    source = get_lang(request.headers["accept-language"], c_n)
    return templates.TemplateResponse("index.html", {"request": request, "source": source, "target": target, "text": text, "languages": n_c})

@app.get("/translate/")
async def translate(request: Request, source: str = Query(...), target: str = Query(...), text: str = Query(...)):
    translator.source = source
    translator.target = target
    t = translator.translate(text)
    html_response = templates.TemplateResponse("translate_result.html", {"request": request, "result": t, "items": get_links_dict(t, c_n[target])})
    return JSONResponse({"result": t, "html": str(html_response.body.decode("utf-8"))})

def get_links_dict(text, language):
    results = []
    for i in text.split(" "):
        link = f"https://en.wiktionary.org/wiki/{i.lower()}#{language.title()}"
        results.append(
            {
                "word": i,
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

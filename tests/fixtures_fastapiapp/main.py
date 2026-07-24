"""Pulseboard: a tiny status board used as sharepack's FastAPI fixture."""
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

ITEMS = [
    {"id": 1, "name": "ingest pipeline", "state": "up"},
    {"id": 2, "name": "nightly backup", "state": "up"},
    {"id": 3, "name": "geo cache", "state": "down"},
]


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(
        request, "index.html", {"items": ITEMS}
    )


@app.post("/add")
async def add(name: str = Form(...), state: str = Form("up")):
    ITEMS.append({"id": len(ITEMS) + 1, "name": name, "state": state})
    return RedirectResponse(url="/", status_code=303)


@app.get("/item/{item_id}")
async def detail(request: Request, item_id: int):
    for item in ITEMS:
        if item["id"] == item_id:
            return templates.TemplateResponse(
                request, "detail.html", {"item": item}
            )
    raise HTTPException(status_code=404, detail="no such item")


@app.get("/api/items")
async def api_items():
    return ITEMS

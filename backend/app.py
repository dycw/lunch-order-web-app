import datetime as dt
from getpass import getuser

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def home(*, request: Request) -> Response:
    name = "index.html"
    context = {
        "request": request,
        "username": getuser(),
        "now": dt.datetime.now().isoformat(),
    }
    return templates.TemplateResponse(name=name, context=context)

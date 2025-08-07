from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pandas as pd
import io
import chardet

app = FastAPI()

# Static files & template setup
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/", response_class=HTMLResponse)
async def upload_csv(request: Request, file: UploadFile = File(...)):
    try:
        # 1. File Type Check
        if not file.filename.endswith(".csv"):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed.")

        # 2. File Size Check
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large (max 2MB).")

        # 3. Encoding Detection
        # encoding_result = chardet.detect(contents)
        # encoding = encoding_result['encoding'] or 'utf-8'

        # try:
        # decoded_content = contents.decode(encoding)
        # except Exception:
        #     raise HTTPException(status_code=400, detail="Failed to decode file. Ensure it's valid UTF-8/CSV.")

        # 4. Parse CSV
        # try:
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
        # except Exception:
        #     raise HTTPException(status_code=400, detail="Invalid CSV format.")

        # 5. Tabulator-ready data
        data = df.fillna("").to_dict(orient="records")
        columns = [{"title": col, "field": col, "editor": "input"} for col in df.columns]

        # 6. Numeric Summary
        describe_html = ""
        numeric_df = df.select_dtypes(include="number")
        if not numeric_df.empty:
            describe_df = numeric_df.describe().round(2)
            describe_html = describe_df.to_html(classes="table-auto border border-collapse", border=1)

        return templates.TemplateResponse("index.html", {
            "request": request,
            "data": data,
            "columns": columns,
            "describe": describe_html
        })

    except HTTPException as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": e.detail
        })
    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": f"Unexpected error: {str(e)}"
        })

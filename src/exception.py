from fastapi import Request
from fastapi.exceptions import RequestValidationError
from starlette import status
from starlette.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

async def validation_exception_handler(request: Request, exc:RequestValidationError):
    form_data = await request.form()
    return templates.TemplateResponse("/patients/create.html", {
        "request":request,
        "errors":exc.errors(),
        "form_data":form_data
    }, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
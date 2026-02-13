import uuid
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware


from app.api import millex
from app.api import search
from app.api.chat import router as chat_router

from app.core.errors import ERRORS
from app.core.exceptions import APIException

app = FastAPI(title="URL Ingestor", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(millex.router, prefix="/api/v1")

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = str(uuid.uuid4())
    response = await call_next(request)
    return response

@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    status_code, message = ERRORS.get(
        exc.error_code,
        ERRORS["INTERNAL_SERVER_ERROR"]
    )

    request_id = getattr(request.state, "request_id", None)

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "error",
            "error_code": exc.error_code,
            "message": message,
            "request_id": request_id
        }
    )



app.include_router(search.router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")



@app.get("/health")
def health():
    return {"status": "ok"}

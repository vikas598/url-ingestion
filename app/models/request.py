from pydantic import BaseModel, HttpUrl

class ProductIngestRequest(BaseModel):
    url: HttpUrl

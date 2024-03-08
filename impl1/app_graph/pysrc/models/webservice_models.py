from pydantic import BaseModel
from typing import Any, List, Optional

# This module contains the several Pydantic "models" that define both the
# request and response payloads for the web endpoints in this application.
# Think of these models as "interfaces" that define the "shapes" of actual
# objects.  Pydantic models are an interesting feature of the FastAPI
# webframework.  Using these models, FastAPI can automatically generate
# OpenAPI/Swagger request/response endpoint documentation.
#
# See https://fastapi.tiangolo.com/tutorial/response-model/
# See https://fastapi.tiangolo.com/tutorial/body/
#
# Chris Joakim, Microsoft, 2024


class PingModel(BaseModel):
    epoch: float


class LivenessModel(BaseModel):
    epoch: float
    alive: bool
    rows_read: int


class OwlInfoModel(BaseModel):
    ontology_file: str
    owl: str
    epoch: float
    error: str | None


class SparqlQueryRequestModel(BaseModel):
    sparql: str


class SparqlQueryResponseModel(BaseModel):
    sparql: str
    # results: list[dict] = []
    # results: Optional[List[int]] = None
    results: Any = None
    elapsed: float
    error: str | None

    # FastAPI may have a bug currently re: validating response data
    # containing lists, or lists of dicts.  Therefore, using an Any above.


class SparqlBomQueryRequestModel(BaseModel):
    libname: str
    libtype: str
    max_depth: int


class SparqlBomQueryResponseModel(BaseModel):
    libname: str
    libtype: str
    max_depth: int
    actual_depth: int
    bom_libs: dict | None
    elapsed: float
    error: str | None


class SparqlGenerationRequestModel(BaseModel):
    session_id: str | None
    natural_language: str
    owl: str


class SparqlGenerationResponseModel(BaseModel):
    session_id: str | None
    natural_language: str
    completion_id: str
    completion_model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    epoch: int
    elapsed: float
    sparql: str
    error: str | None


class DocumentsVSResultsModel(BaseModel):
    libtype: str
    libname: str
    count: int
    doc: dict | None
    results: list
    elapsed: float
    error: str | None


class VectorizeRequestModel(BaseModel):
    session_id: str | None
    text: str


class VectorizeResponseModel(BaseModel):
    session_id: str | None
    text: str
    embeddings: list
    elapsed: float
    error: str | None

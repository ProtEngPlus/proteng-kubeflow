from pydantic import BaseModel, HttpUrl

class Protein(BaseModel):
    sequence: str
    fitness: float

class RequestTopModelBody(BaseModel):
    proteins: list[Protein]
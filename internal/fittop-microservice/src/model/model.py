from pydantic import BaseModel, HttpUrl

class Protein(BaseModel):
    sequence: str
    fitness: float

class requestTopModelBody(BaseModel):
    proteins: list[Protein]
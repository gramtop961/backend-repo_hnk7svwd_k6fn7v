from __future__ import annotations

import json
from typing import Any, Dict, Optional

from fastapi import FastAPI, Query
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from database import create_document, get_documents, count_documents
from schemas import Project

app = FastAPI(title="IDF Projets BTP API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProjectsResponse(BaseModel):
    items: list[dict]
    total: int
    page: int
    page_size: int


@app.get("/test")
async def test() -> dict:
    return {"status": "ok"}


@app.post("/projects", response_model=dict)
async def create_project(project: Project) -> dict:
    doc = await create_document("project", project.model_dump())
    return doc


@app.get("/projects", response_model=ProjectsResponse)
async def list_projects(
    q: Optional[str] = None,
    status: Optional[str] = None,
    typologie: Optional[str] = None,
    min_budget: Optional[float] = None,
    max_budget: Optional[float] = None,
    bbox: Optional[str] = Query(
        None,
        description="minLon,minLat,maxLon,maxLat",
    ),
    polygon: Optional[str] = Query(
        None,
        description="JSON string of [[lon,lat], ...] coordinates (closed or open, will be closed)",
    ),
    date_debut_from: Optional[str] = None,
    date_debut_to: Optional[str] = None,
    acteur: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
) -> ProjectsResponse:
    # Build MongoDB filter
    f: Dict[str, Any] = {}
    ors = []
    if q:
        ors.extend([
            {"name": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
        ])
    if status:
        f["status"] = status
    if typologie:
        f["typologie"] = typologie
    if min_budget is not None or max_budget is not None:
        r: Dict[str, Any] = {}
        if min_budget is not None:
            r["$gte"] = min_budget
        if max_budget is not None:
            r["$lte"] = max_budget
        f["budget"] = r
    if date_debut_from or date_debut_to:
        dr: Dict[str, Any] = {}
        if date_debut_from:
            dr["$gte"] = date_debut_from
        if date_debut_to:
            dr["$lte"] = date_debut_to
        f["date_debut"] = dr
    if acteur:
        ors.extend([
            {"maitrise_ouvrage": {"$regex": acteur, "$options": "i"}},
            {"architecte": {"$regex": acteur, "$options": "i"}},
            {"entreprise": {"$regex": acteur, "$options": "i"}},
        ])
    if ors:
        f["$or"] = ors

    # Spatial filters: polygon has priority over bbox
    if polygon:
        try:
            coords = json.loads(polygon)
            if isinstance(coords, list) and len(coords) >= 3:
                # ensure closed ring
                if coords[0] != coords[-1]:
                    coords.append(coords[0])
                f["location"] = {"$geoWithin": {"$polygon": coords}}
        except Exception:
            pass
    elif bbox:
        try:
            min_lon, min_lat, max_lon, max_lat = map(float, bbox.split(","))
            f["location"] = {
                "$geoWithin": {
                    "$box": [
                        [min_lon, min_lat],
                        [max_lon, max_lat],
                    ]
                }
            }
        except Exception:
            pass

    # Pagination
    page = max(1, page)
    page_size = max(1, min(page_size, 200))
    skip = (page - 1) * page_size

    items = await get_documents("project", f, limit=page_size, skip=skip)
    total = await count_documents("project", f)

    return ProjectsResponse(items=items, total=total, page=page, page_size=page_size)

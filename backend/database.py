from __future__ import annotations

import os
from typing import Any, Dict, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pydantic import BaseModel

MONGO_URL = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DATABASE_NAME", "appdb")

_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


async def get_db() -> AsyncIOMotorDatabase:
    global _client, _db
    if _db is None:
        _client = AsyncIOMotorClient(MONGO_URL)
        _db = _client[DB_NAME]
    return _db


class BaseDoc(BaseModel):
    id: Optional[str] = None


async def create_document(collection: str, data: Dict[str, Any]) -> Dict[str, Any]:
    db = await get_db()
    res = await db[collection].insert_one({**data})
    doc = await db[collection].find_one({"_id": res.inserted_id})
    if doc is None:
        return data
    doc["id"] = str(doc.pop("_id"))
    return doc


async def get_documents(
    collection: str,
    filter_dict: Dict[str, Any] | None = None,
    limit: int = 100,
    skip: int = 0,
    sort: Optional[list[tuple[str, int]]] = None,
) -> list[Dict[str, Any]]:
    db = await get_db()
    cursor = db[collection].find(filter_dict or {}).skip(skip).limit(limit)
    if sort:
        cursor = cursor.sort(sort)
    docs = []
    async for d in cursor:
        d["id"] = str(d.pop("_id"))
        docs.append(d)
    return docs


async def count_documents(collection: str, filter_dict: Dict[str, Any] | None = None) -> int:
    db = await get_db()
    return await db[collection].count_documents(filter_dict or {})

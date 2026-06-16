import httpx
import os

VALHALLA_URL = os.getenv("VALHALLA_URL", "http://localhost:8003")

async def trace_attributes(shape: list) -> list:
    body = {
        "shape": shape,
        "costing": "auto",
        "shape_match": "map_snap",
        "filters": {
            "attributes": [
                "edge.way_id",
                "edge.id",
                "edge.length",
                "edge.begin_heading",
                "edge.end_heading"
            ],
            "action": "include"
        }
    }
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(f"{VALHALLA_URL}/trace_attributes", json=body)
        r.raise_for_status()
        return r.json().get("edges", [])

async def locate_nearest_edge(lat: float, lon: float) -> dict:
    body = {
        "locations": [{"lat": lat, "lon": lon}],
        "costing": "auto",
        "verbose": True
    }
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(f"{VALHALLA_URL}/locate", json=body)
        r.raise_for_status()
        edges = r.json()[0].get("edges", [])
        return {"way_id": edges[0]["way_id"]} if edges else {"way_id": None}

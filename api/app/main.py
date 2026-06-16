from fastapi import FastAPI
from dotenv import load_dotenv
load_dotenv()

from .schemas import MatchRequest, MatchResponse, SegmentInfo, CameraAlert
from .valhalla_client import trace_attributes
from .db import cameras_on_segment

app = FastAPI(title="CamCrusher API")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "camcrusher-api"}

@app.post("/v1/match", response_model=MatchResponse)
async def match(req: MatchRequest):
    shape = [{"lat": p.lat, "lon": p.lon} for p in req.points]
    edges = await trace_attributes(shape)
    if not edges:
        return MatchResponse(current_segment=None, cameras_ahead=[])

    last = edges[-1]
    way_id = last["way_id"]
    heading = last.get("begin_heading", 0)
    direction = 0 if heading < 180 else 1

    cams_raw = await cameras_on_segment(way_id, direction)
    cameras_ahead = [
        CameraAlert(
            camera_id=c["camera_id"],
            spot_type=c["spot_type"],
            speed_limit=c.get("speed_limit"),
            distance_m=None,
            same_direction=True,
            bearing=c["bearing"],
            lat=c["lat"],
            lon=c["lon"],
        )
        for c in cams_raw
    ]

    return MatchResponse(
        current_segment=SegmentInfo(way_id=way_id, direction=direction),
        cameras_ahead=cameras_ahead,
    )

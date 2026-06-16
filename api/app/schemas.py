from pydantic import BaseModel
from typing import List, Optional

class GPSPoint(BaseModel):
    lat: float
    lon: float
    t: Optional[float] = None

class MatchRequest(BaseModel):
    points: List[GPSPoint]

class CameraAlert(BaseModel):
    camera_id: str
    spot_type: str
    speed_limit: Optional[int]
    distance_m: Optional[float]
    same_direction: bool
    bearing: int
    lat: float
    lon: float

class SegmentInfo(BaseModel):
    way_id: int
    direction: Optional[int]

class MatchResponse(BaseModel):
    current_segment: Optional[SegmentInfo]
    cameras_ahead: List[CameraAlert]

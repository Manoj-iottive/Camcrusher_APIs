import os
import asyncpg
import json
from typing import List, Optional
from datetime import datetime, timezone

DATABASE_URL = os.getenv("DATABASE_URL")

def parse_dt(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except:
        return None

async def get_conn():
    url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    return await asyncpg.connect(url)

async def cameras_on_segment(way_id: int, direction: Optional[int]) -> List[dict]:
    conn = await get_conn()
    try:
        rows = await conn.fetch("""
            SELECT c.camera_id, c.spot_type, c.speed_limit,
                   c.bearing, c.lat, c.lon
            FROM cc_camera c
            JOIN cc_segment s ON c.cc_segment_id = s.cc_segment_id
            WHERE s.way_id = $1
              AND (c.expiry_date IS NULL OR c.expiry_date > now())
        """, way_id)
        return [dict(r) for r in rows]
    finally:
        await conn.close()

async def upsert_segment(way_id: int, start_offset: float,
                          end_offset: float, direction: Optional[int],
                          geometry_wkt: Optional[str]) -> int:
    conn = await get_conn()
    try:
        row = await conn.fetchrow("""
            INSERT INTO cc_segment (way_id, start_offset, end_offset, direction, geom)
            VALUES ($1, $2, $3, $4,
                CASE WHEN $5::text IS NOT NULL
                     THEN ST_GeomFromText($5, 4326)
                     ELSE NULL END)
            ON CONFLICT (way_id, start_offset, end_offset, direction)
            DO UPDATE SET direction = EXCLUDED.direction
            RETURNING cc_segment_id
        """, way_id, start_offset, end_offset, direction, geometry_wkt)
        return row["cc_segment_id"]
    finally:
        await conn.close()

async def upsert_camera(camera_id: str, cc_segment_id: int,
                         spot_type: str, speed_limit: Optional[int],
                         bearing: int, lat: float, lon: float,
                         open_lr: str, expiry_date, match_confidence: str,
                         last_update=None):
    conn = await get_conn()
    try:
        await conn.execute("""
            INSERT INTO cc_camera (camera_id, cc_segment_id, spot_type, speed_limit,
                bearing, lat, lon, open_lr, expiry_date, match_confidence, last_update)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
            ON CONFLICT (camera_id) DO UPDATE SET
                cc_segment_id = EXCLUDED.cc_segment_id,
                spot_type = EXCLUDED.spot_type,
                speed_limit = EXCLUDED.speed_limit,
                bearing = EXCLUDED.bearing,
                match_confidence = EXCLUDED.match_confidence,
                last_update = EXCLUDED.last_update
        """, camera_id, cc_segment_id, spot_type, speed_limit,
             bearing, lat, lon, open_lr,
             parse_dt(expiry_date),
             match_confidence,
             parse_dt(last_update))
    finally:
        await conn.close()

async def enqueue_review(camera_id: str, reason: str, payload: dict):
    conn = await get_conn()
    try:
        await conn.execute("""
            INSERT INTO review_queue (camera_id, reason, payload)
            VALUES ($1, $2, $3)
            ON CONFLICT (camera_id) DO NOTHING
        """, camera_id, reason, json.dumps(payload))
    finally:
        await conn.close()

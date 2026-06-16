import os
from datetime import datetime, timezone
from typing import Optional
from .openlr_decoder import decode_tomtom_openlr, snap_to_valhalla, haversine_m
from .db import upsert_segment, upsert_camera, enqueue_review

VALHALLA_URL = os.getenv("VALHALLA_URL", "http://localhost:8003")
CONF_THRESHOLD = 0.7
SANITY_METERS = 50

async def ingest_camera(cam: dict) -> str:
    # 1. Expiry filter
    exp = cam.get("expiryDate")
    if exp:
        try:
            exp_dt = datetime.fromisoformat(exp.replace("Z", "+00:00"))
            if exp_dt < datetime.now(timezone.utc):
                return "expired"
        except:
            pass

    coords = cam.get("spotLocation", {}).get("coordinates", [])
    if not coords or len(coords) < 2:
        await enqueue_review(cam["id"], "missing_coordinates", cam)
        return "fallback"

    lon, lat = coords[0], coords[1]
    open_lr = cam.get("openLR", "")

    seg_id = None
    confidence = "fallback"

    # 2. Try OpenLR decode
    if open_lr:
        decoded = decode_tomtom_openlr(open_lr)
        if decoded.get("matched"):
            lrp = decoded["first_lrp"]
            dist = haversine_m(lat, lon, lrp["lat"], lrp["lon"])
            if dist <= SANITY_METERS:
                snap = await snap_to_valhalla(lrp["lat"], lrp["lon"], VALHALLA_URL)
                if snap.get("way_id"):
                    seg_id = await upsert_segment(
                        way_id=snap["way_id"],
                        start_offset=decoded.get("positive_offset", 0.0),
                        end_offset=1.0 - decoded.get("negative_offset", 0.0),
                        direction=0 if decoded.get("bearing", 0) < 180 else 1,
                        geometry_wkt=decoded.get("geometry")
                    )
                    confidence = "openlr"

    # 3. Fallback: snap camera lat/lon directly
    if seg_id is None:
        snap = await snap_to_valhalla(lat, lon, VALHALLA_URL)
        if snap.get("way_id"):
            seg_id = await upsert_segment(
                way_id=snap["way_id"],
                start_offset=0.0,
                end_offset=1.0,
                direction=0 if cam.get("bearing", 0) < 180 else 1,
                geometry_wkt=None
            )
        await enqueue_review(cam["id"], "openlr_fallback", {
            "open_lr": open_lr, "lat": lat, "lon": lon
        })

    if seg_id is None:
        await enqueue_review(cam["id"], "no_segment", cam)
        return "fallback"

    # 4. Upsert camera
    await upsert_camera(
        camera_id=cam["id"],
        cc_segment_id=seg_id,
        spot_type=cam.get("spotType", "UNKNOWN"),
        speed_limit=cam.get("speedLimit"),
        bearing=cam.get("bearing", 0),
        lat=lat,
        lon=lon,
        open_lr=open_lr,
        expiry_date=exp,
        match_confidence=confidence,
        last_update=cam.get("lastUpdate")
    )
    return confidence

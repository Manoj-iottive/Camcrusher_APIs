import base64
import math

def _signed24(b0, b1, b2):
    val = (b0 << 16) | (b1 << 8) | b2
    if val >= 0x800000:
        val -= 0x1000000
    return val

def _signed16(b0, b1):
    val = (b0 << 8) | b1
    if val >= 0x8000:
        val -= 0x10000
    return val

def decode_tomtom_openlr(base64_str: str) -> dict:
    try:
        raw = base64.b64decode(base64_str)
        if len(raw) != 17:
            return {"matched": False, "reason": f"Expected 17 bytes, got {len(raw)}"}

        lon1_deg = _signed24(raw[1], raw[2], raw[3]) * 360.0 / (1 << 24)
        lat1_deg = _signed24(raw[4], raw[5], raw[6]) * 360.0 / (1 << 24)

        attr1 = raw[7]
        fow1  = (attr1 >> 3) & 0x07
        frc1  = attr1 & 0x07

        attr2 = raw[8]
        bear1 = (attr2 & 0x1F) * 11.25

        dlon_deg = _signed16(raw[9],  raw[10]) * 360.0 / (1 << 24)
        dlat_deg = _signed16(raw[11], raw[12]) * 360.0 / (1 << 24)

        lon2_deg = lon1_deg + dlon_deg
        lat2_deg = lat1_deg + dlat_deg

        pos_offset = raw[15] / 256.0
        neg_offset = raw[16] / 256.0

        return {
            "matched": True,
            "first_lrp": {"lon": lon1_deg, "lat": lat1_deg},
            "last_lrp":  {"lon": lon2_deg, "lat": lat2_deg},
            "bearing": bear1,
            "frc": frc1,
            "fow": fow1,
            "positive_offset": pos_offset,
            "negative_offset": neg_offset,
            "geometry": f"LINESTRING({lon1_deg} {lat1_deg}, {lon2_deg} {lat2_deg})",
            "confidence": 0.85,
            "reason": None
        }
    except Exception as e:
        return {"matched": False, "reason": str(e)}


def haversine_m(lat1, lon1, lat2, lon2) -> float:
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


async def snap_to_valhalla(lat: float, lon: float, valhalla_url: str) -> dict:
    import httpx
    body = {
        "locations": [{"lat": lat, "lon": lon}],
        "costing": "auto",
        "verbose": True
    }
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(f"{valhalla_url}/locate", json=body)
        r.raise_for_status()
        edges = r.json()[0].get("edges", [])
        if not edges:
            return {"way_id": None, "confidence": 0.0}
        # way_id is nested inside edge_info
        way_id = edges[0]["edge_info"]["way_id"]
        heading = edges[0].get("heading", 0)
        return {
            "way_id": way_id,
            "heading": heading,
            "confidence": 0.9
        }


async def decode_and_snap(base64_openlr: str, valhalla_url: str) -> dict:
    result = decode_tomtom_openlr(base64_openlr)
    if not result["matched"]:
        return result

    lrp = result["first_lrp"]
    snap = await snap_to_valhalla(lrp["lat"], lrp["lon"], valhalla_url)

    if snap["way_id"] is None:
        return {"matched": False, "reason": "Valhalla snap failed"}

    result["way_ids"] = [snap["way_id"]]
    result["confidence"] = snap["confidence"]
    return result

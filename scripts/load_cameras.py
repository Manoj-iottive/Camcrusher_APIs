import asyncio
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))
from app.ingest import ingest_camera

async def main():
    path = os.path.join(os.path.dirname(__file__), '..', 'TomtomCamera_response.json')
    data = json.load(open(path))
    cameras = data.get("data", data) if isinstance(data, dict) else data

    total = len(cameras)
    stats = {"openlr": 0, "fallback": 0, "expired": 0, "error": 0}
    start = time.time()

    print(f"Starting ingestion of {total} cameras...")

    for i, cam in enumerate(cameras):
        try:
            result = await ingest_camera(cam)
            stats[result] = stats.get(result, 0) + 1
        except Exception as e:
            stats["error"] += 1
            print(f"Error on camera {cam.get('id')}: {e}")

        if (i + 1) % 100 == 0:
            elapsed = time.time() - start
            rate = (i + 1) / elapsed
            remaining = (total - i - 1) / rate
            print(f"Progress: {i+1}/{total} | "
                  f"openlr={stats['openlr']} fallback={stats['fallback']} "
                  f"expired={stats['expired']} error={stats['error']} | "
                  f"ETA: {remaining:.0f}s")

    elapsed = time.time() - start
    print(f"\n{'='*50}")
    print(f"DONE in {elapsed:.1f}s")
    print(f"openlr:   {stats['openlr']} ({stats['openlr']/total*100:.1f}%)")
    print(f"fallback: {stats['fallback']} ({stats['fallback']/total*100:.1f}%)")
    print(f"expired:  {stats['expired']} ({stats['expired']/total*100:.1f}%)")
    print(f"error:    {stats['error']}")

asyncio.run(main())

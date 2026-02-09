from app.core.debug_tools import trace, trace_enabled, brief

import asyncio, base64, json, time
import websockets

URI = "ws://localhost:8000/ws/analyze"
IMG = r"sample.jpg" 

@trace("ws_send_file.main")
async def main():
    with open(IMG, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")

    payload = {
        "type": "analyze",
        "session_id": "s_test",
        "seq": 2,
        "ts_ms": int(time.time() * 1000),
        "image_format": "jpeg",
        "image_b64": b64,
    }

    async with websockets.connect(URI, max_size=20 * 1024 * 1024) as ws:
        await ws.send(json.dumps(payload))
        print("SENT b64_len =", len(b64))
        msg = await ws.recv()
        print("RECV =", msg)

asyncio.run(main())

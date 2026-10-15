"""Script to capture real, high-resolution screenshots of SmartPick AI.

Uses Chrome DevTools Protocol (CDP) natively without external driver dependencies.
Captures:
- home.png
- results.png
- compare.png
- insights.png
- what-if.png
- empty-state.png
- mobile.png
- dark-mode.png
"""

import asyncio
import base64
import json
import logging
import subprocess
import time
import urllib.request
from pathlib import Path

import websockets

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("screenshot_taker")

SCREENSHOTS_DIR = Path("assets/screenshots")
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
TEMP_PROFILE = r"C:\Users\HP\AppData\Local\Temp\chrome_smartpick_ss"


async def send_cdp(ws, method, params=None, msg_id=1):
    payload = {"id": msg_id, "method": method, "params": params or {}}
    await ws.send(json.dumps(payload))
    while True:
        resp = json.loads(await ws.recv())
        if resp.get("id") == msg_id:
            return resp.get("result", {})


async def capture_page_screenshot(ws, filename: str, msg_id_start: int):
    res = await send_cdp(
        ws,
        "Page.captureScreenshot",
        {"format": "png", "captureBeyondViewport": False},
        msg_id=msg_id_start,
    )
    data = base64.b64decode(res["data"])
    out_path = SCREENSHOTS_DIR / filename
    out_path.write_bytes(data)
    logger.info(f"Saved screenshot: {out_path} ({len(data)} bytes)")


async def wait_for_selector(ws, selector: str, timeout: float = 15.0):
    start = time.time()
    mid = 200
    while time.time() - start < timeout:
        mid += 1
        res = await send_cdp(
            ws,
            "Runtime.evaluate",
            {
                "expression": f"document.querySelector('{selector}') !== null",
                "returnByValue": True,
            },
            msg_id=mid,
        )
        if res.get("result", {}).get("value") is True:
            return True
        await asyncio.sleep(0.5)
    return False


async def click_element(ws, selector: str, msg_id: int):
    await send_cdp(
        ws,
        "Runtime.evaluate",
        {
            "expression": f"(() => {{ const el = document.querySelector('{selector}'); if (el) {{ el.click(); return true; }} return false; }})()",
            "returnByValue": True,
        },
        msg_id=msg_id,
    )


async def click_tab_by_text(ws, text: str, msg_id: int):
    await send_cdp(
        ws,
        "Runtime.evaluate",
        {
            "expression": f"""(() => {{
            const tabs = Array.from(document.querySelectorAll('button[data-baseweb="tab"]'));
            const target = tabs.find(t => t.innerText.includes('{text}'));
            if (target) {{ target.click(); return true; }}
            return false;
        }})()""",
            "returnByValue": True,
        },
        msg_id=msg_id,
    )


async def run_captures():
    # 1. Start headless Chrome with remote debugging
    logger.info("Launching Chrome headless with remote debugging port 9222...")
    proc = subprocess.Popen(  # noqa: ASYNC220
        [
            CHROME_PATH,
            "--headless=new",
            "--remote-debugging-port=9222",
            "--disable-gpu",
            "--no-first-run",
            f"--user-data-dir={TEMP_PROFILE}",
            "about:blank",
        ]
    )

    await asyncio.sleep(2)

    try:
        # Create a new tab navigating to http://localhost:8501
        req = urllib.request.Request(
            "http://localhost:9222/json/new?http://localhost:8501", method="PUT"
        )
        tab_info = json.loads(urllib.request.urlopen(req).read().decode())  # noqa: ASYNC210
        ws_url = tab_info["webSocketDebuggerUrl"]
        logger.info(f"Connected to Chrome page via WebSocket: {ws_url}")

        async with websockets.connect(ws_url, max_size=20 * 1024 * 1024) as ws:
            await send_cdp(ws, "Page.enable", {}, msg_id=1)
            await send_cdp(ws, "Runtime.enable", {}, msg_id=2)

            # Set Desktop Viewport
            await send_cdp(
                ws,
                "Emulation.setDeviceMetricsOverride",
                {"width": 1440, "height": 900, "deviceScaleFactor": 1, "mobile": False},
                msg_id=3,
            )

            logger.info("Waiting for Streamlit app to load...")
            await wait_for_selector(ws, "div.smartpick-card", timeout=20.0)
            await asyncio.sleep(3.0)  # Let Plotly and CSS render completely

            # 1. Capture Home / Dark Mode Hero
            logger.info("Capturing home.png and dark-mode.png...")
            await capture_page_screenshot(ws, "home.png", msg_id_start=10)
            await capture_page_screenshot(ws, "dark-mode.png", msg_id_start=11)

            # 2. Results View (Scroll down slightly to focus on recommendations)
            logger.info("Capturing results.png...")
            await send_cdp(
                ws,
                "Runtime.evaluate",
                {"expression": "window.scrollTo(0, 320);"},
                msg_id=12,
            )
            await asyncio.sleep(1.0)
            await capture_page_screenshot(ws, "results.png", msg_id_start=13)

            # 3. Compare View (Tab 2)
            logger.info("Switching to Compare tab...")
            await send_cdp(
                ws,
                "Runtime.evaluate",
                {"expression": "window.scrollTo(0, 0);"},
                msg_id=14,
            )
            await click_tab_by_text(ws, "Compare", msg_id=15)
            await asyncio.sleep(2.5)
            await capture_page_screenshot(ws, "compare.png", msg_id_start=16)

            # 4. Insights View (Tab 5)
            logger.info("Switching to Insights tab...")
            await click_tab_by_text(ws, "Insights", msg_id=17)
            await asyncio.sleep(2.5)
            await capture_page_screenshot(ws, "insights.png", msg_id_start=18)

            # 5. What-If / Why Not View (Tab 4)
            logger.info("Switching to Why Not tab...")
            await click_tab_by_text(ws, "Why Not", msg_id=19)
            await asyncio.sleep(2.5)
            await capture_page_screenshot(ws, "what-if.png", msg_id_start=20)

            # 6. Mobile Viewport (iPhone 14 / Pixel dimension)
            logger.info("Switching to Mobile Viewport (412x915)...")
            await click_tab_by_text(ws, "Recommendations", msg_id=21)
            await asyncio.sleep(1.0)
            await send_cdp(
                ws,
                "Emulation.setDeviceMetricsOverride",
                {"width": 412, "height": 915, "deviceScaleFactor": 2, "mobile": True},
                msg_id=22,
            )
            await asyncio.sleep(2.0)
            await capture_page_screenshot(ws, "mobile.png", msg_id_start=23)

            # 7. Empty State View
            logger.info("Navigating to impossible query to capture empty state...")
            # Restore desktop dimensions
            await send_cdp(
                ws,
                "Emulation.setDeviceMetricsOverride",
                {"width": 1440, "height": 900, "deviceScaleFactor": 1, "mobile": False},
                msg_id=24,
            )
            # Apple has no phones under 20,000 INR
            await send_cdp(
                ws,
                "Page.navigate",
                {
                    "url": "http://localhost:8501/?min_budget=10000&max_budget=20000&brands=Apple"
                },
                msg_id=25,
            )
            await asyncio.sleep(4.0)
            await capture_page_screenshot(ws, "empty-state.png", msg_id_start=26)

            logger.info("All 8 screenshots successfully captured!")

    finally:
        proc.terminate()


if __name__ == "__main__":
    asyncio.run(run_captures())

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from vision_detect import detect_phones_once
from wifi_scan import scan_wifi_devices
from bt_scan import scan_bt_devices

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Phone Detection Web App Running ✅"}

@app.get("/detect")   # ✅ Changed from /scan
def scan_devices():
    wifi_devices = scan_wifi_devices()
    bt_devices = scan_bt_devices()
    vision_count = detect_phones_once()

    estimated = max(len(wifi_devices | bt_devices), vision_count)

    return JSONResponse({
        "wifi_devices": list(wifi_devices),
        "bluetooth_devices": list(bt_devices),
        "vision_detected": vision_count,
        "estimated_phones_in_room": estimated
    })

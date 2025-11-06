# vision_detect.py
import cv2, threading, time, numpy as np
from ultralytics import YOLO
from sort_tracker import SortTracker
from db import insert_detection
import asyncio
from typing import List, Tuple

# model load
MODEL_NAME = "yolov8n.pt"  # small + fast
MODEL_CONF = 0.35
FRAMES_PER_UPDATE = 2      # run detection every N frames (reduce CPU)
CAPTURE_INDEX = 0

model = YOLO(MODEL_NAME)
tracker = SortTracker(max_missed=30, iou_thresh=0.3, appearance_thresh=0.4)

# Shared state
_latest_lock = threading.Lock()
_latest_count = 0
_latest_frame = None
_latest_tracks = {}  # track_id -> box

# helper: compute color histogram descriptor for a box
def compute_descriptor(frame: np.ndarray, box) -> np.ndarray:
    x, y, w, h = box
    x2, y2 = x + w, y + h
    h_img, w_img = frame.shape[:2]
    # clamp
    x = max(0, min(w_img - 1, x)); y = max(0, min(h_img - 1, y))
    x2 = max(0, min(w_img, x2)); y2 = max(0, min(h_img, y2))
    crop = frame[y:y2, x:x2]
    if crop.size == 0:
        return np.zeros(256, dtype=float)
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0,1], None, [16,16], [0,180,0,256])
    hist = hist.flatten()
    return hist

def _boxes_from_results(results) -> List[Tuple[List[int], float, np.ndarray]]:
    detections = []
    if results is None:
        return detections
    # boxes.xyxy, boxes.conf, boxes.cls
    boxes_xyxy = getattr(results, "boxes").xyxy.cpu().numpy() if hasattr(results.boxes.xyxy, "cpu") else results.boxes.xyxy.numpy()
    confs = getattr(results, "boxes").conf.cpu().numpy() if hasattr(results.boxes.conf, "cpu") else results.boxes.conf.numpy()
    cls_ids = getattr(results, "boxes").cls.cpu().numpy().astype(int) if hasattr(results.boxes.cls, "cpu") else results.boxes.cls.numpy().astype(int)

    # find cell phone class indexes
    target_idxs = [k for k,v in model.names.items() if v.lower() in ("cell phone", "cellphone", "phone")]
    target_set = set(target_idxs)

    for b, c, cl in zip(boxes_xyxy, confs, cls_ids):
        if int(cl) in target_set:
            x1, y1, x2, y2 = [int(i) for i in b]
            w = max(1, x2 - x1); h = max(1, y2 - y1)
            detections.append(([x1, y1, w, h], float(c), None))
    return detections

def camera_worker():
    global _latest_count, _latest_frame, _latest_tracks
    cap = cv2.VideoCapture(CAPTURE_INDEX)
    if not cap.isOpened():
        print("Camera open failed in vision_detect.camera_worker")
        return

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.1)
            continue
        frame_idx += 1

        # do detection every FRAMES_PER_UPDATE frames to save CPU
        detections = []
        if frame_idx % FRAMES_PER_UPDATE == 0:
            try:
                results = model.predict(source=frame, conf=MODEL_CONF, verbose=False, max_det=50)[0]
                raw_dets = _boxes_from_results(results)
                # compute descriptors now
                dets_with_desc = []
                for box, conf, _ in raw_dets:
                    desc = compute_descriptor(frame, box)
                    dets_with_desc.append((box, conf, desc))
                detections = dets_with_desc
            except Exception as e:
                print("Vision detect error:", e)
                detections = []

            # update tracker
            tracks = tracker.update(detections)  # returns dict track_id->box
            now_ts = time.strftime("%Y-%m-%d %H:%M:%S")
            # persist detections to DB (async)
            for tid, box in tracks.items():
                # find confidence for this box from detections list (closest IoU)
                best_conf = 0.0
                for b, conf, desc in detections:
                    if iou(b, box) > 0.4:
                        best_conf = max(best_conf, conf)
                # fire and forget DB insertion
                try:
                    asyncio.create_task(insert_detection(now_ts, tid, box, best_conf))
                except Exception:
                    pass

            with _latest_lock:
                _latest_count = len(tracks)
                _latest_tracks = tracks.copy()
                _latest_frame = frame.copy()

        # small sleep so thread kindness
        time.sleep(0.01)

def get_latest():
    with _latest_lock:
        return {"count": _latest_count, "tracks": _latest_tracks.copy()}

def get_mjpeg_frame_bytes(draw_boxes=True):
    with _latest_lock:
        frame = _latest_frame.copy() if _latest_frame is not None else None
        tracks = _latest_tracks.copy()
    if frame is None:
        # return black image
        frame = (255 * np.ones((480, 640, 3), dtype=np.uint8))
    if draw_boxes and tracks:
        for tid, box in tracks.items():
            x, y, w, h = box
            x2, y2 = x + w, y + h
            cv2.rectangle(frame, (x, y), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"ID {tid}", (x, y - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

    ret, jpeg = cv2.imencode(".jpg", frame)
    return jpeg.tobytes()

# start background thread on import
_thread = threading.Thread(target=camera_worker, daemon=True)
_thread.start()

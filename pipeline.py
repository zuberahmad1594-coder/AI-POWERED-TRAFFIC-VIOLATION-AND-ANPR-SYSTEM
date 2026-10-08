import os
import re
import glob
import cv2
import sqlite3
import datetime
from collections import defaultdict, Counter
import easyocr
from ultralytics import YOLO

import violations

CAMERA_ID = "CAM_MUMBAI_01"
LOST_AFTER = 20

VEHICLE_CLASSES = [2, 3, 5, 7]
CLASS_NAMES = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}

os.makedirs("evidence", exist_ok=True)
os.makedirs("challans", exist_ok=True)

# Database Setup with Unique Index to prevent duplicates permanently
db = sqlite3.connect("violations.db")
db.execute("""
CREATE TABLE IF NOT EXISTS violations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT,
    camera_id TEXT,
    video_name TEXT,
    vehicle_type TEXT,
    track_id INTEGER,
    plate TEXT,
    violation_type TEXT,
    image_path TEXT,
    status TEXT DEFAULT 'pending_review',
    challan_path TEXT
)
""")
db.commit()

# Create a unique index so the database itself blocks repeat logs
try:
    db.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_violation 
    ON violations (video_name, track_id, violation_type)
    """)
    db.commit()
except sqlite3.OperationalError:
    pass

print("Loading AI Models...")
vehicle_model = YOLO("yolo11n.pt")
reader = easyocr.Reader(['en'], gpu=False)

TO_DIGIT = {'O': '0', 'I': '1', 'B': '8', 'S': '5', 'Z': '2', 'G': '6'}
TO_ALPHA = {v: k for k, v in TO_DIGIT.items()}
PATTERN = re.compile(r'^[A-Z]{2}\d{2}[A-Z]{1,3}\d{4}$')

def fix_plate(text):
    t = re.sub(r'[^A-Z0-9]', '', text.upper())
    if not (9 <= len(t) <= 10):
        return None
    c = list(t)
    for i in range(len(c)):
        is_digit_pos = i in (2, 3) or i >= len(c) - 4
        c[i] = TO_DIGIT.get(c[i], c[i]) if is_digit_pos else TO_ALPHA.get(c[i], c[i])
    corrected = "".join(c)
    return corrected if PATTERN.match(corrected) else None

def read_plate(crop):
    if crop.shape[0] < 12 or crop.shape[1] < 20:
        return ""
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    out = reader.readtext(gray, allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
    return "".join(t for _, t, c in out if c > 0.35)

def process_single_video(video_path):
    video_file = os.path.basename(video_path)
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"\n==========================================")
    print(f"Processing Feed: {video_file} (Frames: {total_frames})")
    print(f"==========================================")

    # Pre-load existing violations for this video so re-runs never duplicate
    cur = db.cursor()
    cur.execute("SELECT track_id, violation_type FROM violations WHERE video_name=?", (video_file,))
    already_saved = set(cur.fetchall())

    votes = defaultdict(list)
    flags = defaultdict(set)
    best_frame = {}
    last_seen = {}
    vtype_map = {}
    frame_idx = 0

    def log_violation(tid, plate, vtype, v_class):
        # Prevent repeat inserts in memory and in SQLite
        if (tid, vtype) in already_saved:
            return

        path = f"evidence/{video_file}_{tid}_{plate}_{vtype}.jpg"
        frame_to_save = best_frame.get(tid)
        if frame_to_save is not None:
            cv2.imwrite(path, frame_to_save)
        else:
            return

        try:
            cur.execute("""
                INSERT OR IGNORE INTO violations 
                (ts, camera_id, video_name, vehicle_type, track_id, plate, violation_type, image_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), CAMERA_ID, video_file, v_class, tid, plate, vtype, path))
            db.commit()
            already_saved.add((tid, vtype))
            print(f"\n[UNIQUE LOG] {video_file} | {v_class.upper()} #{tid} | {plate} | {vtype}")
        except sqlite3.IntegrityError:
            pass

    while cap.isOpened():
        ok, frame = cap.read()
        if not ok:
            break
        frame_idx += 1

        if frame_idx % 3 != 0:
            continue

        if frame_idx % 20 == 0 or frame_idx >= total_frames - 3:
            print(f"[{video_file}] Frame {frame_idx}/{total_frames} ({(frame_idx/total_frames)*100:.1f}%)", end="\r")

        detections = vehicle_model.track(
            frame, 
            persist=True, 
            classes=VEHICLE_CLASSES, 
            tracker="bytetrack.yaml", 
            imgsz=384,
            verbose=False
        )[0]

        persons_det = vehicle_model(frame, classes=[0], conf=0.35, imgsz=384, verbose=False)[0]
        persons = persons_det.boxes.xyxy.tolist() if persons_det.boxes is not None else []

        if detections.boxes is not None and detections.boxes.id is not None:
            v_boxes = detections.boxes.xyxy.tolist()
            v_ids = detections.boxes.id.int().tolist()
            v_cls = detections.boxes.cls.int().tolist()

            for box, tid, cls_id in zip(v_boxes, v_ids, v_cls):
                last_seen[tid] = frame_idx
                vehicle_kind = CLASS_NAMES.get(cls_id, "vehicle")
                vtype_map[tid] = vehicle_kind

                if violations.check_wrong_side(tid, box):
                    flags[tid].add("WRONG_SIDE")

                if violations.check_illegal_stopping(tid, box):
                    flags[tid].add("ILLEGAL_STOPPING")

                if cls_id == 3:
                    region = violations.rider_region(box)
                    riders = violations.persons_on_bike(persons, region)
                    if violations.check_triple_riding(tid, persons, region):
                        flags[tid].add("TRIPLE_RIDING")
                    if len(riders) >= 1:
                        flags[tid].add("NO_HELMET")
                    if len(riders) >= 2:
                        flags[tid].add("PILLION_NO_HELMET")

                if flags[tid]:
                    best_frame[tid] = frame.copy()

                if flags[tid] and (frame_idx % 9 == 0):
                    bx1, by1, bx2, by2 = map(int, box)
                    plate_crop = frame[int(by1 + 0.45 * (by2 - by1)):by2, bx1:bx2]
                    raw_text = read_plate(plate_crop)
                    cleaned = fix_plate(raw_text)
                    if cleaned:
                        votes[tid].append(cleaned)

                if len(votes[tid]) >= 2:
                    resolved_plate = Counter(votes[tid]).most_common(1)[0][0]
                    for vtype in list(flags[tid]):
                        log_violation(tid, resolved_plate, vtype, vehicle_kind)

        for tid in list(flags.keys()):
            if frame_idx - last_seen.get(tid, frame_idx) > LOST_AFTER:
                resolved_plate = Counter(votes[tid]).most_common(1)[0][0] if votes[tid] else f"MH04BK{tid:04d}"
                vehicle_kind = vtype_map.get(tid, "vehicle")
                for vtype in list(flags[tid]):
                    log_violation(tid, resolved_plate, vtype, vehicle_kind)
                if tid in flags:
                    del flags[tid]

    cap.release()
    print(f"\nFinished: {video_file}")

video_list = sorted(glob.glob("videos/*.mp4"))
for vid in video_list:
    process_single_video(vid)
print("\nAll videos scanned with duplicate protection!")
import numpy as np
from collections import defaultdict

TRIPLE_FRAMES = 3
STOPPED_FRAMES = 25
WINDOW = 15
MIN_MOVE = 30
COS_LIMIT = -0.55

person_counts = defaultdict(list)
history = defaultdict(list)
stop_counts = defaultdict(int)

# Default flow vector: downwards (0, 1). If vehicles move upwards, set (0, -1)
ALLOWED_DIR = np.array([0.0, 1.0])

def center(b):
    return ((b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0)

def inside(pt, box):
    return box[0] <= pt[0] <= box[2] and box[1] <= pt[1] <= box[3]

def rider_region(bike):
    x1, y1, x2, y2 = bike
    h = y2 - y1
    w = x2 - x1
    # Expand upward and horizontally to capture both rider and pillion heads
    return [x1 - 0.2 * w, y1 - 1.2 * h, x2 + 0.2 * w, y2]

def overlap_area(a, b):
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[2], b[2]), min(a[3], b[3])
    return max(0, x2 - x1) * max(0, y2 - y1)

def persons_on_bike(persons, region):
    return [p for p in persons if inside(center(p), region)]

def check_triple_riding(tid, persons, region):
    on_bike = persons_on_bike(persons, region)
    person_counts[tid].append(len(on_bike))
    recent = person_counts[tid][-TRIPLE_FRAMES:]
    return len(recent) >= TRIPLE_FRAMES and (sum(c >= 3 for c in recent) >= 2 or max(recent) >= 3)

def check_wrong_side(tid, box):
    cx, cy = center(box)
    h = history[tid]
    h.append((cx, cy))
    if len(h) < WINDOW:
        return False
    move = np.array(h[-1]) - np.array(h[-WINDOW])
    dist = np.linalg.norm(move)
    if dist < MIN_MOVE:
        return False
    cos = float(np.dot(move / dist, ALLOWED_DIR))
    return cos < COS_LIMIT

def check_illegal_stopping(tid, box):
    cx, cy = center(box)
    h = history[tid]
    if len(h) >= 10:
        move = np.array([cx, cy]) - np.array(h[-10])
        if np.linalg.norm(move) < 6.0:
            stop_counts[tid] += 1
        else:
            stop_counts[tid] = 0
    return stop_counts[tid] >= STOPPED_FRAMES

def check_helmet_violation(heads_or_persons, region):
    """
    Flags no-helmet if an exposed head/person without helmet sits in the rider region.
    """
    riders = persons_on_bike(heads_or_persons, region)
    # If riders are on the bike, check upper head area
    return len(riders) > 0
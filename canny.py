import cv2
import numpy as np
from collections import deque
import os

# -------------------- CONFIG --------------------
video_file = "solidYellowLeft.mp4"  # Replace with your video file
use_camera = False                  # True to use camera
save_roi = True                     # Save ROI images
output_dir = "roi_frames_Yellow"    # Folder for ROI images
os.makedirs(output_dir, exist_ok=True)

# -------------------- CAPTURE --------------------
if use_camera:
    cap = cv2.VideoCapture(0)
else:
    cap = cv2.VideoCapture(video_file)

# Resize for Pi 3
frame_width = 480
frame_height = 320
cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)

fourcc = cv2.VideoWriter_fourcc(*"mp4v")
out = cv2.VideoWriter("lane_output_Yellow.mp4", fourcc, 20.0, (frame_width*3, frame_height))

# -------------------- SMOOTHING --------------------
left_lines_history = deque(maxlen=5)
right_lines_history = deque(maxlen=5)
frame_count = 0

# -------------------- FUNCTIONS --------------------
def region_of_interest(img):
    h, w = img.shape
    polygons = np.array([[
        (int(w*0.1), h),
        (int(w*0.9), h),
        (int(w*0.55), int(h*0.6)),
        (int(w*0.45), int(h*0.6))
    ]])
    mask = np.zeros_like(img)
    cv2.fillPoly(mask, polygons, 255)
    return cv2.bitwise_and(img, mask)

def crop_roi(frame):
    h, w = frame.shape[:2]
    x_min = int(w*0.1)
    x_max = int(w*0.9)
    y_min = int(h*0.6)
    y_max = h
    return frame[y_min:y_max, x_min:x_max]

def make_coordinates(image, line_parameters):
    slope, intercept = line_parameters
    y1 = image.shape[0]
    y2 = int(y1 * 0.6)
    x1 = int((y1 - intercept) / slope)
    x2 = int((y2 - intercept) / slope)
    return np.array([x1, y1, x2, y2])

def average_slope_intercept(image, lines):
    left, right = [], []
    if lines is None:
        return None
    for line in lines:
        x1, y1, x2, y2 = line[0]
        if abs(x2 - x1) < 1e-3:
            continue
        slope = (y2 - y1) / (x2 - x1)
        intercept = y1 - slope * x1
        if abs(slope) < 0.01:
            continue
        if slope < 0:
            left.append((slope, intercept))
        else:
            right.append((slope, intercept))
    lane_lines = []
    if left:
        left_avg = np.mean(left, axis=0)
        lane_lines.append(make_coordinates(image, left_avg))
    if right:
        right_avg = np.mean(right, axis=0)
        lane_lines.append(make_coordinates(image, right_avg))
    return lane_lines

def stack_images(scale, imgArray):
    # Optional: skip stacking if low RAM / Pi is slow
    rows = len(imgArray)
    cols = len(imgArray[0])
    width = imgArray[0][0].shape[1]
    height = imgArray[0][0].shape[0]
    for r in range(rows):
        for c in range(cols):
            if imgArray[r][c].shape[:2] != (height, width):
                imgArray[r][c] = cv2.resize(imgArray[r][c], (width, height))
            if len(imgArray[r][c].shape) == 2:
                imgArray[r][c] = cv2.cvtColor(imgArray[r][c], cv2.COLOR_GRAY2BGR)
    hor = [np.hstack(imgArray[r]) for r in range(rows)]
    return np.vstack(hor)

# -------------------- MAIN LOOP --------------------
while True:
    ret, frame = cap.read()
    if not ret:
        break
    frame_count += 1

    # Resize if not already
    frame = cv2.resize(frame, (frame_width, frame_height))

    # Simple contrast boost for low-quality camera
    frame = cv2.convertScaleAbs(frame, alpha=1.5, beta=20)

    # Preprocess
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    edges = cv2.Canny(blur, 80, 150)  # higher thresholds for noisy images

    # Apply ROI mask
    masked = region_of_interest(edges)

    # Optionally save ROI
    if save_roi:
        cv2.imwrite(f"{output_dir}/roi_masked_{frame_count:04d}.png", masked)
        roi_crop = crop_roi(frame)
        cv2.imwrite(f"{output_dir}/roi_cropped_{frame_count:04d}.png", roi_crop)

    # Detect lines
    lines = cv2.HoughLinesP(masked, 2, np.pi/180, 80,
                            np.array([]), minLineLength=30, maxLineGap=10)
    averaged_lines = average_slope_intercept(frame, lines)
    lane_frame = frame.copy()

    # Stabilize lanes using moving average and handle missing lines
    left_line, right_line = None, None
    if averaged_lines is not None:
        if len(averaged_lines) == 2:
            left_line, right_line = averaged_lines
        elif len(averaged_lines) == 1:
            slope = (averaged_lines[0][3]-averaged_lines[0][1]) / (averaged_lines[0][2]-averaged_lines[0][0]+1e-6)
            if slope < 0:
                left_line = averaged_lines[0]
            else:
                right_line = averaged_lines[0]

    # Update histories if lines detected
    if left_line is not None:
        left_lines_history.append(left_line)
    if right_line is not None:
        right_lines_history.append(right_line)

    # Draw left lane (use previous if missing)
    if left_lines_history:
        left_avg = np.mean(left_lines_history, axis=0).astype(int)
        cv2.line(lane_frame, (left_avg[0], left_avg[1]), (left_avg[2], left_avg[3]), (0,255,0), 4)

    # Draw right lane (use previous if missing)
    if right_lines_history:
        right_avg = np.mean(right_lines_history, axis=0).astype(int)
        cv2.line(lane_frame, (right_avg[0], right_avg[1]), (right_avg[2], right_avg[3]), (0,255,0), 4)

    # Optional 3-panel display (can disable on Pi 3)
    # stacked = stack_images(0.8, [[frame, edges, lane_frame]])
    # cv2.imshow("Lane Detection - 3 View", stacked)
    cv2.imshow("Lane Detection", lane_frame)

    # Save video (optional, slows Pi)
    out.write(lane_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# -------------------- CLEAN UP --------------------
cap.release()
out.release()
cv2.destroyAllWindows()

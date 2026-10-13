"""Interactive four-corner screen replacement with tracked motion and foreground mask.

Dependencies: pip install opencv-python numpy
Run from a desktop session (requires OpenCV GUI). Original video is never modified.
"""
import argparse
from pathlib import Path
import cv2
import numpy as np

def select_polygon(frame, title, count=None):
    points = []
    view = frame.copy()
    def click(event, x, y, flags, userdata):
        if event == cv2.EVENT_LBUTTONDOWN:
            if count is None or len(points) < count:
                points.append((x, y))
    cv2.namedWindow(title, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(title, click)
    while True:
        display = view.copy()
        for i, (x, y) in enumerate(points):
            cv2.circle(display, (x, y), 5, (0, 255, 0), -1)
            cv2.putText(display, str(i + 1), (x + 7, y - 7),
                        cv2.FONT_HERSHEY_SIMPLEX, .6, (0, 255, 0), 2)
        if len(points) > 1:
            cv2.polylines(display, [np.array(points, np.int32)], count is not None and len(points) == count,
                          (0, 255, 0), 2)
        cv2.imshow(title, display)
        key = cv2.waitKey(30) & 0xFF
        if key in (13, 32) and (len(points) == count if count else len(points) >= 3):
            break
        if key in (8, 127) and points:
            points.pop()
        if key == 27:
            raise KeyboardInterrupt("Selection cancelled")
    cv2.destroyWindow(title)
    return np.array(points, np.float32)

def main():
    p = argparse.ArgumentParser(description="Track moving screen and replace distorted digits")
    p.add_argument("--video", default="D:/AI-Video/ComfyUI/output/video/ComfyUI_00002_.mp4")
    p.add_argument("--screen", required=True, help="PNG/JPG containing accurate replacement spectrum display")
    p.add_argument("--output", default="D:/AI-Video/private/lost-signal/v0.3/pilot/S007_screen_fixed.mp4")
    p.add_argument("--opacity", type=float, default=0.95)
    p.add_argument("--skip-occlusion", action="store_true")
    a = p.parse_args()
    if not 0 < a.opacity <= 1:
        p.error("--opacity must be in (0, 1]")
    video, screen, output = Path(a.video), Path(a.screen), Path(a.output)
    if not video.is_file() or not screen.is_file():
        p.error(f"Missing video or screen image: {video} | {screen}")
    cap = cv2.VideoCapture(str(video))
    ok, first = cap.read()
    if not ok:
        raise RuntimeError("Cannot read input video")
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        raise RuntimeError("Invalid FPS")
    height, width = first.shape[:2]
    overlay = cv2.imread(str(screen), cv2.IMREAD_COLOR)
    if overlay is None:
        raise RuntimeError("Cannot decode screen image")
    print("Click screen corners in order: top-left, top-right, bottom-right, bottom-left; Enter to confirm.")
    corners = select_polygon(first, "1 - screen corners (TL TR BR BL)", 4)
    occlusion = None
    if not a.skip_occlusion:
        print("Click polygon around foreground computer covering the screen, Enter to confirm; Esc cancels.")
        occlusion = select_polygon(first, "2 - foreground computer polygon", None)
    output.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(output), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
    if not writer.isOpened():
        raise RuntimeError("Cannot open output writer")
    src = np.array([[0, 0], [overlay.shape[1]-1, 0],
                    [overlay.shape[1]-1, overlay.shape[0]-1], [0, overlay.shape[0]-1]], np.float32)
    prev_gray = cv2.cvtColor(first, cv2.COLOR_BGR2GRAY)
    prev_corners = corners.reshape(-1, 1, 2)
    prev_occ = occlusion
    idx = 0
    try:
        frame = first
        while True:
            if idx:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                tracked, status, _ = cv2.calcOpticalFlowPyrLK(
                    prev_gray, gray, prev_corners, None, winSize=(31,31), maxLevel=3)
                if tracked is None or status is None or not np.all(status):
                    raise RuntimeError(f"Corner tracking lost at frame {idx}. No misleading output produced.")
                corners = tracked.reshape(4, 2)
                if prev_occ is not None:
                    moved, occ_status, _ = cv2.calcOpticalFlowPyrLK(
                        prev_gray, gray, prev_occ.reshape(-1, 1, 2), None, winSize=(31,31), maxLevel=3)
                    if moved is None or occ_status is None or not np.all(occ_status):
                        raise RuntimeError(f"Occluder tracking lost at frame {idx}")
                    occlusion = moved.reshape(-1, 2)
                    prev_occ = occlusion
                prev_corners = tracked
                prev_gray = gray
            H = cv2.getPerspectiveTransform(src, corners.astype(np.float32))
            warped = cv2.warpPerspective(overlay, H, (width, height))
            mask = cv2.warpPerspective(np.full(overlay.shape[:2], 255, np.uint8), H, (width, height))
            if occlusion is not None:
                foreground = np.zeros((height, width), np.uint8)
                cv2.fillPoly(foreground, [occlusion.astype(np.int32)], 255)
                mask[foreground > 0] = 0
            alpha = (mask.astype(np.float32) / 255.0 * a.opacity)[:, :, None]
            result = np.clip(frame * (1 - alpha) + warped * alpha, 0, 255).astype(np.uint8)
            writer.write(result)
            idx += 1
            if idx % 25 == 0:
                print(f"Processed {idx} frames")
            ok, frame = cap.read()
            if not ok:
                break
    finally:
        writer.release()
        cap.release()
        cv2.destroyAllWindows()
    print(f"Saved {idx} frames: {output}")
    print("Note: output is video-only. Original video remains unchanged.")

if __name__ == "__main__":
    main()

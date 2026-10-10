# mirror88.py
# Mirror88 - Live phone screen mirror with touch control (Windows host)
# Copyright (c) 2026 mohamed005cheikh@gmail.com | by MC88

import sys
import os
import subprocess
import time
import queue
import threading
from io import BytesIO

try:
    from flask import Flask, Response, send_from_directory, jsonify, request
    from PIL import Image
except ImportError:
    print("Missing dependency. Run:  pip install -r requirements.txt")
    sys.exit(1)

APP_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)

# ---- Tunables -----------------------------------------------------------
# Lower width = higher FPS. 480 is a good balance on most phones.
STREAM_WIDTH  = 480
JPEG_QUALITY  = 55
# ------------------------------------------------------------------------


def find_adb():
    """Locate adb.exe. Prefers local platform-tools, then PATH."""
    local = os.path.join(APP_DIR, "platform-tools", "adb.exe")
    if os.path.exists(local):
        return local

    try:
        r = subprocess.run(["adb", "version"], capture_output=True, timeout=4)
        if r.returncode == 0:
            return "adb"
    except Exception:
        pass

    for path in [
        os.path.expanduser("~/AppData/Local/Android/Sdk/platform-tools/adb.exe"),
        "C:/platform-tools/adb.exe",
        "C:/adb/adb.exe",
    ]:
        if os.path.exists(path):
            return path

    return None


ADB = find_adb()


def connected_device():
    """Return the serial of a connected device, or None."""
    if not ADB:
        return None
    try:
        r = subprocess.run([ADB, "devices"], capture_output=True,
                           timeout=5, text=True)
        for line in r.stdout.splitlines()[1:]:
            line = line.strip()
            if line.endswith("\tdevice"):
                return line.split("\t")[0]
    except Exception:
        pass
    return None


def device_info():
    """Fetch model name and battery level."""
    if not ADB:
        return {"model": "Unknown", "battery": 0}

    info = {"model": "Unknown", "battery": 0}

    try:
        r = subprocess.run([ADB, "shell", "getprop", "ro.product.model"],
                           capture_output=True, timeout=3, text=True)
        info["model"] = r.stdout.strip() or "Unknown"
    except Exception:
        pass

    try:
        r = subprocess.run([ADB, "shell", "dumpsys", "battery"],
                           capture_output=True, timeout=3, text=True)
        for line in r.stdout.splitlines():
            if "level:" in line:
                info["battery"] = int(line.split(":", 1)[1].strip())
                break
    except Exception:
        pass

    return info


# ------------------------------------------------------------------------
# Frame pipeline: capture and encode run in parallel threads
# ------------------------------------------------------------------------

# Latest known phone resolution, updated on every frame
PHONE_SIZE = {"w": 1080, "h": 2400}


def capture_raw():
    """Grab one raw RGBA frame from the phone."""
    proc = subprocess.Popen(
        [ADB, "exec-out", "screencap"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    data = proc.stdout.read()
    proc.wait()
    return data


def raw_to_jpeg(data):
    """Convert raw screencap output to compressed JPEG bytes."""
    if not data or len(data) < 12:
        return None

    w = int.from_bytes(data[0:4], "little")
    h = int.from_bytes(data[4:8], "little")

    if w <= 0 or h <= 0 or w > 5000 or h > 5000:
        return None

    PHONE_SIZE["w"] = w
    PHONE_SIZE["h"] = h

    expected = 12 + w * h * 4
    if len(data) < expected:
        return None

    try:
        img = Image.frombytes("RGBA", (w, h), data[12:expected])
    except Exception:
        return None

    img = img.convert("RGB")

    if w > STREAM_WIDTH:
        ratio = STREAM_WIDTH / w
        img = img.resize(
            (STREAM_WIDTH, max(1, int(h * ratio))),
            Image.BILINEAR,
        )

    buf = BytesIO()
    img.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=False)
    return buf.getvalue()


class FramePipeline:
    """Two-thread pipeline: one captures, one encodes. Doubles throughput."""

    def __init__(self):
        self.capture_q = queue.Queue(maxsize=1)
        self.encoded_q = queue.Queue(maxsize=2)
        self.running = True
        self.paused = False

        threading.Thread(target=self._capture_loop, daemon=True).start()
        threading.Thread(target=self._encode_loop, daemon=True).start()

    def _capture_loop(self):
        while self.running:
            if self.paused:
                time.sleep(0.1)
                continue

            try:
                data = capture_raw()
            except Exception:
                time.sleep(0.1)
                continue

            # Replace any older pending frame — always prefer the freshest
            try:
                while not self.capture_q.empty():
                    self.capture_q.get_nowait()
            except queue.Empty:
                pass

            try:
                self.capture_q.put_nowait(data)
            except queue.Full:
                pass

    def _encode_loop(self):
        while self.running:
            try:
                raw = self.capture_q.get(timeout=1)
            except queue.Empty:
                continue

            try:
                jpeg = raw_to_jpeg(raw)
            except Exception:
                continue

            if not jpeg:
                continue

            try:
                while not self.encoded_q.empty():
                    self.encoded_q.get_nowait()
            except queue.Empty:
                pass

            try:
                self.encoded_q.put_nowait(jpeg)
            except queue.Full:
                pass

    def get_frame(self, timeout=2):
        try:
            return self.encoded_q.get(timeout=timeout)
        except queue.Empty:
            return None


PIPELINE = None


def frame_generator():
    """Yield MJPEG frames."""
    global PIPELINE
    PIPELINE = FramePipeline()

    boundary = b"--frame\r\n"

    while True:
        if not connected_device():
            PIPELINE.paused = True
            time.sleep(0.5)
            continue

        PIPELINE.paused = False
        jpeg = PIPELINE.get_frame(timeout=2)

        if not jpeg:
            continue

        yield (
            boundary +
            b"Content-Type: image/jpeg\r\n" +
            b"Content-Length: " + str(len(jpeg)).encode() + b"\r\n\r\n" +
            jpeg + b"\r\n"
        )


# ------------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------------

@app.route("/")
def serve_index():
    return send_from_directory(APP_DIR, "index.html")


@app.route("/stream")
def stream():
    return Response(
        frame_generator(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@app.route("/status")
def status():
    serial = connected_device()
    if not serial:
        return jsonify({"connected": False})

    info = device_info()
    info["connected"] = True
    info["serial"] = serial
    info["phone_w"] = PHONE_SIZE["w"]
    info["phone_h"] = PHONE_SIZE["h"]
    return jsonify(info)


@app.route("/control", methods=["POST"])
def control():
    """Receive a click or swipe from the browser and replay it on the phone."""
    if not ADB or not connected_device():
        return jsonify({"success": False, "error": "No device"}), 400

    data = request.get_json(silent=True) or {}
    action = data.get("action")

    # Browser sends coordinates in the displayed image space.
    # We scale them up to the phone's real resolution.
    disp_w = float(data.get("disp_w") or 1)
    disp_h = float(data.get("disp_h") or 1)
    phone_w = PHONE_SIZE["w"]
    phone_h = PHONE_SIZE["h"]

    def scale(x, y):
        px = int((x / disp_w) * phone_w)
        py = int((y / disp_h) * phone_h)
        px = max(0, min(phone_w - 1, px))
        py = max(0, min(phone_h - 1, py))
        return px, py

    try:
        if action == "tap":
            px, py = scale(data.get("x", 0), data.get("y", 0))
            subprocess.Popen(
                [ADB, "shell", "input", "tap", str(px), str(py)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )

        elif action == "swipe":
            x1, y1 = scale(data.get("x1", 0), data.get("y1", 0))
            x2, y2 = scale(data.get("x2", 0), data.get("y2", 0))
            duration = int(data.get("duration", 250))
            subprocess.Popen(
                [ADB, "shell", "input", "swipe",
                 str(x1), str(y1), str(x2), str(y2), str(duration)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )

        elif action == "text":
            text = str(data.get("text", ""))
            # adb input text needs %s for spaces
            safe = text.replace(" ", "%s")
            subprocess.Popen(
                [ADB, "shell", "input", "text", safe],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )

        elif action == "key":
            key = str(data.get("key", ""))
            if key:
                subprocess.Popen(
                    [ADB, "shell", "input", "keyevent", key],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )

        else:
            return jsonify({"success": False, "error": "Unknown action"}), 400

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ------------------------------------------------------------------------
# Entry
# ------------------------------------------------------------------------

if __name__ == "__main__":
    if not ADB:
        print()
        print("  ADB was not found.")
        print("  Run Start_Mirror88.bat — it downloads it automatically.")
        print()
        sys.exit(1)

    serial = connected_device()

    print()
    print("+" + "-" * 56 + "+")
    print("|" + "MIRROR88 - PHONE SCREEN MIRROR".center(56) + "|")
    print("+" + "-" * 56 + "+")

    if serial:
        print(f"| Device detected: {serial:<37} |")
    else:
        print("| No device detected.                                  |")
        print("| Connect via USB or run Pair_Wireless.bat.            |")

    print("+" + "-" * 56 + "+")
    print("| Open in your browser:   http://localhost:8890        |")
    print("+" + "-" * 56 + "+")
    print("| Click and drag on the screen to control the phone.   |")
    print("| Press Ctrl+C to stop.                                |")
    print("+" + "-" * 56 + "+")
    print()

    app.run(host="127.0.0.1", port=8890, debug=False, threaded=True)

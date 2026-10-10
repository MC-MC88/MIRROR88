```markdown
# Mirror88

Live phone screen mirror with mouse control — right in your browser.  
No app on the phone. No cloud. Works wired or fully wireless.

**Copyright (c) 2026 mohamed005cheikh@gmail.com — by MC88**

---

## What's new in this version

- **Mouse control** — click on the screen to tap, drag to swipe
- **Quick keys** — Home / Back / Recents / Power / Volume on the sidebar
- **~2× more frames** — capture and encoding run in parallel threads
- **ADB auto-download** — no manual setup, just double-click
- **Wireless helper scripts** — `Pair_Wireless.bat` and `Connect_Wireless.bat`

---

## Requirements

- **Windows PC**
- **Android phone** (Android 11+ for wireless; any recent Android for USB)
- **Python 3.9+** (with "Add Python to PATH")

Everything else (ADB, Pillow, Flask) is downloaded automatically.

---

## First-time setup

1. Put all files in one folder.
2. Double-click **`Start_Mirror88.bat`**.
   - First run downloads ADB (~10 MB) and Python packages.
   - Every run after that starts in a second.
3. Open **http://localhost:8890** in your browser.

---

## Connecting the phone

### Option A — USB (simplest)

1. On the phone: **Settings → About phone → tap "Build number" 7 times**
2. **Settings → System → Developer options → USB debugging → ON**
3. Plug the phone into the PC via USB
4. Tap **Allow** on the phone popup
5. Done — the mirror will appear

### Option B — Wireless (Android 11+, no cable ever)

1. On the phone: **Developer options → Wireless debugging → ON**
2. Tap **"Pair device with pairing code"**
3. Note the **IP:PORT** and **6-digit code** shown
4. On the PC: double-click **`Pair_Wireless.bat`**
5. Enter the IP:PORT and code when asked
6. Back on the phone, look at the **main Wireless debugging screen**
   (not the pairing dialog) — note the IP:PORT shown there
7. On the PC: double-click **`Connect_Wireless.bat`**
8. Enter that IP:PORT
9. Done — now run `Start_Mirror88.bat`

> **Tip:** The phone and PC must be on the same Wi-Fi network.

---

## How to control the phone

Once the screen is mirrored in the browser:

| Action | On the PC |
|---|---|
| **Tap** on the phone | Single left-click on the mirrored image |
| **Swipe** on the phone | Click, hold, drag, release |
| **Home button** | Sidebar → HOME |
| **Back button** | Sidebar → BACK |
| **Recent apps** | Sidebar → RECENTS |
| **Power / screen off** | Sidebar → POWER |
| **Volume** | Sidebar → VOL + / VOL − |

The coordinates are scaled automatically — what you click on the
mirrored image matches the exact point on the phone.

---

## Why the FPS is what it is

Mirror88 uses `adb exec-out screencap`, which is a **raw pixel
capture**. On a typical phone this runs at 8–15 FPS.

The pipeline runs **capture** and **JPEG encoding** in parallel
threads, so you get roughly **twice** the throughput of a naive
loop. Lower `STREAM_WIDTH` in `mirror88.py` for even more frames
(e.g. 380 for ~15–20 FPS).

For 60 FPS you would need H.264 streaming (`screenrecord` +
ffmpeg), which is what **scrcpy** does. That's a much larger
project, but Mirror88 is the honest learning version.

---

## Tuning performance

Open `mirror88.py` and change the top constants:

```python
STREAM_WIDTH  = 480   # Lower = faster. Try 380 for more FPS.
JPEG_QUALITY  = 55    # Lower = faster. 40 is still readable.
```

---

Troubleshooting

"No device"

· USB: check the cable, enable USB debugging, tap Allow on the popup
· Wireless: the IP:PORT may have changed — re-run Connect_Wireless.bat
· Verify with: platform-tools\adb.exe devices

Black screen

· Lock and unlock the phone once after connecting

Clicks are off by a few pixels

· Wait for one full frame after the resolution readout changes

Port 8890 already in use

· Change port = 8890 at the bottom of mirror88.py

---

Privacy

· The phone connects only to your PC (USB or local Wi-Fi).
· The browser runs on the same PC — no LAN exposure, no PIN.
· Nothing is uploaded anywhere.
· Source code is fully readable.

---

Credits

© 2026 mohamed005cheikh@gmail.com — by MC88.
Free to use and modify for personal use.

```
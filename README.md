# 🎮 LANStream

A **real-time multi-user LAN game streaming platform** built using WebRTC.

Stream your screen + mic to friends on the same network — no installs, just open a browser.

---

## ✨ Features

* 📡 Screen + microphone streaming
* 👥 Multiple viewers per stream
* ⚡ Low latency via WebRTC
* 🌐 Works entirely on LAN
* 🖥️ Clean grid UI with live tiles
* 🔒 HTTPS support (required for screen/mic access)

---

## 🚀 Getting Started

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 2. Run server

```bash
python server.py
```

---

### 3. Open in browser

On your PC:

```
https://localhost:8000
```

On other devices (same WiFi):

```
https://<your-ip>:8000
```

⚠️ You will see a "Not Secure" warning (self-signed certificate).
Click **Advanced → Proceed**.

---

## 🎮 Usage

* Enter your name
* Toggle screen/mic
* Click **Go Live**
* Others can join instantly from the grid

---

## 🧠 Tech Stack

* **Frontend:** HTML, CSS, JavaScript, WebRTC
* **Backend:** FastAPI (WebSocket signaling)
* **Streaming:** Peer-to-peer via WebRTC

---

## ⚠️ Notes

* Works best on LAN (no TURN server)
* Chrome recommended
* Wayland users may face screen capture issues

---

## 🔥 Future Ideas

* Chat system
* Stream rooms
* Bitrate control
* Mobile UI improvements

---

## 🧑‍💻 Author

Built for fun, learning, and streaming games with friends.

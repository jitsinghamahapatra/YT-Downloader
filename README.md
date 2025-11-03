# 🎬 YouTube Video Downloader

A simple and efficient web application that allows users to download YouTube videos or audio directly by pasting the video link.  
Built using **Flask (Python)** for the backend and a clean **HTML + JS** frontend interface powered by **yt-dlp**.

---

## 🚀 Features

- 🔗 **Paste any YouTube video link** and get available formats  
- 🎥 **Download videos in multiple resolutions** (360p, 480p, 720p, 1080p, etc.)  
- 🎧 **Download audio-only (MP3) version**  
- ⚡ **Fast and reliable downloading using `yt-dlp`**  
- 🔒 **Supports cookies.txt** for authenticated or restricted videos  
- 🌐 **Cross-platform (works on Windows, macOS, Linux)**  
- 🧩 **Frontend + Backend integrated** — ready to use out of the box

---

## 🛠 Technologies Used

- **Python (Flask)** — Backend API  
- **yt-dlp** — For YouTube downloading  
- **HTML5, CSS3, JavaScript** — Frontend UI  
- **Flask-CORS** — For API communication  
- **FFmpeg** — For merging audio and video

---

## ⚙️ How It Works

1. The user enters a YouTube video URL.  
2. The app fetches all available video and audio formats using `yt-dlp`.  
3. The user selects a desired format (e.g., 1080p MP4 or MP3).  
4. Flask downloads the video using the selected format and serves it directly as a downloadable file.  
5. After sending the file, it automatically deletes the temporary download to save space.

---

## 📂 Project Setup

1. Download and open the folder that contains **index.html**.  
2. Right-click the folder and open it with **VS Code**.  
3. Download **requirements.txt** and **FFmpeg** (for merging audio and video).  
4. Run the Flask server using:
   ```bash
   python server.py

---

## 🌐 Live Demo

Link: https://yt-video-playlist-dowenloder.onrender.com/

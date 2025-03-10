# GestureSymphony
[Open in Render Spaces](https://huggingface.co/spaces/asr24/GestureSymphony)

GestureSymphony is a web application that lets you control video playback using intuitive hand gestures. Powered by cutting-edge computer vision and hand gesture recognition technology, this project uses MediaPipe Hands and OpenCV on the backend (via Flask) and a responsive HTML5/JavaScript frontend to provide a truly touch-free experience.

## Features

- **Real-time Hand Gesture Recognition**  
  Detect gestures from your webcam feed to control video playback:
  - **ONE**: Pause video
  - **TWO**: Play video
  - **THREE**: Skip to the next video
  - **FOUR**: Go back to the previous video

- **Video Playlist Management**  
  View and interact with a dynamic playlist of uploaded videos. Click on any video to play it.

- **Video Upload**  
  Easily upload new videos to expand your playlist.

- **Dockerized Deployment**  
  Deploy the entire application using Docker.

- **Git LFS Integration**  
  Manage and push large video files seamlessly with Git LFS.

## Prerequisites

- **Python 3.12** (or later)
- **Docker** (for containerized deployment)
- **Git & Git LFS** installed

## Technologies Used

- **Flask** – Lightweight Python web framework
- **OpenCV** – Real-time computer vision library
- **MediaPipe Hands** – State-of-the-art hand gesture recognition
- **HTML5, CSS, JavaScript** – Frontend development
- **Bootstrap** – Responsive design framework
- **Docker** – Containerization platform
- **Git LFS** – Large file storage for Git

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/GestureSymphony.git
   cd GestureSymphony
   ```

2. **Install Python Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Flask Application Locally:**
   ```bash
   python3 app.py
   ```
   Then, open your browser and navigate to `http://localhost:8080`.

## Docker Deployment

1. **Build the Docker Image:**
   ```bash
   docker build -t gesturesymphony .
   ```

2. **Run the Docker Container:**
   ```bash
   docker run -p 8080:8080 gesturesymphony
   ```

## Git LFS Setup for Large Video Files

1. **Install Git LFS:**
   ```bash
   git lfs install
   ```

2. **Track Video File Extensions:**
   ```bash
   git lfs track "*.mp4"
   git lfs track "*.webm"
   ```

3. **Add the `.gitattributes` File:**
   ```bash
   git add .gitattributes
   ```

4. **Commit and Push Your Changes:**
   ```bash
   git add .
   git commit -m "Update app, templates; add videos with Git LFS; remove old song files"
   git push origin main
   ```

## Usage

1. **Access the Website:**
   Open `http://localhost:8080` in your web browser.

2. **Upload Videos:**
   Use the upload section to add new videos to your playlist.

3. **Control Video Playback with Gestures:**
   - Click **Start Camera** to enable webcam access.
   - Use the following gestures:
     - **ONE**: Pauses the video.
     - **TWO**: Plays the video.
     - **THREE**: Skips to the next video.
     - **FOUR**: Goes back to the previous video.

4. **Manual Control:**
   Click on any video in the playlist to play it manually.

## Contributing

Contributions are welcome! Please fork the repository, create a feature branch, and submit a pull request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **MediaPipe Hands** for advanced hand gesture recognition.
- **OpenCV** for robust computer vision capabilities.
- **Flask** for the backend framework.
- **Bootstrap** for responsive UI design.

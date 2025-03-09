import os
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import os
import cv2
import mediapipe as mp
import numpy as np
import base64
from flask import Flask, render_template, request, jsonify
import pygame
import threading
import time

app = Flask(__name__)
app.config['DEBUG'] = False

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

hands_detector = mp_hands.Hands(static_image_mode=True,
                                max_num_hands=1,
                                min_detection_confidence=0.7)

pygame.mixer.init()

is_paused = False
music_started = False 

@app.route("/health")
def health():
    return "ok", 200


SONG_FOLDER = os.path.join(os.getcwd(), "songs")

def get_playlist():
    """Return a list of full paths to all songs in SONG_FOLDER."""
    return [os.path.join(SONG_FOLDER, f) for f in os.listdir(SONG_FOLDER)
            if f.lower().endswith(('.mp3', '.wav'))]

playlist = get_playlist()
current_song_index = 0

def play_song():
    """Play (or unpause) the current song."""
    global current_song_index, playlist, is_paused
    if not playlist:
        print("No songs in playlist.")
        return
    is_paused = False
    if not pygame.mixer.music.get_busy():
        pygame.mixer.music.load(playlist[current_song_index])
        pygame.mixer.music.play()
        print(f"Playing: {os.path.basename(playlist[current_song_index])}")
    else:
        pygame.mixer.music.unpause()
        print("Unpaused")

def pause_song():
    """Pause the current song."""
    global is_paused
    pygame.mixer.music.pause()
    is_paused = True
    print("Paused")

def next_song():
    """Move to the next song in the playlist and play it."""
    global current_song_index, playlist, is_paused
    if not playlist:
        return
    current_song_index = (current_song_index + 1) % len(playlist)
    pygame.mixer.music.load(playlist[current_song_index])
    pygame.mixer.music.play()
    is_paused = False
    print(f"Next Track: {os.path.basename(playlist[current_song_index])}")

def prev_song():
    """Move to the previous song in the playlist and play it."""
    global current_song_index, playlist, is_paused
    if not playlist:
        return
    current_song_index = (current_song_index - 1) % len(playlist)
    pygame.mixer.music.load(playlist[current_song_index])
    pygame.mixer.music.play()
    is_paused = False
    print(f"Previous Track: {os.path.basename(playlist[current_song_index])}")

def control_music(command):
    """
    Execute a media control command based on the detected gesture.
    Mapping:
      - "Play" → Play/Unpause current song
      - "Pause" → Pause the song
      - "Next" → Next song in the playlist
    """
    print("Executing Music Command:", command)
    if command == "Play":
        play_song()
    elif command == "Pause":
        pause_song()
    elif command == "Next":
        next_song()

def count_fingers(hand_landmarks, image_width, image_height):
    """
    Count the number of extended fingers using hand landmarks.
    For index, middle, ring, and pinky fingers, check if the tip is above the PIP joint.
    (The thumb is ignored in this implementation.)
    """
    landmarks = []
    for lm in hand_landmarks.landmark:
        landmarks.append((int(lm.x * image_width), int(lm.y * image_height)))
    
    finger_tips = [8, 12, 16, 20]
    count = 0
    for tip in finger_tips:
        if landmarks[tip][1] < landmarks[tip - 2][1]:
            count += 1
    return count

def process_frame(frame):
    """
    Process the input frame using MediaPipe Hands.
    Detects hand landmarks, counts extended fingers (ignoring thumb),
    maps the count to a gesture, and triggers a corresponding music command.
    """
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands_detector.process(img_rgb)
    
    gesture_text = "No hand detected"
    music_command = "None"
    
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            image_height, image_width, _ = frame.shape
            finger_count = count_fingers(hand_landmarks, image_width, image_height)
            
            # Mapping: 1 finger → Pause, 2 fingers → Play, 3 fingers → Next
            if finger_count == 1:
                gesture_text = "ONE"
                music_command = "Pause"
            elif finger_count == 2:
                gesture_text = "TWO"
                music_command = "Play"
            elif finger_count == 3:
                gesture_text = "THREE"
                music_command = "Next"
            else:
                gesture_text = {0: "Fist", 4: "FOUR", 5: "FIVE"}.get(finger_count, "Unknown")
                music_command = "None"
            
            if music_command != "None":
                control_music(music_command)
            break
    cv2.putText(frame, f"Gesture: {gesture_text} | Command: {music_command}", (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
    return frame

# On full page refresh, remove temporary songs (files starting with "temp_") that are not currently playing.
@app.route('/')
def index():
    global playlist, current_song_index
    playlist = get_playlist()
    current_song_path = None
    if playlist and current_song_index < len(playlist):
        current_song_path = playlist[current_song_index]
    # Delete any temporary songs not currently playing.
    for f in os.listdir(SONG_FOLDER):
        if f.startswith("temp_"):
            temp_file = os.path.join(SONG_FOLDER, f)
            if temp_file != current_song_path:
                os.remove(temp_file)
    playlist = get_playlist()
    songs = []
    for idx, song in enumerate(playlist):
        songs.append({
            "name": os.path.basename(song),
            "isPlaying": (idx == current_song_index)
        })
    return render_template('index.html', songs=songs)

@app.route('/process', methods=['POST'])
def process():
    data = request.get_json()
    img_data = data['image']
    header, encoded = img_data.split(',', 1)
    decoded = base64.b64decode(encoded)
    np_arr = np.frombuffer(decoded, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    
    processed = process_frame(frame)
    
    ret, buf = cv2.imencode('.jpg', processed)
    processed_base64 = base64.b64encode(buf).decode('utf-8')
    
    return jsonify({'processed_image': 'data:image/jpeg;base64,' + processed_base64})

@app.route('/start', methods=['POST'])
def start_music():
    global music_started
    music_started = True
    play_song()
    return jsonify({"status": "Music started"})

@app.route('/prev', methods=['POST'])
def prev_track():
    prev_song()
    return jsonify({"status": "Previous track started"})

@app.route('/set_volume', methods=['POST'])
def set_volume():
    data = request.get_json()
    vol = data.get('volume', 1.0)
    pygame.mixer.music.set_volume(float(vol))
    return jsonify({"status": f"Volume set to {vol}"})

@app.route('/songs', methods=['GET'])
def get_songs():
    global playlist, current_song_index
    playlist = get_playlist()
    songs = []
    for idx, song in enumerate(playlist):
        songs.append({
            "name": os.path.basename(song),
            "isPlaying": (idx == current_song_index)
        })
    return jsonify({"songs": songs})

@app.route('/upload', methods=['POST'])
def upload_song():
    if 'file' not in request.files:
        return jsonify({"status": "No file uploaded"}), 400
    file = request.files['file']
    if file.filename == "":
        return jsonify({"status": "No file selected"}), 400
    
    # Delete any previously uploaded temporary song
    for f in os.listdir(SONG_FOLDER):
        if f.startswith("temp_"):
            os.remove(os.path.join(SONG_FOLDER, f))
    
    filename = "temp_" + file.filename
    filepath = os.path.join(SONG_FOLDER, filename)
    file.save(filepath)
    return jsonify({"status": "Uploaded", "filename": filename})

def auto_next_song():
    """Background thread to automatically play the next song when the current one finishes,
    but only if music has been started by the user."""
    global is_paused, music_started
    while True:
        time.sleep(1)
        if music_started and (not is_paused) and (not pygame.mixer.music.get_busy()):
            next_song()

threading.Thread(target=auto_next_song, daemon=True).start()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

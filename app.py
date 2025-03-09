import os
import cv2
import numpy as np
import base64
from flask import Flask, render_template, request, jsonify, send_from_directory
import threading
import time
import mediapipe as mp

app = Flask(__name__)
app.config['DEBUG'] = False

SONG_FOLDER = os.path.join(os.getcwd(), "songs")

@app.route("/health")
def health():
    return "ok", 200

@app.route("/songs/<path:filename>")
def serve_song(filename):
    return send_from_directory(SONG_FOLDER, filename)

def get_playlist():
    return [f for f in os.listdir(SONG_FOLDER) if f.lower().endswith(('.mp3', '.wav'))]

@app.route('/songs', methods=['GET'])
def get_songs():
    playlist = get_playlist()
    songs = []
    for idx, song in enumerate(playlist):
        songs.append({
            "name": song,
            "isPlaying": (idx == 0)  
        })
    return jsonify({"songs": songs})

def get_hands_detector():
    global _hands_detector
    try:
        return _hands_detector
    except NameError:
        mp_hands = mp.solutions.hands
        _hands_detector = mp_hands.Hands(
            static_image_mode=True,
            max_num_hands=1,
            min_detection_confidence=0.7
        )
        return _hands_detector

def get_mp_drawing():
    global _mp_drawing
    try:
        return _mp_drawing
    except NameError:
        _mp_drawing = mp.solutions.drawing_utils
        return _mp_drawing

def count_fingers(hand_landmarks, image_width, image_height):
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
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    detector = get_hands_detector()
    drawing_utils = get_mp_drawing()
    results = detector.process(img_rgb)
    
    gesture_text = "No hand detected"
    music_command = "None"
    
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            drawing_utils.draw_landmarks(frame, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)
            image_height, image_width, _ = frame.shape
            finger_count = count_fingers(hand_landmarks, image_width, image_height)
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
            break

    cv2.putText(frame, f"Gesture: {gesture_text} | Command: {music_command}", (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
    return frame, music_command

@app.route('/')
def index():
    songs = []
    for idx, song in enumerate(get_playlist()):
        songs.append({
            "name": song,
            "isPlaying": (idx == 0)
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
    
    processed_frame, music_command = process_frame(frame)
    
    ret, buf = cv2.imencode('.jpg', processed_frame)
    processed_base64 = base64.b64encode(buf).decode('utf-8')
    
    return jsonify({
        'processed_image': 'data:image/jpeg;base64,' + processed_base64,
        'music_command': music_command
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

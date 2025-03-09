import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import cv2
import numpy as np
import base64
from flask import send_from_directory, Flask, render_template, request, jsonify
import time

app = Flask(__name__)
app.config['DEBUG'] = False

# Define the folder where your video files are stored.
VIDEO_FOLDER = os.path.join(os.getcwd(), "videos")

@app.route("/health")
def health():
    return "ok", 200

# Serve video files
@app.route('/videos/<path:filename>')
def serve_video(filename):
    return send_from_directory(VIDEO_FOLDER, filename)

def get_hands_detector():
    global _hands_detector
    try:
        return _hands_detector
    except NameError:
        import mediapipe as mp
        _mp_hands = mp.solutions.hands
        _hands_detector = _mp_hands.Hands(
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
        import mediapipe as mp
        _mp_drawing = mp.solutions.drawing_utils
        return _mp_drawing

# Return a list of video files (adjust extensions as needed)
def get_playlist():
    return [os.path.join(VIDEO_FOLDER, f) for f in os.listdir(VIDEO_FOLDER)
            if f.lower().endswith(('.mp4', '.webm'))]

playlist = get_playlist()
current_video_index = 0

def process_frame(frame):
    import mediapipe as mp
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    detector = get_hands_detector()
    drawing_utils = get_mp_drawing()
    results = detector.process(img_rgb)
    
    # Defaults if no hand is detected
    gesture_text = "No hand detected"
    action_text = "No action"
    
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            drawing_utils.draw_landmarks(frame, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)
            image_height, image_width, _ = frame.shape
            landmarks = [(int(lm.x * image_width), int(lm.y * image_height))
                         for lm in hand_landmarks.landmark]
            finger_tips = [8, 12, 16, 20]
            count = 0
            for tip in finger_tips:
                if landmarks[tip][1] < landmarks[tip - 2][1]:
                    count += 1
            if count == 1:
                gesture_text = "ONE"
                action_text = "Pause video"
            elif count == 2:
                gesture_text = "TWO"
                action_text = "Play video"
            elif count == 3:
                gesture_text = "THREE"
                action_text = "Next video"
            elif count == 4:
                gesture_text = "FOUR"
                action_text = "Previous video"
            else:
                if count == 0:
                    gesture_text = "Fist"
                elif count == 5:
                    gesture_text = "FIVE"
                else:
                    gesture_text = "Unknown"
                action_text = "No action"
            break
    cv2.putText(frame, f"Gesture: {gesture_text} | Action: {action_text}", (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
    return frame, gesture_text, action_text

@app.route('/process', methods=['POST'])
def process():
    data = request.get_json()
    img_data = data['image']
    header, encoded = img_data.split(',', 1)
    decoded = base64.b64decode(encoded)
    np_arr = np.frombuffer(decoded, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    
    processed, gesture, action = process_frame(frame)
    
    ret, buf = cv2.imencode('.jpg', processed)
    processed_base64 = base64.b64encode(buf).decode('utf-8')
    
    return jsonify({
        'processed_image': 'data:image/jpeg;base64,' + processed_base64,
        'gesture': gesture,
        'action': action
    })

@app.route('/')
def index():
    global playlist, current_video_index
    playlist = get_playlist()
    current_video_path = None
    if playlist and current_video_index < len(playlist):
        current_video_path = playlist[current_video_index]
    for f in os.listdir(VIDEO_FOLDER):
        if f.startswith("temp_"):
            temp_file = os.path.join(VIDEO_FOLDER, f)
            if temp_file != current_video_path:
                os.remove(temp_file)
    playlist = get_playlist()
    videos = []
    for idx, video_file in enumerate(playlist):
        videos.append({
            "name": os.path.basename(video_file),
            "isPlaying": (idx == current_video_index)
        })
    return render_template('index.html', videos=videos)

@app.route('/videos', methods=['GET'])
def get_videos():
    global playlist, current_video_index
    playlist = get_playlist()
    videos = []
    for idx, video_file in enumerate(playlist):
        videos.append({
            "name": os.path.basename(video_file),
            "isPlaying": (idx == current_video_index)
        })
    return jsonify({"videos": videos})

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'file' not in request.files:
        return jsonify({"status": "No file uploaded"}), 400
    file = request.files['file']
    if file.filename == "":
        return jsonify({"status": "No file selected"}), 400
    for f in os.listdir(VIDEO_FOLDER):
        if f.startswith("temp_"):
            os.remove(os.path.join(VIDEO_FOLDER, f))
    filename = "temp_" + file.filename
    filepath = os.path.join(VIDEO_FOLDER, filename)
    file.save(filepath)
    return jsonify({"status": "Uploaded", "filename": filename})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

from flask import Flask, render_template, request, url_for, Response, jsonify, send_from_directory
import os
import cv2
import pickle
import cvzone
import numpy as np

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

available_slot = []

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/save_slot', methods=['POST'])
def save_slot():
    try:
        data = request.get_json()  
        positions = data.get('positions', [])
        positions = list(map(tuple, positions))
        positions.sort(key=lambda pos: (pos[1], pos[0])) 
        with open("slot", 'wb') as f:
            pickle.dump(positions, f)
        return jsonify({"message": "Slots Saved", "positions": positions}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/select', methods=['POST'])
def select():
    if 'image' not in request.files:
        return "No File", 400
    image = request.files['image']
    if image.filename == '':
        return "No File Selected", 400
    if image:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
        image.save(image_path)
        image_url = url_for('uploaded_file', filename=image.filename)
        try:
            with open('slot', 'rb') as f:
                positions = pickle.load(f)
        except:
            positions = []
        return render_template('select.html', image_url=image_url, position=positions)

@app.route('/detect', methods=['POST'])
def detect():
    if 'video' not in request.files:
        return "No File", 400
    video = request.files['video']
    if video.filename == '':
        return "No File Selected", 400
    if video:
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], video.filename)
        video.save(video_path)
        return render_template('live.html', video_path=video_path, slot=len(available_slot))

@app.route('/live')
def live():
    video_path = request.args.get('video_path')
    return Response(generate_frames(video_path), mimetype='multipart/x-mixed-replace;boundary=frame')
def generate_frames(video_path):
    global available_slot
    cap = cv2.VideoCapture(video_path)
    try:
        if os.path.exists('slot'):
            try:
                with open('slot', 'rb') as f:
                    slotList = pickle.load(f)
            except (EOFError):
                slotList = []
        else:
            slotList = []
            with open('slot', 'wb') as f:
                pickle.dump(slotList, f)
        width, height = 107, 48
        def checkParkingSlot(img, imgPro):
            global available_slot
            available_slot.clear()
            slotCount = 0
            for idx, pos in enumerate(slotList):
                x, y = pos
                imgCrop = imgPro[y:y+height, x:x+width]
                count = cv2.countNonZero(imgCrop)
                slot_number = idx+1
                if count<900:
                    color = (0, 255, 0)
                    thickness = 5
                    slotCount += 1
                    available_slot.append(slot_number)
                else:
                    color = (0, 0, 255)
                    thickness = 2
                cv2.rectangle(img, pos, (pos[0]+width, pos[1]+height), color, thickness)
                cvzone.putTextRect(img, f'Slot {slot_number}', (x, y+height-3), scale=1, thickness=2, offset=0, colorR=color)
            cvzone.putTextRect(img, f'Available Slot: {slotCount}/{len(slotList)}', (325, 50), scale=3, thickness=3, offset=10, colorR=(0, 200, 0))
        while True:
            if cap.get(cv2.CAP_PROP_POS_FRAMES) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            success, img = cap.read()
            if not success:
                break
            imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            imgBlur = cv2.GaussianBlur(imgGray, (3, 3), 1)
            imgThreshold = cv2.adaptiveThreshold(imgBlur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 16)
            imgMedian = cv2.medianBlur(imgThreshold, 5)
            kernel = np.ones((3, 3), np.uint8)
            imgDilate = cv2.dilate(imgMedian, kernel, iterations=1)
            checkParkingSlot(img, imgDilate)
            ret, jpeg = cv2.imencode('.jpg', img)
            if not ret:
                continue
            frame = jpeg.tobytes()
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    finally:
        cap.release()

@app.route('/get_available_slot', methods=['GET'])
def get_available_slot():
    return jsonify({
        'availableSlot': available_slot,
        'totalAvailableSlot': len(available_slot)
    })

@app.route('/available')
def available():
    return render_template('available.html', available_slot=available_slot)

@app.route('/delete', methods=['POST'])
def delete():
    file = 'slot'
    if os.path.exists(file):
        try:
            os.remove(file)
            return "File Deleted Successfully", 200
        except Exception as e:
            return f"Error Deleting File: {str(e)}", 500
    return "File Not Found", 404

if __name__ == '__main__':
    app.run(debug=True)

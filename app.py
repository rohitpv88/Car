from flask import Flask, render_template, request, redirect, url_for, Response, jsonify
import subprocess
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

free_spaces = []  # Global list to store free parking spaces

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/picker', methods=['POST'])
def picker():
    if 'image' not in request.files:
        return "No file part", 400
    image = request.files['image']
    if image.filename == '':
        return "No selected file", 400
    if image:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
        image.save(image_path)

        # Run picker.py when the button is clicked
        subprocess.run(['python', 'picker.py', image_path])  # Pass the uploaded image to the picker script

        return redirect(url_for('home'))  # Redirect back to the home page after processing

@app.route('/detect', methods=['POST'])
def detect():
    if 'video' not in request.files:
        return "No file part", 400
    video = request.files['video']
    if video.filename == '':
        return "No selected file", 400
    if video:
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], video.filename)
        video.save(video_path)

        # Redirect to result page to display the processed video
        return render_template('live.html', video_path=video_path)

@app.route('/live')
def live():
    video_path = request.args.get('video_path')
    return Response(generate_frames(video_path), mimetype='multipart/x-mixed-replace; boundary=frame')

def generate_frames(video_path):
    global free_spaces
    cap = cv2.VideoCapture(video_path)

    posList = []
    try:
        # Open pickle file and load parking space positions
        with open('slot', 'rb') as f:
            posList = pickle.load(f)

        width, height = 107, 48

        def checkParkingSpace(img, imgPro):
            global free_spaces  # Use the global variable directly
            free_spaces.clear()  # Clear the list at the start of each frame
            spaceCounter = 0

            for idx, pos in enumerate(posList):
                x, y = pos

                imgCrop = imgPro[y:y + height, x:x + width]
                count = cv2.countNonZero(imgCrop)

                space_number = idx + 1  # Assign a unique number to each parking space
                if count < 900:
                    color = (0, 255, 0)
                    thickness = 5
                    spaceCounter += 1
                    free_spaces.append(space_number)  # Add free space number to the list
                else:
                    color = (0, 0, 255)
                    thickness = 2

                cv2.rectangle(img, pos, (pos[0] + width, pos[1] + height), color, thickness)
                cvzone.putTextRect(img, f'Space {space_number}', (x, y + height - 3), scale=1,
                                   thickness=2, offset=0, colorR=color)

            cvzone.putTextRect(img, f'Free: {spaceCounter}/{len(posList)}', (100, 50), scale=3,
                               thickness=5, offset=20, colorR=(0, 200, 0))

        while True:
            if cap.get(cv2.CAP_PROP_POS_FRAMES) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            success, img = cap.read()
            if not success:
                break
            imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            imgBlur = cv2.GaussianBlur(imgGray, (3, 3), 1)
            imgThreshold = cv2.adaptiveThreshold(imgBlur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                 cv2.THRESH_BINARY_INV, 25, 16)
            imgMedian = cv2.medianBlur(imgThreshold, 5)
            kernel = np.ones((3, 3), np.uint8)
            imgDilate = cv2.dilate(imgMedian, kernel, iterations=1)

            checkParkingSpace(img, imgDilate)  # Update free spaces list

            # Convert frame to JPEG
            ret, jpeg = cv2.imencode('.jpg', img)
            if not ret:
                continue

            # Yield the frame as a response
            frame = jpeg.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    finally:
        cap.release()

@app.route('/available_slot', methods=['GET'])
def available_slot():
    # Return the free spaces as JSON along with the total count
    return jsonify({
        'availableSlot': free_spaces,
        'totalAvailableSlot': len(free_spaces)
    })


# Existing code ...

@app.route('/available')
def available():
    # Render the status page and pass free_spaces to display them
    return render_template('available.html', free_spaces=free_spaces)



# Existing code ...

@app.route('/clear', methods=['POST'])
def clear():
    # Clear the contents of the file instead of deleting it
    file_path = 'slot'
    if os.path.exists(file_path):
        with open(file_path, 'w') as file:
            pass  # This clears the file contents by overwriting it with nothing
        return '', 200
    return 'File not found', 404

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=10000debug=True)

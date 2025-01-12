import cv2
import pickle
import sys

width, height = 107, 48

try:
    with open('slot', 'rb') as f:
        posList = pickle.load(f)
except:
    posList = []

def mouseClick(events, x, y, flags, params):
    global posList

    if events == cv2.EVENT_LBUTTONDOWN:
        posList.append((x, y))  # Add position
        # Sort the positions by x first (column order), then by y (vertical order)
        posList.sort(key=lambda pos: (pos[0], pos[1]))  # Sort first by x (horizontal), then by y (vertical)
    if events == cv2.EVENT_RBUTTONDOWN:
        for i, pos in enumerate(posList):
            x1, y1 = pos
            if x1 < x < x1 + width and y1 < y < y1 + height:
                posList.pop(i)  # Remove position

    # Save the updated list
    with open('slot', 'wb') as f:
        pickle.dump(posList, f)

image_path = sys.argv[1]  # Get the image path from the command-line argument
img = cv2.imread(image_path)

while True:
    temp_img = img.copy()
    # Draw rectangles based on the sorted positions
    for pos in posList:
        cv2.rectangle(temp_img, pos, (pos[0] + width, pos[1] + height), (255, 0, 255), 2)

    cv2.imshow("Image", temp_img)
    cv2.setMouseCallback("Image", mouseClick)
    key = cv2.waitKey(1)
    if key == 27:  # Esc key to close
        break

cv2.destroyAllWindows()

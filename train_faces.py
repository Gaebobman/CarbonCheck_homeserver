import math
import os
import pickle
import sys
import time
from os import listdir, makedirs
from os.path import isdir, isfile, join
import cv2
import face_recognition
import numpy as np
import requests
import json
from face_recognition import face_recognition_cli
from face_recognition.face_recognition_cli import image_files_in_folder
from sklearn import neighbors

from config.database_config import CARBONCHECK_SERVER_URL, HOME_SERVER_ID


# https://blog.naver.com/chandong83/221695462391
# function for consecutive capture
def detect_face(frame, classifier):
    grayscale_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = classifier.detectMultiScale(grayscale_frame, 1.3, 3)   # image, image_scale, max_faces
    if len(faces) == 0:
        return None
    for(x,y,w,h) in faces:
        margin = 0.1 # 배경 비율
        x = int (x - w * margin) # x 좌표를 왼쪽으로 이동
        y = int (y - h * margin) # y 좌표를 위로 이동
        w = int (w * (1 + margin * 2)) # 너비를 늘림
        h = int (h * (1 + margin * 2)) # 높이를 늘림
        cropped_face = frame[y:y+h, x:x+w]
    
    return cropped_face



# https://blog.naver.com/chandong83/221695462391
def capture_face(user_name):
    classifier = cv2.CascadeClassifier("./data/haarcascade_frontalface_default.xml")
    if not isdir(f"./data/sub_data/{user_name}"):
        makedirs(f"./data/sub_data/{user_name}")
    # Capture for CSI Camera
    # capture= cv2.VideoCapture('nvarguscamerasrc ! video/x-raw(memory:NVMM), width=640, height=480, format=(string)NV12, framerate=(fraction)20/1 ! nvvidconv ! video/x-raw, format=(string)BGRx ! videoconvert ! video/x-raw, format=(string)BGR ! appsink' , cv2.CAP_GSTREAMER)
    # Capture for Webcam
    capture = cv2.VideoCapture("/dev/video0", cv2.CAP_V4L2)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    count = 0
    
    while True:
        result, frame = capture.read()
        if detect_face(frame, classifier) is not None:
            count+=1
            face = cv2.resize(detect_face(frame, classifier),(200,200))
            # face = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
            cv2.imwrite(f"./data/sub_data/{user_name}/{user_name}-{count}.png",face)
            cv2.putText(face,str(count),(50,50),cv2.FONT_HERSHEY_COMPLEX,1,(255,0,0),2)
            # cv2.imshow('Face Cropper',face)
        else:
            print("Face not Found")
            pass
        # Press Enter or get 100 images to break
        if cv2.waitKey(1)==13 or count==100:
            break
        time.sleep(0.1)
        

    capture.release()
    cv2.destroyAllWindows()

    print('Colleting Samples Complete!!!')

# https://github.com/ageitgey/face_recognition/blob/master/examples/face_recognition_knn.py

def train(train_dir, model_save_path=None, n_neighbors=None, knn_algo='ball_tree', verbose=False):
    """
    Trains a k-nearest neighbors classifier for face recognition.

    :param train_dir: directory that contains a sub-directory for each known person, with its name.

    (View in source code to see train_dir example tree structure)

    Structure:
        <train_dir>/
        ├── <person1>/
        │   ├── <somename1>.jpeg
        │   ├── <somename2>.jpeg
        │   ├── ...
        ├── <person2>/
        │   ├── <somename1>.jpeg
        │   └── <somename2>.jpeg
        └── ...

    :param model_save_path: (optional) path to save model on disk
    :param n_neighbors: (optional) number of neighbors to weigh in classification. Chosen automatically if not specified
    :param knn_algo: (optional) underlying data structure to support knn.default is ball_tree
    :param verbose: verbosity of training
    :return: returns knn classifier that was trained on the given data.
    """
    X = []
    y = []

    # Loop through each person in the training set
    for class_dir in os.listdir(train_dir):
        if not os.path.isdir(os.path.join(train_dir, class_dir)):
            continue

        # Loop through each training image for the current person
        for img_path in image_files_in_folder(os.path.join(train_dir, class_dir)):
            image = face_recognition.load_image_file(img_path)
            face_bounding_boxes = face_recognition.face_locations(image)

            if len(face_bounding_boxes) != 1:
                # If there are no people (or too many people) in a training image, skip the image.
                if verbose:
                    print("Image {} not suitable for training: {}".format(img_path, "Didn't find a face" if len(face_bounding_boxes) < 1 else "Found more than one face"))
            else:
                # Add face encoding for current image to the training set
                X.append(face_recognition.face_encodings(image, known_face_locations=face_bounding_boxes)[0])
                y.append(class_dir)

    # Determine how many neighbors to use for weighting in the KNN classifier
    if n_neighbors is None:
        n_neighbors = int(round(math.sqrt(len(X))))
        if verbose:
            print("Chose n_neighbors automatically:", n_neighbors)

    # Create and train the KNN classifier
    knn_clf = neighbors.KNeighborsClassifier(n_neighbors=n_neighbors, algorithm=knn_algo, weights='distance')
    knn_clf.fit(X, y)

    # Save the trained KNN classifier
    if model_save_path is not None:
        with open(model_save_path, 'wb') as f:
            pickle.dump(knn_clf, f)

    return knn_clf


def main():
    
    if len(sys.argv) != 2:
        print(f"Insufficient arguments\n\n Usage: python3 {sys.argv[1]} \"user_name\"")
        sys.exit()
    else:
        user_name = sys.argv[1]
    print(f'Please stay still in front of the camera : {user_name}')
    # capture_face(user_name)
    print("Captured 100 iamges, Now Train KNN classifier... ")
    # TODO: Use Only 80% of image for train, and user 20% for measure accuracy
    # classifier = train("data/sub_data", model_save_path="data/trained_knn_model.clf", n_neighbors=2)
    print("Training complete!")
    # Print User List
    # user_list_path = 'data/sub_data'
    # user_list = [item for item in os.listdir (user_list_path) if os.path.isdir (os.path.join (user_list_path, item))]
    
    # Training done, Notify server
    url = f"https://{CARBONCHECK_SERVER_URL}/training_done"
    headers = {"Content-Type": "application/json"}
    data = {'user_id': str(sys.argv[1]),'home_server_id': HOME_SERVER_ID,'result': True}
    response = requests.post(url, data=json.dumps(data),headers=headers)
    # Check the response status code
    if response.status_code == 200:
        print("Sent training done!!!")
        return 0
    else:
        print("Training done, But couldn't notify server...")
        return 1


if __name__ == "__main__":
    main()

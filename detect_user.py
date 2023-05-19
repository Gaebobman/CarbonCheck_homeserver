import cv2
import face_recognition
import pickle
import pymysql
import os
import time
import PIL
from config.database_config import *
from os.path import isdir, isfile, join

def predict(X_img_path, knn_clf=None, model_path=None, distance_threshold=0.6):
    """
    Recognizes faces in given image using a trained KNN classifier

    :param X_img_path: path to image to be recognized
    :param knn_clf: (optional) a knn classifier object. if not specified, model_save_path must be specified.
    :param model_path: (optional) path to a pickled knn classifier. if not specified, model_save_path must be knn_clf.
    :param distance_threshold: (optional) distance threshold for face classification. the larger it is, the more chance
           of mis-classifying an unknown person as a known one.
    :return: a list of names and face locations for the recognized faces in the image: [(name, bounding box), ...].
        For faces of unrecognized persons, the name 'unknown' will be returned.
    """
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    if not os.path.isfile(X_img_path) or os.path.splitext(X_img_path)[1][1:] not in ALLOWED_EXTENSIONS:
        raise Exception("Invalid image path: {}".format(X_img_path))

    if knn_clf is None and model_path is None:
        raise Exception("Must supply knn classifier either thourgh knn_clf or model_path")

    # Load a trained KNN model (if one was passed in)
    if knn_clf is None:
        with open(model_path, 'rb') as f:
            knn_clf = pickle.load(f)

    # Load image file and find face locations
    X_img=None
    try:
        X_img = face_recognition.load_image_file(X_img_path)
    except PIL.UnidentifiedImageError:
        return None
    X_face_locations = face_recognition.face_locations(X_img)

    # If no faces are found in the image, return an empty result.
    if len(X_face_locations) == 0:
        return []

    # Find encodings for faces in the test iamge
    faces_encodings = face_recognition.face_encodings(X_img, known_face_locations=X_face_locations)

    # Use the KNN model to find the best matches for the test face
    closest_distances = knn_clf.kneighbors(faces_encodings, n_neighbors=1)
    are_matches = [closest_distances[0][i][0] <= distance_threshold for i in range(len(X_face_locations))]

    # Predict classes and remove classifications that aren't within the threshold
    return [(pred, loc) if rec else ("@unknown", loc) for pred, loc, rec in zip(knn_clf.predict(faces_encodings), X_face_locations, are_matches)]


# function for consecutive capture
def detect_face(frame, classifier):
    grayscale_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = classifier.detectMultiScale(grayscale_frame, 1.3, 3)   # image, image_scale, max_faces
    if len(faces) == 0:
        return None
    for(x,y,w,h) in faces:
        margin = 0.3 # 배경 비율
        x = int (x - w * margin) # x 좌표를 왼쪽으로 이동
        y = int (y - h * margin) # y 좌표를 위로 이동
        w = int (w * (1 + margin * 2)) # 너비를 늘림
        h = int (h * (1 + margin * 2)) # 높이를 늘림
        cropped_face = frame[y:y+h, x:x+w]
    
    return cropped_face

def capture_visitor_face():
    classifier = cv2.CascadeClassifier("./data/haarcascade_frontalface_default.xml")
    # Capture for CSI Camera
    # capture= cv2.VideoCapture('nvarguscamerasrc ! video/x-raw(memory:NVMM), width=640, height=480, format=(string)NV12, framerate=(fraction)20/1 ! nvvidconv ! video/x-raw, format=(string)BGRx ! videoconvert ! video/x-raw, format=(string)BGR ! appsink' , cv2.CAP_GSTREAMER)
    # Capture for webcam
    capture = cv2.VideoCapture("/dev/video0", cv2.CAP_V4L2)
    count = 0
    
    while True:
        result, frame = capture.read()
        cv2.imshow("VideoFrame", frame)
        cropped_visitor_face = detect_face(frame, classifier)
        if cropped_visitor_face is not None:
            cv2.imwrite(f'./data/test_data/visitor.png', cropped_visitor_face)
            break
        else:
            print("Visitor Face not found ")
        if cv2.waitKey(1)==13:
            break

    capture.release()
    cv2.destroyAllWindows()
    print('visitor passed door')


def save_prediction_to_database_2(predictions):
    conn = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, 
                            password=MYSQL_PASSWORD, db=MYSQL_DB, charset='utf8')
     
    user_id = "@unknown"
    for name, (top, right, bottom, left) in predictions:
        if(not name.startswith('@')):
            user_id = name
            print(f'{name} Detected')
            break
        else:
            print("@UNKNOWN")
    if(user_id != "@unknown"):
        try:
            curs = conn.cursor()
            sql = "INSERT INTO visitor_info VALUES (%s, %s)"
            enterance_time = time.time()
            enterance_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(enterance_time))
            val = (user_id, enterance_time)
            curs.execute(sql, val)
            conn.commit()
        finally: 
            conn.close()

def main():
    while True:
        capture_visitor_face()
        predictions = predict("./data/test_data/visitor.png", model_path="./data/trained_knn_model.clf")
        if (predictions is not None):
            save_prediction_to_database_2(predictions)
        time.sleep(3)
    


if __name__ == "__main__":
    main()


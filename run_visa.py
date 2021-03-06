import os
import argparse
import cv2
import numpy as np
import importlib.util
import asyncio

from threading import Thread
from collections import deque
# BLE Client
from ble_client.connect import Connection


# Haptic characteristic uuid
HAPTIC_CHAR_UUID = "20000000-0001-11e1-ac36-0002a5d5c51b"

# Define VideoStream class to handle streaming of video from webcam in separate processing thread
# Source - Adrian Rosebrock, PyImageSearch: https://www.pyimagesearch.com/2015/12/28/increasing-raspberry-pi-fps-with-python-and-opencv/
class VideoStream:
    """Camera object that controls video streaming from the Picamera"""
    def __init__(self,resolution=(640,480),framerate=30):
        # Initialize the PiCamera and the camera image stream
        self.stream = cv2.VideoCapture(0)
        ret = self.stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        ret = self.stream.set(3,resolution[0])
        ret = self.stream.set(4,resolution[1])
            
        # Read first frame from the stream
        (self.grabbed, self.frame) = self.stream.read()

	    # Variable to control when the camera is stopped
        self.stopped = False

    def start(self):
	    # Start the thread that reads frames from the video stream
        Thread(target=self.update,args=()).start()
        return self

    def update(self):
        # Keep looping indefinitely until the thread is stopped
        while True:
            # If the camera is stopped, stop the thread
            if self.stopped:
                # Close camera resources
                self.stream.release()
                return

            # Otherwise, grab the next frame from the stream
            (self.grabbed, self.frame) = self.stream.read()

    def read(self):
	    # Return the most recent frame
        return self.frame

    def stop(self):
	    # Indicate that the camera and thread should be stopped
        self.stopped = True

# Define and parse input arguments
parser = argparse.ArgumentParser()
parser.add_argument('--modeldir', help='Folder the .tflite file is located in',
                    required=True)
parser.add_argument('--graph', help='Name of the .tflite file, if different than detect.tflite',
                    default='detect.tflite')
parser.add_argument('--labels', help='Name of the labelmap file, if different than labelmap.txt',
                    default='labelmap.txt')
parser.add_argument('--threshold', help='Minimum confidence threshold for displaying detected objects',
                    default=0.5)
parser.add_argument('--resolution', help='Desired webcam resolution in WxH. If the webcam does not support the resolution entered, errors may occur.',
                    default='1280x720')
parser.add_argument('--edgetpu', help='Use Coral Edge TPU Accelerator to speed up detection',
                    action='store_true')

args = parser.parse_args()

MODEL_NAME = args.modeldir
GRAPH_NAME = args.graph
LABELMAP_NAME = args.labels
min_conf_threshold = float(args.threshold)
resW, resH = args.resolution.split('x')
imW, imH = int(resW), int(resH)
use_TPU = args.edgetpu

# Import TensorFlow libraries
# If tflite_runtime is installed, import interpreter from tflite_runtime, else import from regular tensorflow
# If using Coral Edge TPU, import the load_delegate library
pkg = importlib.util.find_spec('tflite_runtime')
if pkg:
    from tflite_runtime.interpreter import Interpreter
    if use_TPU:
        from tflite_runtime.interpreter import load_delegate
else:
    from tensorflow.lite.python.interpreter import Interpreter
    if use_TPU:
        from tensorflow.lite.python.interpreter import load_delegate

# If using Edge TPU, assign filename for Edge TPU model
if use_TPU:
    # If user has specified the name of the .tflite file, use that name, otherwise use default 'edgetpu.tflite'
    if (GRAPH_NAME == 'detect.tflite'):
        GRAPH_NAME = 'edgetpu.tflite'       

# Get path to current working directory
CWD_PATH = os.getcwd()

# Path to .tflite file, which contains the model that is used for object detection
PATH_TO_CKPT = os.path.join(CWD_PATH,MODEL_NAME,GRAPH_NAME)

# Path to label map file
PATH_TO_LABELS = os.path.join(CWD_PATH,MODEL_NAME,LABELMAP_NAME)

# Load the label map
with open(PATH_TO_LABELS, 'r') as f:
    labels = [line.strip() for line in f.readlines()]

# Load the Tensorflow Lite model.
# If using Edge TPU, use special load_delegate argument
if use_TPU:
    interpreter = Interpreter(model_path=PATH_TO_CKPT,
                              experimental_delegates=[load_delegate('libedgetpu.so.1.0')])
    print(PATH_TO_CKPT)
else:
    interpreter = Interpreter(model_path=PATH_TO_CKPT)

interpreter.allocate_tensors()

# Get model details
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
height = input_details[0]['shape'][1]
width = input_details[0]['shape'][2]

floating_model = (input_details[0]['dtype'] == np.float32)

input_mean = 127.5
input_std = 127.5

detector_item_name = "hand"
detect_item_name = "apple"
detect_item_position = []

feedback_queue = deque(maxlen=3)

# Initialize video stream
videostream = VideoStream(resolution=(imW,imH),framerate=30)

# Create window
cv2.namedWindow('Object detector', cv2.WINDOW_NORMAL)
    
def start_object_detection():
    # Initialize frame rate calculation
    frame_rate_calc = 1
    freq = cv2.getTickFrequency()
    
    print('Starting object detection')
    
    while True:
        # Start timer (for calculating frame rate)
        t1 = cv2.getTickCount()
        # Grab frame from video stream
        frame1 = videostream.read()

        # Acquire frame and resize to expected shape [1xHxWx3]
        frame = frame1.copy()
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_resized = cv2.resize(frame_rgb, (width, height))
        input_data = np.expand_dims(frame_resized, axis=0)

        # Normalize pixel values if using a floating model (i.e. if model is non-quantized)
        if floating_model:
            input_data = (np.float32(input_data) - input_mean) / input_std

        # Perform the actual detection by running the model with the image as input
        interpreter.set_tensor(input_details[0]['index'],input_data)
        interpreter.invoke()

        # Retrieve detection results
        boxes = interpreter.get_tensor(output_details[0]['index'])[0] # Bounding box coordinates of detected objects
        classes = interpreter.get_tensor(output_details[1]['index'])[0] # Class index of detected objects
        scores = interpreter.get_tensor(output_details[2]['index'])[0] # Confidence of detected objects

        # Loop over all detections and draw detection box if confidence is above minimum threshold
        for i in range(len(scores)):
            if ((scores[i] > min_conf_threshold) and (scores[i] <= 1.0) and (labels[int(classes[i])] == detector_item_name or labels[int(classes[i])] == detect_item_name )):

                # Get bounding box coordinates and draw box
                # Interpreter can return coordinates that are outside of image dimensions, need to force them to be within image using max() and min()
                ymin = int(max(1,(boxes[i][0] * imH)))
                xmin = int(max(1,(boxes[i][1] * imW)))
                ymax = int(min(imH,(boxes[i][2] * imH)))
                xmax = int(min(imW,(boxes[i][3] * imW)))
                
                cv2.rectangle(frame, (xmin,ymin), (xmax,ymax), (10, 255, 0), 2)
                
                # Draw label
                object_name = labels[int(classes[i])] # Look up object name from "labels" array using class index
                label = '%s: %d%%' % (object_name, int(scores[i]*100)) # Example: 'person: 72%'?
                labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2) # Get font size
                label_ymin = max(ymin, labelSize[1] + 10) # Make sure not to draw label too close to top of window
                cv2.rectangle(frame, (xmin, label_ymin-labelSize[1]-10), (xmin+labelSize[0], label_ymin+baseLine-10), (255, 255, 255), cv2.FILLED) # Draw white box to put label text in
                cv2.putText(frame, label, (xmin, label_ymin-7), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2) # Draw label text

                # Draw circle in center
                xcenter = xmin + (int(round((xmax - xmin) / 2)))
                ycenter = ymin + (int(round((ymax - ymin) / 2)))
                cv2.circle(frame, (xcenter, ycenter), 5, (0,0,255), thickness=-1)
                
                # Cache the item position to send out events where to move
                if (object_name == detect_item_name):
                    # Cache the item 
                    detect_item_position.insert(0, xmin)
                    detect_item_position.insert(1, xmax)
                    detect_item_position.insert(2, ymin)
                    detect_item_position.insert(3, ymax)
                # Guide the "item" to the correct position    
                elif (object_name == detector_item_name and detect_item_position):
                    
                    # Go Forward 
                    if (xmin < detect_item_position[0] and xmax > detect_item_position[1] and ymin < detect_item_position[2] and ymax > detect_item_position[3]):
                        print('Go Forward')
                        feedback_queue.append(5)
                    # Go Right
                    elif (xcenter < detect_item_position[0]):
                        print('Go Right')
                        feedback_queue.append(1)
                     # Go Left
                    elif (xcenter > detect_item_position[1]):
                        print('Go Left')
                        feedback_queue.append(2)
                    # Go Up     
                    elif (ycenter < detect_item_position[2]):
                        print('Go Up')
                        feedback_queue.append(3)
                    # Go Down  
                    elif (ycenter > detect_item_position[3]):
                        print('Go Down')
                        feedback_queue.append(4)
			
        # Draw framerate in corner of frame
        cv2.putText(frame,'FPS: {0:.2f}'.format(frame_rate_calc),(30,50),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,0),2,cv2.LINE_AA)

        # All the results have been drawn on the frame, so it's time to display it.
        cv2.imshow('Object detector', frame)

        # Calculate framerate
        t2 = cv2.getTickCount()
        time1 = (t2-t1)/freq
        frame_rate_calc = 1/time1
        
            # Press 'q' to quit
        if cv2.waitKey(1) == ord('q'):
            print('Stopping object detection')
            break

    # Clean up
    cv2.destroyAllWindows()
    videostream.stop()
    
def _start_async():
    loop = asyncio.new_event_loop()
    t = Thread(target=loop.run_forever)
    t.daemon = True
    t.start()
    return loop
    
_loop = _start_async()

def submit_async(awaitable):
    return asyncio.run_coroutine_threadsafe(awaitable, _loop)

async def run_haptic_feedback(connection: Connection):
    while True:
        #print(f'run haptic feedback connection: {connection} is connected {connection.connected}' )
        if(connection.client and connection.connected and feedback_queue):
            direction = feedback_queue.pop()
            feedback = bytes([direction])
            await connection.client.write_gatt_char(HAPTIC_CHAR_UUID, feedback)
        else:
            await asyncio.sleep(1)


async def main():

    os.system('bluetoothctl -- remove C0:CC:BB:AA:AA:AA')
    device_ble_mac = os.getenv('DEVICE_BLE_MAC')
    os.system('sudo rm "/var/lib/bluetooth/{}/cache/C0:CC:BB:AA:AA:AA"'.format(device_ble_mac))
    
    videostream.start()
    
    connection = Connection(_loop)
    
    submit_async(connection.manager())
    submit_async(run_haptic_feedback(connection))
    
    start_object_detection()
   
asyncio.run(main())

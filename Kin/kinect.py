from pykinect2 import PyKinectRuntime
from pykinect2 import PyKinectV2
import cv2
import numpy as np

# Initialize Kinect sensor
kinect = PyKinectRuntime.PyKinectRuntime(PyKinectV2.FrameSourceTypes_Color |
                                         PyKinectV2.FrameSourceTypes_Depth |
                                         PyKinectV2.FrameSourceTypes_Infrared)

def get_color_frame():
    if kinect.has_new_color_frame():
        frame = kinect.get_last_color_frame()
        return frame.reshape((1080, 1920, 4))[:, :, :3]  # Remove alpha channel

def get_depth_frame():
    if kinect.has_new_depth_frame():
        frame = kinect.get_last_depth_frame()
        return frame.reshape((424, 512))

def get_infrared_frame():
    if kinect.has_new_infrared_frame():
        frame = kinect.get_last_infrared_frame()
        return frame.reshape((424, 512))

while True:
    color_frame = get_color_frame()
    depth_frame = get_depth_frame()
    infrared_frame = get_infrared_frame()

    if color_frame is not None:
        cv2.imshow('RGB Image', cv2.cvtColor(color_frame, cv2.COLOR_RGB2BGR))

    if depth_frame is not None:
        cv2.imshow('Depth Image', depth_frame.astype(np.uint8))

    if infrared_frame is not None:
        cv2.imshow('Infrared Image', infrared_frame.astype(np.uint8))

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
kinect.close()

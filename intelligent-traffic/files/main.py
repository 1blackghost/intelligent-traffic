import time
import requests
import pandas as pd
import cv2
from ultralytics import YOLO  # Import YOLO from ultralytics package

# Set your URL for controlling the traffic lights
url = 'http://192.168.33.1:5000/'

# Load YOLOv8 model
model = YOLO('yolov8s.pt')  # Specify YOLOv8 model file
def find_and_count_vehicles(frame, lane_number):
    results = model(frame)
    boxes = results[0].boxes
    
    vehicle_classes = [2, 3, 5, 7, 8]  # Vehicle classes: Car, Truck, Bus, Motorcycle, etc.
    
    df = pd.DataFrame({
        "confidence": boxes.conf.cpu().numpy(),
        "class": boxes.cls.cpu().numpy(),
        "xmin": boxes.xywh[:, 0].cpu().numpy(),
        "ymin": boxes.xywh[:, 1].cpu().numpy(),
        "xmax": boxes.xywh[:, 2].cpu().numpy(),
        "ymax": boxes.xywh[:, 3].cpu().numpy()
    })
    
    confidence_threshold = 0.50
    filtered_df = df[(df['confidence'] >= confidence_threshold) & (df['class'].isin(vehicle_classes))]
    
    print(f"Lane {lane_number} detected vehicles: {filtered_df.shape[0]}")  # Debugging count for each lane
    
    return len(filtered_df)

# Function to set the traffic lights based on the configuration
def set_lights(light_config):
    try:
        lights_data = {"lights": light_config}
        response = requests.post(url+"set-lights", json=lights_data)

        if response.status_code == 200:
            print("Lights set successfully")
        else:
            print("Failed to set lights:", response.status_code, response.json())
    except:
        print("Set light failed:")
        return 
def get_data(data):
    try:
        # Prepare the payload
        data_payload = {"data": [data]}

        # Make the POST request with headers to indicate the data is JSON
        headers = {"Content-Type": "application/json"}
        response = requests.post(url+"/data", json=data_payload, headers=headers)

        # Print the raw response content for debugging
        print("Response Status Code:", response.status_code)
        print("Response Content:", response.text)

        if response.status_code == 200:
            print("Lights data successfully updated.")
        else:
            print("Failed to set data:", response.status_code, response.json())
    except Exception as e:
        print("Set data failed:", str(e))
    

# Function to print the light statuses (for debugging)
def print_lights_status(lane_status):
    for i, status in enumerate(lane_status):
        color = ["Red", "Yellow", "Green"][status.index(1)]
        print(f"Lane {i+1}: {color}")

# Function to rotate the traffic lights after each cycle
def rotate_lights(lights_config):
    updated_config = []

    for lane in lights_config:
        if lane == [0, 0, 1]:
            updated_config.append([1, 0, 0])  # Green to Red
        elif lane == [0, 1, 0]:
            updated_config.append([0, 0, 1])  # Yellow to Green
        elif lane == [1, 0, 0]:
            updated_config.append([0, 1, 0])  # Red to Yellow
        else:
            updated_config.append(lane)

    return updated_config

# Main function to control the traffic system
def control_traffic():
    lane_videos = [cv2.VideoCapture(url+"/stream/lane1"),  # Stream URLs from server
                   cv2.VideoCapture(url+"/stream/lane2"),
                   cv2.VideoCapture(url+"/stream/lane3")]

    lane_counts = [0, 0, 0]
    frame_id = 0

    while True:
        lane_frames = []

        # Read one frame from each lane's video at the same time (simultaneously for 3 lanes)
        for cap in lane_videos:
            ret, frame = cap.read()
            if not ret:
                print("End of video feed or error reading frames.")
                return
            lane_frames.append(frame)
        time.sleep(2)
        # Count vehicles in each lane
        lane_counts[0] = find_and_count_vehicles(lane_frames[0],1)
        lane_counts[1] = find_and_count_vehicles(lane_frames[1],2)
        lane_counts[2] = find_and_count_vehicles(lane_frames[2],3)

        # Print total vehicle count for all lanes
        total_vehicles = sum(lane_counts)
        print(lane_counts)
        print(f"Total vehicles detected: {total_vehicles}")
        get_data(lane_counts)


        # Sort lanes based on vehicle count, with the lane with the most vehicles first
        sorted_lanes = sorted(range(len(lane_counts)), key=lambda i: lane_counts[i], reverse=True)

        next_lights_config = [[0, 0, 0] for _ in range(3)]
        next_lights_config[sorted_lanes[0]] = [0, 0, 1]  # Green for the lane with most vehicles
        next_lights_config[sorted_lanes[1]] = [0, 1, 0]  # Yellow for the second lane
        next_lights_config[sorted_lanes[2]] = [1, 0, 0]  # Red for the least traffic lane

        # Print and set the light configuration
        print_lights_status(next_lights_config)
        try:
            set_lights(next_lights_config)
        except:
            print("Setting lights failed!")

        # Rotate lights after 10 seconds
        time.sleep(3)
        set_lights(next_lights_config)

        # Sleep for 1 second before processing the next frame (simulating real-time processing)
        time.sleep(1)
        frame_id += 1

        # Check if the user pressed 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release video captures and close all OpenCV windows
    for cap in lane_videos:
        cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    control_traffic()

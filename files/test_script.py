import time
import requests
import torch
import random

model = torch.hub.load('ultralytics/yolov5', 'yolov5s')

url = 'http://192.168.1.8:5000/set-lights'

def find_count(img_path):
    results = model(img_path)
    df = results.pandas().xyxy[0]
    
    confidence_threshold = 0.50
    filtered_df = df[df['confidence'] >= confidence_threshold]
    
    normal_vehicle_classes = ['car', 'motorbike', 'bus', 'truck']
    emergency_vehicle_classes = ['ambulance', 'fire truck']
    
    normal_vehicles_df = filtered_df[filtered_df['name'].isin(normal_vehicle_classes)]
    emergency_vehicles_df = filtered_df[filtered_df['name'].isin(emergency_vehicle_classes)]
    
    return len(normal_vehicles_df) + len(emergency_vehicles_df)

def set_lights(light_config):
    lights_data = {"lights": light_config}
    response = requests.post(url, json=lights_data)
    
    if response.status_code == 200:
        print("Lights set successfully")
    else:
        print("Failed to set lights:", response.status_code, response.json())

def print_lights_status(lane_status):
    for i, status in enumerate(lane_status):
        color = ["Red", "Yellow", "Green"][status.index(1)]
        print(f"Lane {i+1}: {color}")

def rotate_lights(lights_config):
    updated_config = []
    
    for lane in lights_config:
        if lane == [0, 0, 1]:
            updated_config.append([1, 0, 0])
        elif lane == [0, 1, 0]:
            updated_config.append([0, 0, 1])
        elif lane == [1, 0, 0]:
            updated_config.append([0, 1, 0])
        else:
            updated_config.append(lane)

    return updated_config

def control_traffic():
    lane_images = ["lane1.jpg", "lane2.jpg", "lane3.jpg"]
    prev_lights_config = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    
    lane_counts = [find_count(img) for img in lane_images]
    print("Vehicle counts:", lane_counts)
        
    sorted_lanes = sorted(range(len(lane_counts)), key=lambda i: lane_counts[i], reverse=True)
        
    next_lights_config = [[0, 0, 0] for _ in range(3)]
        
    next_lights_config[sorted_lanes[0]] = [0, 0, 1]
    next_lights_config[sorted_lanes[1]] = [0, 1, 0]
    next_lights_config[sorted_lanes[2]] = [1, 0, 0]
    
    print_lights_status(next_lights_config)
    set_lights(next_lights_config)
    time.sleep(10)
    
    while True:
        new = rotate_lights(next_lights_config)
        print_lights_status(new)
        set_lights(new)
        next_lights_config = new
        time.sleep(10)

if __name__ == "__main__":
    control_traffic()

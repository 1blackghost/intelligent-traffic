import time
import requests
import pandas as pd
import cv2
from ultralytics import YOLO  # Import YOLO from ultralytics package

# Set your URL for controlling the traffic lights
url = 'http://192.168.1.8:5000/set-lights'

# Load YOLOv8 model
model = YOLO('yolov8s.pt')  # Specify YOLOv8 model file

# Function to find vehicles and draw boxes on the frame
def find_and_draw_count(frame):
    # Run inference on the frame
    results = model(frame)  # Inference on the frame directly
    boxes = results[0].boxes  # Extract boxes from the first result

    # Convert boxes data to a dictionary and then to a DataFrame for easier filtering
    df = pd.DataFrame({
        "confidence": boxes.conf.cpu().numpy(),
        "class": boxes.cls.cpu().numpy(),
        "xmin": boxes.xywh[:, 0].cpu().numpy(),
        "ymin": boxes.xywh[:, 1].cpu().numpy(),
        "xmax": boxes.xywh[:, 2].cpu().numpy(),
        "ymax": boxes.xywh[:, 3].cpu().numpy()
    })

    confidence_threshold = 0.50
    filtered_df = df[df['confidence'] >= confidence_threshold]

    # Draw rectangles around the vehicles
    for _, row in filtered_df.iterrows():
        xmin, ymin, xmax, ymax = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
        cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)  # Green for normal vehicles
    
    return len(filtered_df), frame  # Return the number of vehicles and the frame with bounding boxes

# Function to set the traffic lights based on the configuration
def set_lights(light_config):
    lights_data = {"lights": light_config}
    response = requests.post(url, json=lights_data)

    if response.status_code == 200:
        print("Lights set successfully")
    else:
        print("Failed to set lights:", response.status_code, response.json())

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
    lane_videos = [cv2.VideoCapture("http://localhost:5000/stream/lane1"),  # Stream URLs from server
                   cv2.VideoCapture("http://localhost:5000/stream/lane2"),
                   cv2.VideoCapture("http://localhost:5000/stream/lane3")]

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

        # Process each frame for vehicles and draw bounding boxes
        for i, frame in enumerate(lane_frames):
            vehicle_count, frame_with_boxes = find_and_draw_count(frame)
            print(f"Lane {i + 1}: Detected {vehicle_count} vehicles")

            # Display the frame with bounding boxes
            cv2.imshow(f"Lane {i + 1} Frame", frame_with_boxes)

        # Calculate lane vehicle counts for setting the lights
        lane_counts[0] = find_and_draw_count(lane_frames[0])[0]
        lane_counts[1] = find_and_draw_count(lane_frames[1])[0]
        lane_counts[2] = find_and_draw_count(lane_frames[2])[0]

        # Sort lanes based on vehicle count, with the lane with the most vehicles first
        sorted_lanes = sorted(range(len(lane_counts)), key=lambda i: lane_counts[i], reverse=True)

        next_lights_config = [[0, 0, 0] for _ in range(3)]
        next_lights_config[sorted_lanes[0]] = [0, 0, 1]  # Green for the lane with most vehicles
        next_lights_config[sorted_lanes[1]] = [0, 1, 0]  # Yellow for the second lane
        next_lights_config[sorted_lanes[2]] = [1, 0, 0]  # Red for the least traffic lane

        # Print and set the light configuration
        print_lights_status(next_lights_config)
        set_lights(next_lights_config)

        # Rotate lights after 10 seconds
        time.sleep(10)
        next_lights_config = rotate_lights(next_lights_config)
        print_lights_status(next_lights_config)
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

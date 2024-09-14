from flask import Flask, request, jsonify
import RPi.GPIO as GPIO
import time

app = Flask(__name__)

# GPIO pin configuration for each lane
lanes = {
    'lane1': {'red': 14, 'yellow': 15, 'green': 26},
    'lane2': {'red': 23, 'yellow': 24, 'green': 25},
    'lane3': {'red': 5, 'yellow': 6, 'green': 13},
}

# Setup GPIO mode
GPIO.setmode(GPIO.BCM)

# Setup GPIO pins as output
for lane in lanes.values():
    for color, pin in lane.items():
        GPIO.setup(pin, GPIO.OUT)

def control_lights(lights_matrix):
    for lane_idx, lane_state in enumerate(lights_matrix):
        lane_name = f'lane{lane_idx + 1}'
        lane_pins = lanes[lane_name]

        GPIO.output(lane_pins['red'], lane_state[0])
        GPIO.output(lane_pins['yellow'], lane_state[1])
        GPIO.output(lane_pins['green'], lane_state[2])

@app.route('/set-lights', methods=['POST'])
def set_lights():
    try:
        # Get the 2D array from the POST request
        lights_matrix = request.json['lights']
        
        # Ensure it's a valid array for 3 lanes
        if len(lights_matrix) != 3 or any(len(lane) != 3 for lane in lights_matrix):
            return jsonify({"error": "Invalid array format. Must be 3x3."}), 400
        
        # Control the traffic lights based on the input
        control_lights(lights_matrix)
        
        return jsonify({"status": "Success, lights updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

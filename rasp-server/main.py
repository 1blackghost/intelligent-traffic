from flask import Flask, request, jsonify, render_template, session, Response
import cv2
import time

app = Flask(__name__)
app.secret_key = "1234"
data = [
    [0, 0, 0] 
]
lanes = {
    'lane1': {'red': 14, 'yellow': 15, 'green': 26},
    'lane2': {'red': 23, 'yellow': 24, 'green': 25},
    'lane3': {'red': 5, 'yellow': 6, 'green': 13},
}

VALID_USERNAME = "a"
VALID_PASSWORD = "a"

@app.route("/fetch")
def fetch():
    global data
    
    vehicle_data = {
        "lane1": data[0][0],  
        "lane2": data[0][1],  
        "lane3":data[0][2] 
    }
    print(vehicle_data)
    return jsonify(vehicle_data)
@app.route("/")
def login_page():
    return render_template("index.html")

@app.route("/validate-login", methods=["POST"])
def validate_login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if username == VALID_USERNAME and password == VALID_PASSWORD:
        session["user"] = "admin"
        return jsonify({"status": "Success"}), 200
    else:
        return jsonify({"status": "Failure"}), 401

@app.route("/dash")
def control_panel():
    if "user" in session:
        return render_template("dash.html")

cap_lane1 = cv2.VideoCapture("1.mp4")  
cap_lane2 = cv2.VideoCapture("2.mp4")
cap_lane3 = cv2.VideoCapture("3.mp4")

def generate_video_stream(capture_device, lane):
    """Function to generate video stream from a video capture device (OpenCV)"""
    while True:
        ret, frame = capture_device.read()
        
        if not ret:
            capture_device.set(cv2.CAP_PROP_POS_FRAMES, 0)  
            ret, frame = capture_device.read()  

        if not ret:
            print(f"Error reading video for Lane {lane}")
            break
        
        ret, jpeg = cv2.imencode('.jpg', frame)
        if not ret:
            print(f"Error encoding frame for Lane {lane}")
            break

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')


@app.route('/data', methods=['POST'])
def handle_data():
    try:
        global data
        data = request.json['data']
        print("Received data:", data)
        

        return jsonify({"status": "Success, lights updated"}), 200
    except Exception as e:
        print(f"Error processing data: {str(e)}")
        return jsonify({"error": f"Error processing data: {str(e)}"}), 400

@app.route("/stream/lane1")
def stream_lane1():
    """Video stream for lane 1"""
    return Response(generate_video_stream(cap_lane1,"1"),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/stream/lane2")
def stream_lane2():
    """Video stream for lane 2"""
    return Response(generate_video_stream(cap_lane2,"2"),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/stream/lane3")
def stream_lane3():
    """Video stream for lane 3"""
    return Response(generate_video_stream(cap_lane3,"3"),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


import RPi.GPIO as GPIO
import time


GPIO.setmode(GPIO.BCM)

@app.route("/")
def login():
    return render_template("index.html")


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
        lights_matrix = request.json['lights']
        
        if len(lights_matrix) != 3 or any(len(lane) != 3 for lane in lights_matrix):
            return jsonify({"error": "Invalid array format. Must be 3x3."}), 400
        
        control_lights(lights_matrix)
        
        return jsonify({"status": "Success, lights updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,debug=True)

# Save this as stream_server.py
import time
import io
import threading
from picamera2 import Picamera2
from flask import Flask, Response

# --- Setup ---
app = Flask(__name__)
# Create an in-memory buffer to hold the current frame
output = io.BytesIO() 
lock = threading.Lock()
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))

# --- Background Frame Capture Thread ---
def camera_loop():
    # Start the camera with a callback function for frame capture
    picam2.start_preview()
    time.sleep(1) # Wait for camera to warm up
    
    # Use Picamera2's own built-in streaming/callback method
    picam2.start(show_preview=False) 

    try:
        # Loop forever, generating and yielding frames
        while True:
            # Capture the frame as a JPEG
            buffer = io.BytesIO()
            picam2.capture_file(buffer, format='jpeg')
            
            with lock:
                output.seek(0)
                output.truncate()
                output.write(buffer.getvalue())
            
            time.sleep(0.05) # Control frame rate (20 FPS max)

    finally:
        picam2.stop()

# Start the camera capture loop in a separate thread
threading.Thread(target=camera_loop, daemon=True).start()

# --- Web Server Functions ---

def generate():
    """Generator function to continuously yield MJPEG frames."""
    while True:
        with lock:
            # Read the latest frame from the buffer
            frame = output.getvalue()
        
        # Yield the frame in the MJPEG format required by browsers
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.01)

@app.route('/video_feed')
def video_feed():
    """The main route for the video stream."""
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    """Simple HTML page to view the stream."""
    # Note: Use your Pi's actual IP address instead of 0.0.0.0
    return ('<html><body>'
            '<h1>Raspberry Pi Camera Stream</h1>'
            '<img src="/video_feed" width="640" height="480">'
            '</body></html>')

if __name__ == '__main__':
    # Find your Pi's IP address (e.g., 192.168.1.100) and use it to connect
    app.run(host='0.0.0.0', port=8080, threaded=True)
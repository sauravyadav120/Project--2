import boto3
import time
import threading
import schedule
import os
from datetime import datetime
from PIL import ImageGrab, Image
from pynput import mouse, keyboard
from pytz import timezone
import psutil

s3_client = boto3.client('s3', aws_access_key_id='YOUR_AWS_ACCESS_KEY', aws_secret_access_key='YOUR_AWS_SECRET_KEY', region_name='YOUR_AWS_REGION')

SCREENSHOT_INTERVAL = 5 
UPLOAD_BUCKET = 'your-s3-bucket-name'
UPLOAD_FOLDER = 'screenshots/'
SHOULD_BLUR = False
TRACKED_ACTIVITY_LOG = "activity_log.txt"

def track_activity():
    def on_move(x, y):
        with open(TRACKED_ACTIVITY_LOG, "a") as log:
            log.write(f"Mouse moved to {(x, y)} at {datetime.now()}\n")

    def on_click(x, y, button, pressed):
        with open(TRACKED_ACTIVITY_LOG, "a") as log:
            log.write(f"Mouse clicked at {(x, y)} with {button} at {datetime.now()}\n")

    def on_press(key):
        with open(TRACKED_ACTIVITY_LOG, "a") as log:
            log.write(f"Key {key} pressed at {datetime.now()}\n")

    with mouse.Listener(on_move=on_move, on_click=on_click) as mouse_listener, keyboard.Listener(on_press=on_press) as keyboard_listener:
        mouse_listener.join()
        keyboard_listener.join()

def capture_screenshot():
    screenshot = ImageGrab.grab()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = f"screenshot_{timestamp}.png"

    if SHOULD_BLUR:
        screenshot = screenshot.filter(Image.BLUR)
    
    screenshot.save(screenshot_path)
    print(f"Screenshot saved at {screenshot_path}")
    return screenshot_path

def upload_to_s3(file_path):
    try:
        s3_client.upload_file(file_path, UPLOAD_BUCKET, UPLOAD_FOLDER + os.path.basename(file_path))
        print(f"Uploaded {file_path} to S3.")
        os.remove(file_path)  
    except Exception as e:
        print(f"Error uploading file: {e}")

def check_time_zone():
    local_zone = timezone('America/New_York')  
    local_time = datetime.now(local_zone)
    print(f"Current Time Zone: {local_zone}, Local Time: {local_time}")

def schedule_screenshots():
    screenshot_path = capture_screenshot()
    upload_to_s3(screenshot_path)

def check_system_health():
    battery = psutil.sensors_battery()
    if battery and battery.percent < 20 and battery.power_plugged is False:
        print("Low battery! Pausing activity tracking.")
        return False  
    return True

def start_agent():
    schedule.every(SCREENSHOT_INTERVAL).minutes.do(schedule_screenshots)
    
    activity_thread = threading.Thread(target=track_activity)
    activity_thread.daemon = True
    activity_thread.start()
    
    while True:
        schedule.run_pending()

        check_time_zone()

        if not check_system_health():
            break  

        time.sleep(1)

if __name__ == "__main__":
    start_agent()

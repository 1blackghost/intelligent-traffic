import RPi.GPIO as GPIO
import time

# Pin setup
pins = [14,15,26,23,24,25,5,6,13]
# Set up the GPIO mode


try:
    for i in pins:
        print(i)
        GPIO.setmode(GPIO.BCM)  # Use Broadcom pin-numbering
        GPIO.setup(i, GPIO.OUT)  # Set GPIO 14 as an output pin
        GPIO.output(i, GPIO.HIGH)  # Turn on the LED
        print("LED ON")
        time.sleep(1)  # Wait for 1 second

        GPIO.output(i, GPIO.LOW)  # Turn off the LED
        print("LED OFF")
        time.sleep(1)  # Wait for 1 second

except KeyboardInterrupt:
    # Clean up GPIO on CTRL+C exit
    GPIO.cleanup()

except Exception as e:
    print(f"An error occurred: {e}")
    GPIO.cleanup()

finally:
    # Clean up GPIO on normal exit
    GPIO.cleanup()

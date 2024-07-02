from machine import Pin, ADC
from dht import DHT11
import time
import urequests as requests
import keys

# Set up DHT11 sensor
dht_pin = Pin(15, Pin.IN, Pin.PULL_UP)
dht_sensor = DHT11(dht_pin)

# Set up photoresistor
photoresistor_pin = ADC(26)

# Set up LED
green_led = Pin(18, Pin.OUT)

# Notification thresholds
TEMP_THRESHOLD = 30
LIGHT_THRESHOLD = 100

# Function to read temperature and humidity from DHT11 sensor
def read_dht11():
    dht_sensor.measure()
    temperature = dht_sensor.temperature()
    humidity = dht_sensor.humidity()
    return temperature, humidity

# Function to read light intensity from photoresistor
def read_light_intensity():
    adc_value = photoresistor_pin.read_u16()
    voltage = adc_value * 3.3 / 65535
    light_intensity = voltage * 1000
    return light_intensity

# Function to send data to Ubidots
def send_to_ubidots(temperature, humidity, light_intensity):
    headers = {"X-Auth-Token": keys.UBIDOTS_TOKEN, "Content-Type": "application/json"}
    data = {
        keys.UBIDOTS_VARIABLE_LABEL_TEMP: temperature,
        keys.UBIDOTS_VARIABLE_LABEL_HUMIDITY: humidity,
        keys.UBIDOTS_VARIABLE_LABEL_LIGHT: light_intensity
    }
    try:
        response = requests.post(keys.UBIDOTS_URL, headers=headers, json=data)
        response.close()
        print("Data sent to Ubidots")
    except Exception as e:
        print("Failed to send data to Ubidots:", e)

# Function to send notification using NTFY.SH
def send_notification(notification):
    url = f"https://ntfy.sh/{notification["type"]}"
    response = requests.post(
        url,
        data=notification["message"],
        headers={
            "Title": notification["title"],
            "Priority": "5",
            "Tags": notification["tag"],
        }
    )
    # Check if the notification was sent successfully
    if response.status_code == 200:
        print("Notification sent successfully")
    else:
        print("Failed to send notification", response.status_code)

# Main loop
while True:
    green_led.on()

    # Read temperature, humidity, and light intensity
    temperature, humidity = read_dht11()
    light_intensity = read_light_intensity()

    # Print temperature, humidity, and light intensity
    print(f"Temperature: {temperature}C")
    print(f"Humidity: {humidity}%")
    print(f"Light Intensity: {light_intensity:.2f} (scaled value)")

    # Send notification if temperature is above 30C
    if temperature is not None and temperature > TEMP_THRESHOLD:
        notification = {
            "type": "temp_warning",
            "message": f"Temperature is above 30C ({temperature}C), consider opening the window.",
            "title": "ALERT: Temperature",
            "tag": "thermometer"
        }
        send_notification(notification)

    # Send notification if light intensity is higher than 100
    if light_intensity is not None and light_intensity < LIGHT_THRESHOLD:
        notification = {
            "type": "light_warning",
            "message": f"The light in the room is too bright ({light_intensity:.1f}), consider closing the blinds.",
            "title": "ALERT: Light intensity",
            "tag": "sunny"
        }
        send_notification(notification)

    # Send data to Ubidots
    if temperature is not None and humidity is not None and light_intensity is not None:
        send_to_ubidots(temperature, humidity, light_intensity)
    else:
        green_led.off()

    # Wait for 1 hour before taking the next reading
    time.sleep(3600)
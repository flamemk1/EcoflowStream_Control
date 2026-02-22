# Zero Feed-In Ecoflow Stream

Unfortunately, the official Ecoflow API does not support setting the AC output power of the Stream devices. This means, a zero feed-in can only be realized with one of the supported power meters.
This script can be used to realize zero feed-in with a Ecoflow Stream Pro without using one of the supported power meters. Stream Ultra/X Ultra/AC might also work.
All you need is:

- Current power consumption via MQTT
- MQTT credentials of the official Ecoflow API
- MQTT credentials of the Ecoflow App

## WARNING

This script uses a non-offical communication with the devices.
Wrong communication or setting wrong values can affect the functionality of the device and may lead to exclusion from the service.

## Installation

A python 3 installation is required.
Install the required libraries:
```bash
pip install numpy
pip install paho-mqtt
pip install ssl
````

## EF credentials

First you need the MQTT credentials of your Ecoflow App.
Visit the website https://energychain.github.io/site_ecoflow_mqtt_credentials/ and enter your e-mail and password from your Ecorflow account.

You should get back something like this:
- MQTT Protocoll:	mqtts
- MQTT Host:	mqtt-e.ecoflow.com
- MQTT Port:	8883
- MQTT User:	app-123456789abcdef123456
- MQTT Password:	fedcba987654321
- MQTT Client ID (sample):	ANDROID_12345678_987654321987654

Secondly, you need the MQTT cedential of the official Ecoflow API.
1. Visit the official Ecoflow developer website: https://developer-eu.ecoflow.com/us
2. Click on "Become a Developer". After a few days, your account gets unlocked. (I didn't get a notification, I just was able to log in after a while)
3. Follow the informations on https://developer-eu.ecoflow.com/us/document/generalInfo under section "MQTT certificate acquisition" to get the credentials.

You should get back something like this:
```json
{
    "code":"0",
    "message":"Success",
    "data":{
        "certificateAccount":"open-57c134518b5***",
        "certificatePassword":"959253cc103a4008***",
        "url":"mqtt.ecoflow.com",
        "port":"8883",
        "protocol":"mqtts"
    }
}
````
## Setup and Configuration

#### App Settings:
The maximum AC output power and Backup SoC shall be set in the app. Acually, setting the backup SoC is one of the few parameters you can set via the official API. However, if you always keep it at the same value, you can set it once in the app.
The mode shall be set to self powered.

#### Script Settings:
Fill in your credentials from App, API and your e-meter:
```bash
# ========= CONFIG =========

# e-meter MQTT
EMETER_HOST = "localhost"
EMETER_PORT = 1883
EMETER_TOPIC = "your/emeter/topic"

# EcoFlow App MQTT
ECOFLOW_HOST = "mqtt-e.ecoflow.com"
ECOFLOW_PORT = 8883
ECOFLOW_CID = "ANDROID_123_yyyyyyyyyyyyyyyy" # App MQTT Client ID:	ANDROID_123_yyyyyyyyyyyyyyyy
ECOFLOW_UID  = "yyyyyyyyyyyyyyyy" 
ECOFLOW_SN   = "BKxxxxxxxxxxxx" # Serial Number of your stream device

ECOFLOW_TOPIC = f"/app/{ECOFLOW_UID}/{ECOFLOW_SN}/thing/property/set"

ECOFLOW_USER = "app-zzzzzzzzzzzzzzzzzzzzzzz" # App MQTT User: app-zzzzzzzzzzzzzzzzzzzzzzz
ECOFLOW_PASS = "your_app_password" # App MQTT Password

# EcoFlow API MQTT
ECOFLOW_API_USER = "open-aaaaaaaaaaaaaaaaaaaaa" # API MQTT User: open-aaaaaaaaaaaaaaaaaaaaa
ECOFLOW_API_PASS = "your_api_password" # API MQTT Password

ECOFLOW_TOPIC_STATE = f"/open/{ECOFLOW_API_USER}/{ECOFLOW_SN}/quota"
```

## Run Script
```bash
python stream_e-meter_control.py
````
You can also run it in a venv or container.

## Further Description

#### Payload
I have identified two different payloads which can be used to adapt the AC output power. Both seem to work (at least for my Stream device). Currently, only the first one is used, the other one is uncommented:
```bash
if (power != power_old) or (gridConnectionPower < power-20) or (gridConnectionPower > power+20):
            #eco_app.publish(ECOFLOW_TOPIC, payload=payload2_bytes, qos=0)
            eco_app.publish(ECOFLOW_TOPIC, payload=payload1_bytes, qos=0)
````

#### Moving Average Filter
I observed large oscillations on the AC out power without a filter. You can adapt the filter depth to your needs by changing
```bash
BUFFER_SIZE = 15 # depth of the moving average buffer
````

#### Power Offset
Since the e-meter power and AC output power fluctuates all the time about +-50W, it might make sense to add a positive power offset to avoid to feed in power to grid. By default the power offset is set to 50W. Hence, if the e-meter power (overall power) is 300W, the AC output power is set to 250W. You can change it here:
```bash
EMETER_POWER_OFFSET = 50 # defines the positive nominal power offset
````

#### Load jumps
When the load jumps from a high value to a low value, the filtered power does not follow the load jump directly. To prevent feed-in to grid, the AC output power is set to zero and the filter is reset.

#### Near Backup SOC behavior
Since the last FW update the Stream device acts quite weird when SoC equals Backup SoC. That's why the AC output power is set to zero when the SoC is only 1% higher than Backup SoC. Furthermore, when SoC is 2% higher than Backup SoC, the AC output power is set to the PV power. Hence, the batterie isn't charged or discharged.  

## License

MIT License

Copyright (c) 2026 flamemk1

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Disclaimer

This open-source software is not affiliated with or endorsed by the company Ecoflow in any way.
Use of the software is at your own risk and discretion, and I assume no liability for any potential
damages or issues that may arise from using the software. It is important to be aware that using
this open-source software comes without direct support or guarantees from the company Ecoflow.

import json
import ssl
import struct
import paho.mqtt.client as mqtt
import numpy as np

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

# ========= PROTOBUF TEMPLATE =========
# This is a REAL binary frame captured from the app
# with feedGridModePowLimit = 0
#
# We'll overwrite only the float32 value
PROTO_TEMPLATE1 = bytearray.fromhex(
    "0a300a050d00000000102018022001280140fe01481a5005580170b3ceffb3017838800103880101ba0107416e64726f6964"
)

# We'll overwrite only the int16 value
PROTO_TEMPLATE2 = bytearray.fromhex(
    "0a350a0a30b2a083cc06c80a0000102018022001280140fe014811500a58017081b0ce8a017838800103880101ba0107416e64726f6964"
)

# Byte offset of the float32 power value
TEMPLATE_OFFSET1 = 5  # <-- adjust if your capture differs
# Byte offset of the int16 power value
TEMPLATE_OFFSET2 = 12  # <-- adjust if your capture differs

BUFFER_SIZE = 15 # depth of the moving average buffer
MAX_POWER = 1200 # maximum AC output power of the stream device
DEFAULT_EMETER_POWER_OFFSET = 50 # defines the positive nominal power offset

eMeterPowerOffset = DEFAULT_EMETER_POWER_OFFSET
gridConnectionPower = 0.0
powChargeDischargeBat = 0.0
soc = 0
backupReverseSoc = 23
PVpower1 = 0.0
PVpower2 = 0.0
PVpower3 = 0.0
PVpower4 = 0.0
power_avg = np.zeros(BUFFER_SIZE)
i_avg = 0
power_old = 0.0

# ========= App Connection =========
def on_app_connect(client, userdata, flags, reason_code, properties):
    print(f"[MQTT App] Connected: {reason_code}")


def on_app_disconnect(client, userdata, reason_code, properties):
    print(f"[MQTT App] Disconnected: {reason_code}")
    
# ========= EF STATE CALLBACK =========
def on_ef_state_connect(client, userdata, flags, reason_code, properties):
    print(f"[MQTT API] Connected: {reason_code}")
    
    # MUST be here so it runs after every reconnect
    client.subscribe(ECOFLOW_TOPIC_STATE)

def on_ef_state_disconnect(client, userdata, reason_code, properties):
    print(f"[MQTT API] Disconnected: {reason_code}")

def on_ef_state_message(client, userdata, msg):
    global gridConnectionPower
    global powChargeDischargeBat
    global soc
    global backupReverseSoc
    global PVpower1
    global PVpower2
    global PVpower3
    global PVpower4

    try:
        # grid power
        data = json.loads(msg.payload.decode())
        gridConnectionPower =  float(data["gridConnectionPower"])        
        print(f"gridConnectionPower {gridConnectionPower:.1f} W")
    except Exception as e:
        pass
        
    try:
        print("Error:", e, gridConnectionPower)
        # battery charge/discharge
        powChargeDischargeBat = int(data["powGetBpCms"]) # positive = charging; negative = discharging        
        print(f"Battery Charge/Discharge Power: {powChargeDischargeBat} W")
    except Exception as e:
        pass
        
    try:
        # SOC
        soc = int(data["soc"]) # int SOC        
        print(f"SoC: {soc} %")
    except Exception as e:
        pass
        
    try:
        # Backup Reserve SoC
        backupReverseSoc = int(data["backupReverseSoc"]) # int backup        
        print(f"Backup Reserve SoC: {backupReverseSoc} %")
    except Exception as e:
        pass
        
    try:
        # PV power
        PVpower1 = int(data["powGetPv1"])    
        print(f"PV power1: {PVpower1} W")
    except Exception as e:
        pass
        
    try:
        PVpower2 = int(data["powGetPv2"])   
        print(f"PV power2: {PVpower2} W")
    except Exception as e:
        pass
        
    try:
        PVpower4 = int(data["powGetPv4"])   
        print(f"PV power4: {PVpower4} W")
    except Exception as e:
        pass
        
    try:
        PVpower3 = int(data["powGetPv3"])    
        print(f"PV power3: {PVpower3} W")
    except Exception as e:
        pass

# ========= ECOFLOW CLIENT =========
# App
eco_app = mqtt.Client(
    client_id=ECOFLOW_CID,
    protocol=mqtt.MQTTv311,
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)
eco_app.username_pw_set(ECOFLOW_USER, ECOFLOW_PASS)

eco_app.tls_set(
    cert_reqs=ssl.CERT_REQUIRED,
    tls_version=ssl.PROTOCOL_TLS_CLIENT
)
eco_app.on_connect = on_app_connect
eco_app.on_disconnect = on_app_disconnect
eco_app.reconnect_delay_set(min_delay=1, max_delay=120)
eco_app.connect(ECOFLOW_HOST, ECOFLOW_PORT, keepalive=30)
eco_app.loop_start()

# API
eco_api = mqtt.Client(
    client_id="Ecoflow_api",
    protocol=mqtt.MQTTv311,
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)
eco_api.username_pw_set(ECOFLOW_API_USER, ECOFLOW_API_PASS)

eco_api.tls_set(
    cert_reqs=ssl.CERT_REQUIRED,
    tls_version=ssl.PROTOCOL_TLS_CLIENT
)
eco_api.on_connect = on_ef_state_connect
eco_api.on_disconnect = on_ef_state_disconnect
eco_api.on_message = on_ef_state_message
eco_api.reconnect_delay_set(min_delay=1, max_delay=120)
eco_api.connect(ECOFLOW_HOST, ECOFLOW_PORT, keepalive=30)
eco_api.loop_start()

# ========= EMETER CALLBACK =========
def on_emeter_connect(client, userdata, flags, reason_code, properties):
    print(f"[MQTT EMETER] Connected: {reason_code}")
    
    # MUST be here so it runs after every reconnect
    client.subscribe(EMETER_TOPIC)

def on_emeter_disconnect(client, userdata, reason_code, properties):
    print(f"[MQTT EMETER] Disconnected: {reason_code}")

def on_emeter_message(client, userdata, msg):
    global power_avg
    global i_avg
    global power_old
    try:
        # E-Meter power
        data = json.loads(msg.payload.decode())
        emeter_power = float(data["eHZ"]["Power"])
        
        # Overall PV power
        PVpower = PVpower1 + PVpower2 + PVpower3 + PVpower4
        
        # Power Offset
        if backupReverseSoc < 20 and PVpower > power_old:
            if soc < 30:
                eMeterPowerOffset = 20
            else:
                eMeterPowerOffset = 0
        else:
            eMeterPowerOffset = DEFAULT_EMETER_POWER_OFFSET
        
        # filtered emeter power
        power_avg[i_avg] = emeter_power + gridConnectionPower - eMeterPowerOffset
        i_avg += 1
        if i_avg > BUFFER_SIZE-1:
            i_avg = 0
        power_filtered = sum(power_avg)/BUFFER_SIZE
                
        # assign filtered or actual e-meter power
        delta_power = power_filtered - (emeter_power + gridConnectionPower - eMeterPowerOffset)
        
        if delta_power > 50:
            power_avg = np.ones(BUFFER_SIZE)*emeter_power
            power = emeter_power + gridConnectionPower - 150
            power_avg = np.ones(BUFFER_SIZE)*power
        elif delta_power < -200:
              power = emeter_power + gridConnectionPower - eMeterPowerOffset
              power_avg = np.ones(BUFFER_SIZE)*power
        else:
            power = power_filtered
        
        # Limit power to min/max 
        power = max(0, min(power, MAX_POWER))
               
        # SoC near Backup SoC       
        if ((soc-2) <= backupReverseSoc): # if SoC is 2% over Backup SoC, limit discharge to current PV power
            if power > PVpower:
                power = PVpower
        if (soc-1) <= backupReverseSoc: # if SoC is 1% over Backup SoC, set power to zero
            power = 0.0
            
        # avoid "grid off" condition
        if power > PVpower and power > 400:
            delta_target_actual = power_old - gridConnectionPower
            if delta_target_actual > 12:
                power = power_old
            else:
                if power_old < 320:
                    power = power_old + 100
                else:
                    power = power_old + 30
            
        power_int = int(round(power))        
        
        # encoding int16/hex for Stream Pro
        zigzag = power_int # << 1
        b0 = (zigzag & 0x7F) | 0x80
        b1 = zigzag >> 7
        encoded = (b1 << 8) | b0

        home_demand = PROTO_TEMPLATE1.copy()
        feedGridModePowLimit = PROTO_TEMPLATE2.copy()

        # Write float32 (little endian)
        home_demand[TEMPLATE_OFFSET1:TEMPLATE_OFFSET1+4] = struct.pack("<f", power)
        # Write int16 (little endian)
        feedGridModePowLimit[TEMPLATE_OFFSET2:TEMPLATE_OFFSET2+2] = struct.pack("<h", encoded)
        
        payload1_bytes = bytes(home_demand)
        payload2_bytes = bytes(feedGridModePowLimit)
        
        if (power != power_old) or (gridConnectionPower < power-20) or (gridConnectionPower > power+20):
            #eco_app.publish(ECOFLOW_TOPIC, payload=payload2_bytes, qos=0)
            eco_app.publish(ECOFLOW_TOPIC, payload=payload1_bytes, qos=0)
        
        power_old = power
        
        print(f"Filtered Power: {power_filtered:.1f} W; actual e-Meter Power: {emeter_power:.1f} W; delta power {delta_power:.1f} W; offset power: {eMeterPowerOffset:.1f} W; gridConnectionPower: {gridConnectionPower:.1f} W; Sent: {power_int} W")

    except Exception as e:
        print("Error:", e, gridConnectionPower)

# ========= EMETER CLIENT =========

em = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
em.on_connect = on_emeter_connect
em.on_disconnect = on_emeter_disconnect
em.on_message = on_emeter_message

em.reconnect_delay_set(min_delay=1, max_delay=120)
em.connect(EMETER_HOST, EMETER_PORT, keepalive=30)
em.loop_forever()

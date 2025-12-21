# Concept2 PM5 – Home Assistant Integration

This integration connects **Concept2 PM5 monitors** (RowErg) to **Home Assistant** over Bluetooth using the official Concept2 protocol.

---

## Features

- Automatic Bluetooth discovery of PM5 monitors
- Live workout metrics (elapsed time, distance, pace, stroke rate, power, heart rate, etc.)
- End-of-workout summaries (splits, averages, calories, drag factor)
- PM5 clock is synchronized to Home Assistant with an accuracy of +/- 30 seconds
- Automatic idle detection and safe workout termination
- Works with **ESPHome Bluetooth Proxy**

---

## Requirements

- Concept2 **PM5** monitor
- Bluetooth support via:
  - ESPHome Bluetooth Proxy **(recommended)**, or
  - Local Bluetooth adapter

---

## Enabling Bluetooth on the PM5

Before Home Assistant can detect the PM5:

1. On the PM5, press **Menu**
2. Select **Connect**
3. Leave the PM5 on the **Connect** screen

> The PM5 only advertises for app connections when this screen is active.

---

## Setup

### Automatic Discovery (Recommended)

1. Enable the PM5 **app connection** (see above)
2. Open **Home Assistant**
3. Navigate to:
   - **Settings → Devices & Services**
4. Select **Add** under **Concept2 PM5**

### Manual Setup

If the device is not discovered automatically:

1. Go to **Settings → Devices & Services → Add Integration**
2. Select **Concept2 PM5**
3. Enter the **Bluetooth MAC address** of the PM5

> 💡 You can find the MAC address on the PM5 under *More Options → Utilities → Product ID*, or via Bluetooth scanning tools.

---

## Recommended Usage Practices

### Ending Workouts Properly

For the **most accurate end-of-workout data**:

**Press the `Menu` button on the PM5 to end workouts manually**

This ensures:
- End-of-workout summary messages are fully emitted
- Final splits are logged
- Accurate calories, averages, and stroke data

### Battery Conservation

The PM5 runs on batteries and Bluetooth connections will keep the device awake.

After finishing your session, it's best to manually disable the App Connection on the PM5.
- Press **Menu**
- Select **Connect**
- Select **Disconnect app**

---

## Automatic Idle Handling

If a workout is left running and the machine becomes idle:

- The integration detects prolonged inactivity
- It *attempts* to safely terminate the workout
- A short grace period allows final workout summaries to be received
- The integration disconnects long enough for the PM5 to enter sleep


**Important:** While waiting for the PM5 to sleep, new Bluetooth connections are intentionally blocked.

---

## Known Limitations

- Only **one active Bluetooth connection** to the PM5 is supported at a time

---

## Disclaimer

This integration is not affiliated with or endorsed by Concept2. Use at your own risk.


# ======================
# HA constants
# ======================

DOMAIN = "c2_pm5"

PLATFORMS = ["sensor"]

CONF_ADDRESS = "address"
CONF_DEVICE_TYPE = "device_type"

# User-selectable device types
DEVICE_TYPE_ROWERG = "RowErg"
DEVICE_TYPES = [DEVICE_TYPE_ROWERG]

# ======================
# PM5 BLE + CSAFE control
# ======================

# Device availability / reconnect behavior
DEVICE_STALE_SECONDS = 30
IDLE_DISCONNECT_SECONDS = 15 * 60  # 15 minutes
IDLE_DISCONNECT_COOLDOWN_SECONDS = 90

# GATT characteristics
BASE_UUID_FMT = "ce06{short:04x}-43e5-11e4-916c-0800200c9a66"
CHAR_CSAFE_RX = 0x0021
CHAR_CSAFE_TX = 0x0022
CHAR_0031 = 0x0031
CHAR_0032 = 0x0032
CHAR_0033 = 0x0033
CHAR_0039 = 0x0039
CHAR_003A = 0x003A

# ---- CSAFE framing bytes ----
CSAFE_EXT_START = 0xF0
CSAFE_STD_START = 0xF1
CSAFE_STOP = 0xF2
CSAFE_STUFF = 0xF3

# CSAFE commands
CSAFE_COMMAND_WRAPPER = 0x76
CSAFE_PM_SET_DATETIME = 0x22
TERMINATE_WORKOUT_CONTENTS = bytes(
    [CSAFE_COMMAND_WRAPPER, 0x04, 0x13, 0x02, 0x01, 0x02]
)
GET_DATETIME_CONTENTS = bytes([CSAFE_COMMAND_WRAPPER, 0x01, 0x85])

# Guardrails
TERMINATE_RATE_LIMIT_SECONDS = 15.0
TERMINATE_GRACE_SECONDS = 10.0  # allow 0039/003A to come in before disconnect

# Date/time sync guardrails
DATETIME_SYNC_RATE_LIMIT_SECONDS = 6 * 60 * 60  # once per 6 hours
DATETIME_SYNC_CONNECT_GRACE_SECONDS = 1.0  # let notifications settle
DATETIME_SYNC_TIMEOUT_SECONDS = 5.0

# ---- Enum mappings (Appendix A) ----
WORKOUT_TYPE = {
    0: "JustRow (no splits)",
    1: "JustRow (splits)",
    2: "Fixed distance (no splits)",
    3: "Fixed distance (splits)",
    4: "Fixed time (no splits)",
    5: "Fixed time (splits)",
    6: "Fixed time interval",
    7: "Fixed distance interval",
    8: "Variable interval",
    9: "Variable interval (undefined rest)",
    10: "Fixed calorie (splits)",
    11: "Fixed watt-minute (splits)",
    12: "Fixed calorie interval",
}

INTERVAL_TYPE = {
    0: "Time",
    1: "Distance",
    2: "Rest",
    3: "Time + undefined rest",
    4: "Distance + undefined rest",
    5: "Undefined rest",
    6: "Calorie",
    7: "Calorie + undefined rest",
    8: "Watt-minute",
    9: "Watt-minute + undefined rest",
    255: "None",
}

WORKOUT_STATE = {
    0: "Wait to begin",
    1: "Workout row",
    2: "Countdown pause",
    3: "Interval rest",
    4: "Interval work (time)",
    5: "Interval work (distance)",
    6: "Interval rest → work (time)",
    7: "Interval rest → work (distance)",
    8: "Interval work (time) → rest",
    9: "Interval work (distance) → rest",
    10: "Workout end",
    11: "Terminate",
    12: "Logged",
    13: "Rearm",
}

ROWING_STATE = {0: "Inactive", 1: "Active"}

STROKE_STATE = {
    0: "Waiting for flywheel to reach min speed",
    1: "Waiting for flywheel to accelerate",
    2: "Driving",
    3: "Dwelling after drive",
    4: "Recovery",
}

# Erg machine type (Appendix A)
ERG_MACHINE_TYPE = {
    0: "Model D (static)",
    1: "Model C (static)",
    2: "Model A (static)",
    3: "Model B (static)",
    5: "Model E (static)",
    7: "Rower simulator",
    8: "Dynamic (static?)",
    16: "Model A (slides)",
    17: "Model B (slides)",
    18: "Model C (slides)",
    19: "Model D (slides)",
    20: "Model E (slides)",
    32: "Dynamic (linked)",
    64: "Dynamometer (static)",
    128: "SkiErg (static)",
    143: "Ski simulator (static)",
    192: "BikeErg (no arms)",
    193: "BikeErg (arms)",
    194: "BikeErg (no arms?)",
    207: "Bike simulator",
    224: "MultiErg row",
    225: "MultiErg ski",
    226: "MultiErg bike",
}

WORKOUT_DURATION_TYPE = {
    0: "Time",
    64: "Calories",
    128: "Distance",
    192: "Watt-minute",
}

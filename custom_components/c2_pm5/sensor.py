from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorEntityDescription,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfEnergy,
    UnitOfLength,
    UnitOfPower,
    UnitOfSpeed,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    HRM_DEVICE_TYPE,
    INTERVAL_TYPE,
    ROWING_STATE,
    STROKE_STATE,
    WORKOUT_DURATION_TYPE,
    WORKOUT_STATE,
    WORKOUT_TYPE,
)
from . import PM5Coordinator
from .pm5_ble import PM5Data


@dataclass(frozen=True, kw_only=True)
class PM5SensorDescription(SensorEntityDescription):
    key: str
    always_available: bool | None = None
    restore: bool = False


SENSORS: list[PM5SensorDescription] = [
    # ---------- 0x0031 : General status ----------
    PM5SensorDescription(
        key="0031_elapsed_time_s",
        name="Elapsed Time",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:timer-outline",
    ),
    PM5SensorDescription(
        key="0031_distance_m",
        name="Distance",
        native_unit_of_measurement=UnitOfLength.METERS,
        suggested_unit_of_measurement=UnitOfLength.FEET,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:map-marker-distance",
    ),
    PM5SensorDescription(
        key="0031_workout_type",
        name="Workout Type",
        device_class=SensorDeviceClass.ENUM,
        options=list(WORKOUT_TYPE.values()),
        icon="mdi:clipboard-text-outline",
    ),
    PM5SensorDescription(
        key="0031_interval_type",
        name="Interval Type",
        device_class=SensorDeviceClass.ENUM,
        options=list(INTERVAL_TYPE.values()),
        icon="mdi:timeline-clock-outline",
    ),
    PM5SensorDescription(
        key="0031_workout_state",
        name="Workout State",
        device_class=SensorDeviceClass.ENUM,
        options=list(WORKOUT_STATE.values()),
        icon="mdi:state-machine",
    ),
    PM5SensorDescription(
        key="0031_rowing_state",
        name="Rowing State",
        device_class=SensorDeviceClass.ENUM,
        options=list(ROWING_STATE.values()),
        icon="mdi:rowing",
    ),
    PM5SensorDescription(
        key="0031_stroke_state",
        name="Stroke State",
        device_class=SensorDeviceClass.ENUM,
        options=list(STROKE_STATE.values()),
        icon="mdi:waveform",
    ),
    PM5SensorDescription(
        key="0031_total_work_distance_m",
        name="Total Work Distance",
        native_unit_of_measurement=UnitOfLength.METERS,
        suggested_unit_of_measurement=UnitOfLength.FEET,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:map-marker-distance",
    ),
    PM5SensorDescription(
        key="0031_workout_duration",
        name="Workout Duration",
        icon="mdi:ruler",
    ),
    PM5SensorDescription(
        key="0031_workout_duration_type",
        name="Workout Duration Type",
        device_class=SensorDeviceClass.ENUM,
        options=list(WORKOUT_DURATION_TYPE.values()),
        icon="mdi:timeline-clock-outline",
    ),
    PM5SensorDescription(
        key="0031_drag_factor",
        name="Drag Factor",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:fan",
    ),
    # ---------- 0x0032 : Performance / live metrics ----------
    PM5SensorDescription(
        key="0032_speed_m_s",
        name="Speed",
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        suggested_unit_of_measurement=UnitOfSpeed.MILES_PER_HOUR,
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:speedometer",
    ),
    PM5SensorDescription(
        key="0032_stroke_rate_spm",
        name="Stroke Rate",
        native_unit_of_measurement="spm",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:sync",
    ),
    PM5SensorDescription(
        key="0032_heart_rate_bpm",
        name="Heart Rate",
        native_unit_of_measurement="bpm",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:heart-pulse",
    ),
    PM5SensorDescription(
        key="0032_current_pace_s_per_500m",
        name="Current Pace per 500m",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:run-fast",
    ),
    PM5SensorDescription(
        key="0032_average_pace_s_per_500m",
        name="Average Pace per 500m",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:run",
    ),
    PM5SensorDescription(
        key="0032_rest_distance_m",
        name="Rest Distance",
        native_unit_of_measurement=UnitOfLength.METERS,
        suggested_unit_of_measurement=UnitOfLength.FEET,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:map-marker-off-outline",
    ),
    PM5SensorDescription(
        key="0032_rest_time_s",
        name="Rest Time",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:timer-sand",
    ),
    # ---------- 0x0033 : Power / intervals ----------
    PM5SensorDescription(
        key="0033_interval_count",
        name="Interval Count",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:counter",
    ),
    PM5SensorDescription(
        key="0033_average_power_w",
        name="Average Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:flash",
    ),
    PM5SensorDescription(
        key="0033_total_calories",
        name="Total Calories",
        native_unit_of_measurement=UnitOfEnergy.CALORIE,
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:fire",
    ),
    PM5SensorDescription(
        key="0033_split_interval_avg_pace_s_per_500m",
        name="Split/Interval Avg Pace per 500m",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:run",
    ),
    PM5SensorDescription(
        key="0033_split_interval_avg_power_w",
        name="Split/Interval Avg Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:flash",
    ),
    PM5SensorDescription(
        key="0033_split_interval_avg_calories",
        name="Split/Interval Avg Calories",
        native_unit_of_measurement=UnitOfEnergy.CALORIE,
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:fire",
    ),
    # ---------- 0x0035 : Stroke data ----------
    PM5SensorDescription(
        key="0035_drive_length_m",
        name="Drive Length",
        native_unit_of_measurement=UnitOfLength.METERS,
        suggested_unit_of_measurement=UnitOfLength.FEET,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:arrow-expand-horizontal",
    ),
    PM5SensorDescription(
        key="0035_drive_time_s",
        name="Drive Time",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:timer",
    ),
    PM5SensorDescription(
        key="0035_stroke_recovery_time_s",
        name="Recovery Time",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:timer-sand",
    ),
    PM5SensorDescription(
        key="0035_stroke_distance_m",
        name="Stroke Distance",
        native_unit_of_measurement=UnitOfLength.METERS,
        suggested_unit_of_measurement=UnitOfLength.FEET,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:arrow-expand-horizontal",
    ),
    PM5SensorDescription(
        key="0035_peak_drive_force",
        name="Peak Drive Force",
        native_unit_of_measurement="lbf",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:weight-lifter",
    ),
    PM5SensorDescription(
        key="0035_average_drive_force",
        name="Average Drive Force",
        native_unit_of_measurement="lbf",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:weight",
    ),
    PM5SensorDescription(
        key="0035_work_per_stroke_j",
        name="Work per Stroke",
        native_unit_of_measurement=UnitOfEnergy.JOULE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:lightning-bolt",
    ),
    PM5SensorDescription(
        key="0035_stroke_count",
        name="Stroke Count",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:counter",
    ),
    # ---------- 0x0036 : Stroke data ----------
    PM5SensorDescription(
        key="0036_stroke_power_w",
        name="Stroke Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:flash",
    ),
    PM5SensorDescription(
        key="0036_stroke_calories_hr",
        name="Stroke Calories/hr",
        native_unit_of_measurement=UnitOfEnergy.CALORIE,
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:fire",
    ),
    PM5SensorDescription(
        key="0036_projected_work_time_s",
        name="Projected Work Time",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:clock-outline",
    ),
    PM5SensorDescription(
        key="0036_projected_work_distance_m",
        name="Projected Work Distance",
        native_unit_of_measurement=UnitOfLength.METERS,
        suggested_unit_of_measurement=UnitOfLength.FEET,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:map-marker-distance",
    ),
    # ---------- 0x0037 : Split/interval data ----------
    PM5SensorDescription(
        key="0037_split_interval_time_s",
        name="Last Split/Interval Time",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:clock-outline",
    ),
    PM5SensorDescription(
        key="0037_split_interval_distance_m",
        name="Last Split/Interval Distance",
        native_unit_of_measurement=UnitOfLength.METERS,
        suggested_unit_of_measurement=UnitOfLength.FEET,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:map-marker-path",
    ),
    PM5SensorDescription(
        key="0037_interval_rest_time_s",
        name="Last Interval Rest Time",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:timer-sand",
    ),
    PM5SensorDescription(
        key="0037_interval_rest_distance_m",
        name="Last Interval Rest Distance",
        native_unit_of_measurement=UnitOfLength.METERS,
        suggested_unit_of_measurement=UnitOfLength.FEET,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:map-marker-off-outline",
    ),
    PM5SensorDescription(
        key="0037_split_interval_type",
        name="Last Split/Interval Type",
        device_class=SensorDeviceClass.ENUM,
        options=list(INTERVAL_TYPE.values()),
        icon="mdi:timeline-clock-outline",
    ),
    PM5SensorDescription(
        key="0037_split_interval_number",
        name="Last Split/Interval Number",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:counter",
    ),
    # ---------- 0x0038 : Split/interval data ----------
    PM5SensorDescription(
        key="0038_split_interval_avg_stroke_rate_spm",
        name="Last Split/Interval Avg Stroke Rate",
        native_unit_of_measurement="spm",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:sync",
    ),
    PM5SensorDescription(
        key="0038_split_interval_work_heart_rate_bpm",
        name="Last Split/Interval Work Heart Rate",
        native_unit_of_measurement="bpm",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:heart-pulse",
    ),
    PM5SensorDescription(
        key="0038_split_interval_rest_heart_rate_bpm",
        name="Last Split/Interval Rest Heart Rate",
        native_unit_of_measurement="bpm",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:heart-pulse",
    ),
    PM5SensorDescription(
        key="0038_split_interval_avg_pace_s_per_500m",
        name="Last Split/Interval Avg Pace per 500m",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:run",
    ),
    PM5SensorDescription(
        key="0038_split_interval_total_calories",
        name="Last Split/Interval Total Calories",
        native_unit_of_measurement=UnitOfEnergy.CALORIE,
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:fire",
    ),
    PM5SensorDescription(
        key="0038_split_interval_avg_calories_hr",
        name="Last Split/Interval Avg Calories/hr",
        native_unit_of_measurement=UnitOfEnergy.CALORIE,
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:fire",
    ),
    PM5SensorDescription(
        key="0038_split_interval_speed_m_s",
        name="Last Split/Interval Speed",
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        suggested_unit_of_measurement=UnitOfSpeed.MILES_PER_HOUR,
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:speedometer",
    ),
    PM5SensorDescription(
        key="0038_split_interval_power_w",
        name="Last Split/Interval Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:flash",
    ),
    PM5SensorDescription(
        key="0038_split_avg_drag_factor",
        name="Last Split Avg Drag Factor",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:fan",
    ),
    # ---------- 0x0039 : End-of-workout summary ----------
    PM5SensorDescription(
        key="0039_elapsed_time_s",
        name="EOW Elapsed Time",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:timer-outline",
    ),
    PM5SensorDescription(
        key="0039_distance_m",
        name="EOW Distance",
        native_unit_of_measurement=UnitOfLength.METERS,
        suggested_unit_of_measurement=UnitOfLength.FEET,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:map-marker-distance",
    ),
    PM5SensorDescription(
        key="0039_avg_stroke_rate_spm",
        name="EOW Avg Stroke Rate",
        native_unit_of_measurement="spm",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:sync",
    ),
    PM5SensorDescription(
        key="0039_ending_heart_rate_bpm",
        name="EOW Ending Heart Rate",
        native_unit_of_measurement="bpm",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:heart-pulse",
    ),
    PM5SensorDescription(
        key="0039_drag_factor_avg",
        name="EOW Avg Drag Factor",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:fan",
    ),
    PM5SensorDescription(
        key="0039_workout_type",
        name="EOW Workout Type",
        device_class=SensorDeviceClass.ENUM,
        options=list(WORKOUT_TYPE.values()),
        icon="mdi:clipboard-text-outline",
    ),
    PM5SensorDescription(
        key="0039_avg_pace_s_per_500m",
        name="EOW Avg Pace per 500m",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:run",
    ),
    # ---------- 0x003A : End-of-workout additional summary ----------
    PM5SensorDescription(
        key="003a_split_interval_type",
        name="EOW Interval Type",
        device_class=SensorDeviceClass.ENUM,
        options=list(INTERVAL_TYPE.values()),
        icon="mdi:timeline-clock-outline",
    ),
    PM5SensorDescription(
        key="003a_split_interval_size",
        name="EOW Interval Size",
        icon="mdi:ruler",
    ),
    PM5SensorDescription(
        key="003a_split_interval_count",
        name="EOW Interval Count",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:counter",
    ),
    PM5SensorDescription(
        key="003a_total_calories",
        name="EOW Total Calories",
        native_unit_of_measurement=UnitOfEnergy.CALORIE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:fire",
    ),
    PM5SensorDescription(
        key="003a_avg_power_w",
        name="EOW Avg Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:flash",
    ),
    PM5SensorDescription(
        key="003a_total_rest_distance_m",
        name="EOW Total Rest Distance",
        native_unit_of_measurement=UnitOfLength.METERS,
        suggested_unit_of_measurement=UnitOfLength.FEET,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:map-marker-off-outline",
    ),
    PM5SensorDescription(
        key="003a_interval_rest_time_s",
        name="EOW Interval Rest Time",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:timer-sand",
    ),
    PM5SensorDescription(
        key="003a_avg_calories_per_hr",
        name="EOW Avg Calories/hr",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:fire-circle",
    ),
    # ---------- Heart rate belt information ----------
    PM5SensorDescription(
        key="hrm_manufacturer_id",
        name="Heart Rate Monitor Manufacturer ID",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:factory",
    ),
    PM5SensorDescription(
        key="hrm_device_type",
        name="Heart Rate Monitor Device Type",
        device_class=SensorDeviceClass.ENUM,
        options=list(HRM_DEVICE_TYPE.values()),
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:bluetooth",
    ),
    PM5SensorDescription(
        key="hrm_belt_id",
        name="Heart Rate Monitor Belt ID",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:network",
    ),
    # ---------- Battery ----------
    PM5SensorDescription(
        key="battery_level_percent",
        name="Battery Level",
        native_unit_of_measurement="%",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:battery",
        always_available=True,
        restore=True,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: PM5Coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [PM5Sensor(coordinator, d) for d in SENSORS], update_before_add=False
    )


class PM5Sensor(RestoreSensor):
    _attr_should_poll = False

    def __init__(
        self, coordinator: PM5Coordinator, description: PM5SensorDescription
    ) -> None:
        self.coordinator = coordinator
        self.entity_description = description
        self._attr_name = f"{coordinator.device_type} {description.name}"
        self._attr_unique_id = f"{coordinator.address}_{description.key}"

    @property
    def available(self) -> bool:
        if self.entity_description.always_available:
            # Always available while we have a value
            data = self.coordinator.data
            if data and data.values.get(self.entity_description.key) is not None:
                return True

        data = self.coordinator.data
        return bool(data and getattr(data, "available", False))

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data
        if not data:
            return None
        return data.values.get(self.entity_description.key)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.entity_description.restore:
            last_state = await self.async_get_last_sensor_data()
            if last_state:
                self.coordinator._handle_data(
                    PM5Data({self.entity_description.key: last_state.native_value})
                )

        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.address)},
            name=self.coordinator.device_type,
            manufacturer="Concept2",
            model="PM5",
        )

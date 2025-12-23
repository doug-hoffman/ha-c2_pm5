from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
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

from .const import DOMAIN
from . import PM5Coordinator


@dataclass(frozen=True, kw_only=True)
class PM5SensorDescription(SensorEntityDescription):
    key: str


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
        icon="mdi:clipboard-text-outline",
    ),
    PM5SensorDescription(
        key="0031_interval_type",
        name="Interval Type",
        icon="mdi:timeline-clock-outline",
    ),
    PM5SensorDescription(
        key="0031_workout_state",
        name="Workout State",
        icon="mdi:state-machine",
    ),
    PM5SensorDescription(
        key="0031_rowing_state",
        name="Rowing State",
        icon="mdi:rowing",
    ),
    PM5SensorDescription(
        key="0031_stroke_state",
        name="Stroke State",
        icon="mdi:waveform",
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
        name="Split Avg Pace per 500m",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:run",
    ),
    PM5SensorDescription(
        key="0033_split_interval_avg_power_w",
        name="Split Avg Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:flash",
    ),
    PM5SensorDescription(
        key="0033_split_interval_avg_calories",
        name="Split Avg Calories",
        native_unit_of_measurement=UnitOfEnergy.CALORIE,
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:fire",
    ),
    PM5SensorDescription(
        key="0033_last_split_time_s",
        name="Last Split Time",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:clock-outline",
    ),
    PM5SensorDescription(
        key="0033_last_split_distance_m",
        name="Last Split Distance",
        native_unit_of_measurement=UnitOfLength.METERS,
        suggested_unit_of_measurement=UnitOfLength.FEET,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:map-marker-path",
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
        key="0039_avg_heart_rate_bpm",
        name="EOW Avg Heart Rate",
        native_unit_of_measurement="bpm",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:heart-pulse",
    ),
    PM5SensorDescription(
        key="0039_min_heart_rate_bpm",
        name="EOW Min Heart Rate",
        native_unit_of_measurement="bpm",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:heart-minus",
    ),
    PM5SensorDescription(
        key="0039_max_heart_rate_bpm",
        name="EOW Max Heart Rate",
        native_unit_of_measurement="bpm",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:heart-plus",
    ),
    PM5SensorDescription(
        key="0039_drag_factor_avg",
        name="EOW Avg Drag Factor",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:fan",
    ),
    PM5SensorDescription(
        key="0039_recovery_heart_rate_bpm",
        name="EOW Recovery Heart Rate",
        native_unit_of_measurement="bpm",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:heart-off",
    ),
    PM5SensorDescription(
        key="0039_workout_type",
        name="EOW Workout Type",
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
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: PM5Coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [PM5Sensor(coordinator, d) for d in SENSORS], update_before_add=False
    )


class PM5Sensor(SensorEntity):
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
        data = self.coordinator.data
        return bool(data and getattr(data, "available", False))

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data
        if not data or not getattr(data, "available", False):
            return None
        return data.values.get(self.entity_description.key)

    async def async_added_to_hass(self) -> None:
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

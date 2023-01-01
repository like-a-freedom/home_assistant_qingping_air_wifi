import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    CONCENTRATION_PARTS_PER_MILLION,
    PERCENTAGE,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .api import QingpingApi
from .const import CONF_CLIENT_ID, CONF_CLIENT_SECRET

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_CLIENT_ID): cv.string,
        vol.Required(CONF_CLIENT_SECRET): cv.string,
    }
)

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="CO2",
        name="CO2",
        device_class=SensorDeviceClass.CO2,
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
        icon="mdi:molecule-co2",
    ),
    SensorEntityDescription(
        key="PM25",
        name="PM2.5",
        device_class=SensorDeviceClass.PM25,
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="PM10",
        name="PM10",
        device_class=SensorDeviceClass.PM10,
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="TVOC",
        name="tVOC",
        device_class=SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS,
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="HUMIDITY",
        name="Humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="TEMPERATURE",
        name="Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    _: DiscoveryInfoType or None = None,
) -> None:
    """Set up the sensor platform."""
    try:
        api_client = QingpingApi(config[CONF_CLIENT_ID], config[CONF_CLIENT_SECRET])
    except Exception as err:
        _LOGGER.error(err)
        return

    entities = [
        QingpingAirSensor(api_client, description) for description in SENSOR_TYPES
    ]
    add_entities(entities, True)


class QingpingAirSensor(SensorEntity):
    def __init__(
        self, api_client: QingpingApi, description: SensorEntityDescription
    ) -> None:
        self.api_client = api_client
        self.entity_description = description
        self._attr_name = description.name

    @property
    def unique_id(self) -> str:
        return f"qingping_air_wifi_{self._attr_name}"

    def update(self) -> None:
        try:
            self.data = self.api_client.get_devices()
        except Exception as err:
            _LOGGER.error(err)

        if self.data is None:
            _LOGGER.error(f"Qingping response is: {self.data}")
            return

        sensor_type = self.entity_description.key

        match sensor_type:
            case "PM25":
                self._attr_native_value = self.data["pm25"]
            case "PM10":
                self._attr_native_value = self.data["pm10"]
            case "CO2":
                self._attr_native_value = self.data["co2"]
            case "TVOC":
                self._attr_native_value = self.data["tvoc"]
            case "TEMPERATURE":
                self._attr_native_value = self.data["temperature"]
            case "HUMIDITY":
                self._attr_native_value = self.data["humidity"]

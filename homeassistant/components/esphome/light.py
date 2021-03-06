"""Support for ESPHome lights."""
import logging
from typing import Optional, List, Tuple, TYPE_CHECKING

from homeassistant.components.esphome import EsphomeEntity, \
    platform_async_setup_entry
from homeassistant.components.light import Light, SUPPORT_FLASH, \
    SUPPORT_BRIGHTNESS, SUPPORT_TRANSITION, SUPPORT_COLOR, \
    SUPPORT_WHITE_VALUE, SUPPORT_COLOR_TEMP, SUPPORT_EFFECT, ATTR_HS_COLOR, \
    ATTR_FLASH, ATTR_TRANSITION, ATTR_BRIGHTNESS, ATTR_COLOR_TEMP, \
    ATTR_EFFECT, ATTR_WHITE_VALUE, FLASH_SHORT, FLASH_LONG
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import HomeAssistantType
import homeassistant.util.color as color_util

if TYPE_CHECKING:
    # pylint: disable=unused-import
    from aioesphomeapi import LightInfo, LightState  # noqa

DEPENDENCIES = ['esphome']
_LOGGER = logging.getLogger(__name__)


FLASH_LENGTHS = {
    FLASH_SHORT: 2,
    FLASH_LONG: 10,
}


async def async_setup_entry(hass: HomeAssistantType,
                            entry: ConfigEntry, async_add_entities) -> None:
    """Set up ESPHome lights based on a config entry."""
    # pylint: disable=redefined-outer-name
    from aioesphomeapi import LightInfo, LightState  # noqa

    await platform_async_setup_entry(
        hass, entry, async_add_entities,
        component_key='light',
        info_type=LightInfo, entity_type=EsphomeLight,
        state_type=LightState
    )


class EsphomeLight(EsphomeEntity, Light):
    """A switch implementation for ESPHome."""

    @property
    def _static_info(self) -> 'LightInfo':
        return super()._static_info

    @property
    def _state(self) -> Optional['LightState']:
        return super()._state

    @property
    def is_on(self) -> Optional[bool]:
        """Return true if the switch is on."""
        if self._state is None:
            return None
        return self._state.state

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the entity on."""
        data = {'key': self._static_info.key, 'state': True}
        if ATTR_HS_COLOR in kwargs:
            hue, sat = kwargs[ATTR_HS_COLOR]
            red, green, blue = color_util.color_hsv_to_RGB(hue, sat, 100)
            data['rgb'] = (red / 255, green / 255, blue / 255)
        if ATTR_FLASH in kwargs:
            data['flash'] = FLASH_LENGTHS[kwargs[ATTR_FLASH]]
        if ATTR_TRANSITION in kwargs:
            data['transition_length'] = kwargs[ATTR_TRANSITION]
        if ATTR_BRIGHTNESS in kwargs:
            data['brightness'] = kwargs[ATTR_BRIGHTNESS] / 255
        if ATTR_COLOR_TEMP in kwargs:
            data['color_temperature'] = kwargs[ATTR_COLOR_TEMP]
        if ATTR_EFFECT in kwargs:
            data['effect'] = kwargs[ATTR_EFFECT]
        if ATTR_WHITE_VALUE in kwargs:
            data['white'] = kwargs[ATTR_WHITE_VALUE] / 255
        await self._client.light_command(**data)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the entity off."""
        data = {'key': self._static_info.key, 'state': False}
        if ATTR_FLASH in kwargs:
            data['flash'] = FLASH_LENGTHS[kwargs[ATTR_FLASH]]
        if ATTR_TRANSITION in kwargs:
            data['transition_length'] = kwargs[ATTR_TRANSITION]
        await self._client.light_command(**data)

    @property
    def brightness(self) -> Optional[int]:
        """Return the brightness of this light between 0..255."""
        if self._state is None:
            return None
        return round(self._state.brightness * 255)

    @property
    def hs_color(self) -> Optional[Tuple[float, float]]:
        """Return the hue and saturation color value [float, float]."""
        if self._state is None:
            return None
        return color_util.color_RGB_to_hs(
            self._state.red * 255,
            self._state.green * 255,
            self._state.blue * 255)

    @property
    def color_temp(self) -> Optional[float]:
        """Return the CT color value in mireds."""
        if self._state is None:
            return None
        return self._state.color_temperature

    @property
    def white_value(self) -> Optional[int]:
        """Return the white value of this light between 0..255."""
        if self._state is None:
            return None
        return round(self._state.white * 255)

    @property
    def effect(self) -> Optional[str]:
        """Return the current effect."""
        if self._state is None:
            return None
        return self._state.effect

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        flags = SUPPORT_FLASH
        if self._static_info.supports_brightness:
            flags |= SUPPORT_BRIGHTNESS
            flags |= SUPPORT_TRANSITION
        if self._static_info.supports_rgb:
            flags |= SUPPORT_COLOR
        if self._static_info.supports_white_value:
            flags |= SUPPORT_WHITE_VALUE
        if self._static_info.supports_color_temperature:
            flags |= SUPPORT_COLOR_TEMP
        if self._static_info.effects:
            flags |= SUPPORT_EFFECT
        return flags

    @property
    def effect_list(self) -> List[str]:
        """Return the list of supported effects."""
        return self._static_info.effects

    @property
    def min_mireds(self) -> float:
        """Return the coldest color_temp that this light supports."""
        return self._static_info.min_mireds

    @property
    def max_mireds(self) -> float:
        """Return the warmest color_temp that this light supports."""
        return self._static_info.max_mireds

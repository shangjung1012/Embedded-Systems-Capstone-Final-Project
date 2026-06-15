from __future__ import annotations

from dataclasses import dataclass
import os
import sys
from typing import Protocol

try:
    from gpiozero import OutputDevice as GpioZeroOutputDevice
except ImportError:
    GpioZeroOutputDevice = None  # type: ignore[assignment]


class OutputDeviceLike(Protocol):
    def on(self) -> None:
        pass

    def off(self) -> None:
        pass


@dataclass(frozen=True)
class GpioPin:
    name: str
    gpio: int
    physical_pin: int


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError as error:
        raise ValueError(f"{name} must be an integer GPIO BCM pin number") from error


class GpioPins:
    VIBRATION = GpioPin("vibration", gpio=_env_int("VIBRATION_PIN", 17), physical_pin=11)
    FAN_INA = GpioPin("fan_ina", gpio=_env_int("FAN_INA_PIN", 22), physical_pin=15)
    FAN_INB = GpioPin("fan_inb", gpio=_env_int("FAN_INB_PIN", 27), physical_pin=13)
    MIST = GpioPin("mist", gpio=_env_int("MIST_PIN", 23), physical_pin=16)


def configure_gpio_pins(
    *,
    vibration_pin: int | None = None,
    fan_ina_pin: int | None = None,
    fan_inb_pin: int | None = None,
    mist_pin: int | None = None,
) -> None:
    if vibration_pin is not None:
        GpioPins.VIBRATION = GpioPin("vibration", gpio=vibration_pin, physical_pin=11)
    if fan_ina_pin is not None:
        GpioPins.FAN_INA = GpioPin("fan_ina", gpio=fan_ina_pin, physical_pin=15)
    if fan_inb_pin is not None:
        GpioPins.FAN_INB = GpioPin("fan_inb", gpio=fan_inb_pin, physical_pin=13)
    if mist_pin is not None:
        GpioPins.MIST = GpioPin("mist", gpio=mist_pin, physical_pin=16)


class NullOutputDevice:
    def __init__(self, pin: GpioPin) -> None:
        self.pin = pin

    def on(self) -> None:
        pass

    def off(self) -> None:
        pass


_warned_pins: set[str] = set()


def create_output_device(pin: GpioPin, *, active_high: bool = True) -> OutputDeviceLike:
    if GpioZeroOutputDevice is None:
        return NullOutputDevice(pin)

    try:
        return GpioZeroOutputDevice(pin.gpio, active_high=active_high)
    except Exception as error:
        if pin.name not in _warned_pins:
            print(
                f"[gpio] {pin.name} GPIO{pin.gpio} unavailable, using no-op device: {error}",
                file=sys.stderr,
            )
            _warned_pins.add(pin.name)
        return NullOutputDevice(pin)


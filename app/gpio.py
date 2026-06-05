from __future__ import annotations

from dataclasses import dataclass
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


class GpioPins:
    VIBRATION = GpioPin("vibration", gpio=17, physical_pin=11)
    FAN_INA = GpioPin("fan_ina", gpio=22, physical_pin=15)
    FAN_INB = GpioPin("fan_inb", gpio=27, physical_pin=13)


class NullOutputDevice:
    def __init__(self, pin: GpioPin) -> None:
        self.pin = pin

    def on(self) -> None:
        pass

    def off(self) -> None:
        pass


_warned_pins: set[str] = set()


def create_output_device(pin: GpioPin) -> OutputDeviceLike:
    if GpioZeroOutputDevice is None:
        return NullOutputDevice(pin)

    try:
        return GpioZeroOutputDevice(pin.gpio)
    except Exception as error:
        if pin.name not in _warned_pins:
            print(
                f"[gpio] {pin.name} GPIO{pin.gpio} unavailable, using no-op device: {error}",
                file=sys.stderr,
            )
            _warned_pins.add(pin.name)
        return NullOutputDevice(pin)


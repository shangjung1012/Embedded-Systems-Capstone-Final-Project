from __future__ import annotations

import argparse
import os
import sys

from app.gpio import configure_gpio_pins
from app.manual_control import ManualControlSession


def main() -> int:
    parser = argparse.ArgumentParser(description="Interactively turn hardware modules on and off.")
    parser.add_argument(
        "--vibration-pin",
        type=int,
        help="BCM GPIO pin for the vibration module. Defaults to VIBRATION_PIN or 17.",
    )
    parser.add_argument(
        "--fan-ina-pin",
        type=int,
        help="BCM GPIO pin for the fan INA input. Defaults to FAN_INA_PIN or 22.",
    )
    parser.add_argument(
        "--fan-inb-pin",
        type=int,
        help="BCM GPIO pin for the fan INB input. Defaults to FAN_INB_PIN or 27.",
    )
    parser.add_argument(
        "--mist-pin",
        type=int,
        help="BCM GPIO pin for the mist module. Defaults to MIST_PIN or 23.",
    )
    args = parser.parse_args()

    if os.geteuid() != 0:
        print(
            "manual_control.py must be run as root for GPIO/LED hardware. "
            "Use: sudo uv run python manual_control.py",
            file=sys.stderr,
        )
        return 1

    configure_gpio_pins(
        vibration_pin=args.vibration_pin,
        fan_ina_pin=args.fan_ina_pin,
        fan_inb_pin=args.fan_inb_pin,
        mist_pin=args.mist_pin,
    )

    ManualControlSession().run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

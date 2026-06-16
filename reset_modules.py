from __future__ import annotations

import argparse
import os
import sys
import time

from app.effects import EffectController
from app.gpio import configure_gpio_pins


def main() -> int:
    parser = argparse.ArgumentParser(description="Reset all hardware modules to the off state.")
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
    parser.add_argument(
        "--repeat",
        type=int,
        default=2,
        help="How many times to send the all-off reset command. Defaults to 2.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.2,
        help="Delay in seconds between repeated reset commands. Defaults to 0.2.",
    )
    args = parser.parse_args()

    if os.geteuid() != 0:
        print(
            "reset_modules.py must be run as root for GPIO/LED hardware. "
            "Use: sudo uv run python reset_modules.py",
            file=sys.stderr,
        )
        return 1

    if args.repeat < 1:
        print("--repeat must be at least 1", file=sys.stderr)
        return 1
    if args.delay < 0:
        print("--delay must be 0 or greater", file=sys.stderr)
        return 1

    configure_gpio_pins(
        vibration_pin=args.vibration_pin,
        fan_ina_pin=args.fan_ina_pin,
        fan_inb_pin=args.fan_inb_pin,
        mist_pin=args.mist_pin,
    )

    controller = EffectController.create()
    for index in range(args.repeat):
        controller.off()
        if index < args.repeat - 1:
            time.sleep(args.delay)

    print("All modules reset to off.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

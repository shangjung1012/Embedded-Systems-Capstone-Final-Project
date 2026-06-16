from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Callable, TextIO

from app.effects import DEFAULT_EFFECTS, EffectController


MODULES = ("fan", "mist", "vibration")
HELP_TEXT = """Commands:
  fan on|off
  mist on|off
  vibration on|off
  led R G B BRIGHTNESS
  led off
  all off
  status
  help
  quit
"""


@dataclass(frozen=True)
class ManualCommandResult:
    effects: dict[str, object]
    message: str
    should_apply: bool = False
    should_exit: bool = False
    error: str | None = None


def initial_effects() -> dict[str, object]:
    return deepcopy(DEFAULT_EFFECTS)


def apply_manual_command(current_effects: dict[str, object], command_line: str) -> ManualCommandResult:
    effects = deepcopy(current_effects)
    parts = command_line.strip().lower().split()

    if not parts:
        return ManualCommandResult(effects=effects, message="", should_apply=False)

    command = parts[0]
    if command in ("quit", "exit"):
        return ManualCommandResult(
            effects=initial_effects(),
            message="Exiting manual control.",
            should_apply=True,
            should_exit=True,
        )

    if command == "help":
        return ManualCommandResult(effects=effects, message=HELP_TEXT.rstrip())

    if command == "status":
        return ManualCommandResult(effects=effects, message=format_effects_status(effects))

    if command == "all":
        if parts == ["all", "off"]:
            return ManualCommandResult(
                effects=initial_effects(),
                message=format_effects_status(DEFAULT_EFFECTS),
                should_apply=True,
            )
        return _error(effects, "Use: all off")

    if command in MODULES:
        return _apply_on_off(effects, command, parts)

    if command == "vibrator":
        return _apply_on_off(effects, "vibration", parts)

    if command == "led":
        return _apply_led(effects, parts)

    return _error(effects, f"Unknown command: {command}")


def format_effects_status(effects: dict[str, object]) -> str:
    fan = _enabled(effects, "fan")
    mist = _enabled(effects, "mist")
    vibration = _enabled(effects, "vibration")
    led = _led_config(effects)
    rgb = led["rgb"]
    brightness = led["brightness"]
    return (
        f"fan={'on' if fan else 'off'} "
        f"mist={'on' if mist else 'off'} "
        f"vibration={'on' if vibration else 'off'} "
        f"led=rgb({rgb[0]},{rgb[1]},{rgb[2]})@{brightness:.2f}"
    )


class ManualControlSession:
    def __init__(
        self,
        *,
        controller: EffectController | None = None,
        input_func: Callable[[str], str] = input,
        output: TextIO | None = None,
    ) -> None:
        import sys

        self.controller = controller or EffectController.create()
        self.input_func = input_func
        self.output = output or sys.stdout
        self.effects = initial_effects()

    def run(self) -> None:
        self._print("Manual module control. Type 'help' for commands.")
        self.controller.off()

        try:
            while True:
                try:
                    command_line = self.input_func("manual> ")
                except EOFError:
                    self._print("")
                    break

                result = apply_manual_command(self.effects, command_line)
                if result.error:
                    self._print(f"Error: {result.error}")
                    continue

                self.effects = result.effects
                if result.should_apply:
                    self.controller.apply(self.effects, force=True)
                if result.message:
                    self._print(result.message)
                if result.should_exit:
                    break
        except KeyboardInterrupt:
            self._print("")
        finally:
            self.effects = initial_effects()
            self.controller.off()
            self._print("All modules off.")

    def _print(self, message: str) -> None:
        print(message, file=self.output)


def _apply_on_off(effects: dict[str, object], module: str, parts: list[str]) -> ManualCommandResult:
    if len(parts) != 2 or parts[1] not in ("on", "off"):
        return _error(effects, f"Use: {module} on|off")

    effects[module] = {"enabled": parts[1] == "on"}
    return ManualCommandResult(
        effects=effects,
        message=format_effects_status(effects),
        should_apply=True,
    )


def _apply_led(effects: dict[str, object], parts: list[str]) -> ManualCommandResult:
    if parts == ["led", "off"]:
        effects["led"] = {"rgb": [0, 0, 0], "brightness": 0.0}
        return ManualCommandResult(effects=effects, message=format_effects_status(effects), should_apply=True)

    if len(parts) != 5:
        return _error(effects, "Use: led R G B BRIGHTNESS or led off")

    try:
        red, green, blue = (int(value) for value in parts[1:4])
        brightness = float(parts[4])
    except ValueError:
        return _error(effects, "LED values must be numbers")

    if any(value < 0 or value > 255 for value in (red, green, blue)):
        return _error(effects, "LED RGB values must be between 0 and 255")
    if brightness < 0.0 or brightness > 1.0:
        return _error(effects, "LED brightness must be between 0.0 and 1.0")

    effects["led"] = {"rgb": [red, green, blue], "brightness": brightness}
    return ManualCommandResult(effects=effects, message=format_effects_status(effects), should_apply=True)


def _error(effects: dict[str, object], message: str) -> ManualCommandResult:
    return ManualCommandResult(effects=deepcopy(effects), message=message, error=message)


def _enabled(effects: dict[str, object], module: str) -> bool:
    config = effects.get(module, {"enabled": False})
    if isinstance(config, dict):
        return bool(config.get("enabled", False))
    return False


def _led_config(effects: dict[str, object]) -> dict[str, object]:
    config = effects.get("led", DEFAULT_EFFECTS["led"])
    if not isinstance(config, dict):
        return deepcopy(DEFAULT_EFFECTS["led"])

    rgb = config.get("rgb", [0, 0, 0])
    if not isinstance(rgb, list) or len(rgb) != 3:
        rgb = [0, 0, 0]

    brightness = config.get("brightness", 0.0)
    try:
        normalized_brightness = float(brightness)
    except (TypeError, ValueError):
        normalized_brightness = 0.0

    return {"rgb": rgb, "brightness": normalized_brightness}

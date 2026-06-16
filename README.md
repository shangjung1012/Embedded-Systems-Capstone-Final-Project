# Embedded Systems Capstone Final Project

Raspberry Pi 4D video interaction prototype. The preprocess step reads an SRT subtitle file and produces a JSON effect timeline. The runtime then reads that timeline and triggers hardware effects.

## Preprocess

Install the Python dependencies:

```bash
uv sync
```

Generate the demo timeline:

```bash
uv run python -m preprocess
```

By default, preprocess also reads `preprocess/video/demo.mp4` with OpenCV and adds LED color events sampled from the video frames.
Because the current GPIO fan and vibration outputs are simple on/off pins, generated fan and vibration events are capped at 2 seconds by default.

Equivalent explicit command:

```bash
uv run python -m preprocess preprocess/subtitles/demo.srt -o preprocess/output/demo.timeline.json
```

Change those short on/off durations:

```bash
uv run python -m preprocess --fan-duration-ms 3000 --vibration-duration-ms 1000
```

Use `0` to keep the full matched subtitle cue duration:

```bash
uv run python -m preprocess --fan-duration-ms 0 --vibration-duration-ms 0
```

Disable video color analysis:

```bash
uv run python -m preprocess --no-video-color
```

Preview the generated timeline without waiting or opening the video:

```bash
uv run python main.py preprocess/output/demo.timeline.json --preview
```

Run the timeline clock and module logs without opening the video player:

```bash
uv run python main.py preprocess/output/demo.timeline.json --dry-run
```

Open a realtime status window while running:

```bash
uv run python main.py preprocess/output/demo.timeline.json --dry-run --status-window
```

The status window clock updates continuously from the same timeline clock used to trigger effects.

## Manual Module Control

Run the standalone manual control CLI to switch modules on and off in real time:

```bash
uv run python manual_control.py
```

Inside the prompt, use one command per line:

```text
fan on
fan off
mist on
mist off
vibration on
vibration off
led 255 120 0 0.6
led off
all off
status
help
quit
```

You can also override GPIO pins when starting manual control:

```bash
uv run python manual_control.py --fan-ina-pin 22 --fan-inb-pin 27 --vibration-pin 17 --mist-pin 23
```

Play the demo video and trigger effects on the same clock:

```bash
uv run python main.py preprocess/output/demo.timeline.json --video preprocess/video/demo.mp4
```

The video backend defaults to `auto`, which first uses the uv-managed Python backend
(`imageio-ffmpeg` + `pygame-ce`). If that backend is unavailable, it falls back to
external players in this order: `ffplay`, `cvlc`, then `vlc`.

To force the uv-managed Python video window:

```bash
uv run python main.py --player python
```

To force an external player:

```bash
uv run python main.py --player ffplay
```

The Python backend displays video frames from the project dependencies. Use `ffplay`
or VLC if you need the system player's audio/device behavior.

## Timeline Format

The preprocess output is grouped by module and only lists active time ranges:

- `fan[]`
- `mist[]`
- `vibration[]`
- `led[]`

Example:

```json
{
  "fan": [{ "start": "00:00:00.500", "end": "00:00:02.500", "enabled": true }],
  "mist": [{ "start": "00:00:14.000", "end": "00:00:18.000", "enabled": true }],
  "vibration": [{ "start": "00:00:00.500", "end": "00:00:02.500", "enabled": true }],
  "led": [{ "start": "00:00:00.500", "end": "00:00:01.000", "rgb": [78, 82, 76], "brightness": 0.32 }]
}
```

The current preprocess rules map subtitle keywords into:

- `fan.enabled`: true or false
- `mist.enabled`: true or false
- `vibration.enabled`: true or false
- `led.rgb` and `led.brightness`

The JSON file is intentionally hardware-neutral so GPIO code can be added later without changing the preprocess pipeline.

## GPIO Pins

- Vibration module: GPIO17, physical pin 11
- Fan INA: GPIO22, physical pin 15
- Fan INB: GPIO27, physical pin 13

GPIO definitions are centralized in `app/gpio.py`.

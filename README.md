# Embedded Systems Capstone Final Project

Raspberry Pi 4D video interaction prototype. The preprocess step reads an SRT subtitle file and produces a JSON effect timeline. The runtime then reads that timeline and triggers hardware effects.

## Preprocess

Generate the demo timeline:

```bash
python -m preprocess
```

By default, preprocess also reads `preprocess/video/demo.mp4` with OpenCV and adds LED color events sampled from the video frames.

Equivalent explicit command:

```bash
python -m preprocess preprocess/subtitles/demo.srt -o preprocess/output/demo.timeline.json
```

Disable video color analysis:

```bash
python -m preprocess --no-video-color
```

Preview the generated timeline without waiting or opening the video:

```bash
python main.py preprocess/output/demo.timeline.json --preview
```

Run the timeline clock and module logs without opening the video player:

```bash
python main.py preprocess/output/demo.timeline.json --dry-run
```

Open a realtime status window while running:

```bash
python main.py preprocess/output/demo.timeline.json --dry-run --status-window
```

The status window clock updates continuously from the same timeline clock used to trigger effects.

Play the demo video and trigger effects on the same clock:

```bash
python main.py preprocess/output/demo.timeline.json --video preprocess/video/demo.mp4
```

The video backend defaults to `auto`, which tries `ffplay`, `cvlc`, then `vlc`. To force one:

```bash
python main.py --player ffplay
```

## Timeline Format

The preprocess output is grouped by module and only lists active time ranges:

- `fan[]`
- `mist[]`
- `vibration[]`
- `led[]`

Example:

```json
{
  "fan": [{ "start": "00:00:00.500", "end": "00:00:04.000", "speed": 90 }],
  "mist": [{ "start": "00:00:14.000", "end": "00:00:18.000", "enabled": true }],
  "vibration": [{ "start": "00:00:00.500", "end": "00:00:04.000", "intensity": 45 }],
  "led": [{ "start": "00:00:00.500", "end": "00:00:01.000", "rgb": [78, 82, 76], "brightness": 0.32 }]
}
```

The current preprocess rules map subtitle keywords into:

- `fan.speed`: 0-100
- `mist.enabled`: true or false
- `vibration.intensity`: 0-100
- `led.rgb` and `led.brightness`

The JSON file is intentionally hardware-neutral so GPIO code can be added later without changing the preprocess pipeline.

## GPIO Pins

- Vibration module: GPIO17, physical pin 11
- Fan INA: GPIO22, physical pin 15
- Fan INB: GPIO27, physical pin 13

GPIO definitions are centralized in `app/gpio.py`.

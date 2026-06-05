# Embedded Systems Capstone Final Project

Raspberry Pi 4D video interaction prototype. The preprocess step reads an SRT subtitle file and produces a JSON effect timeline. The runtime then reads that timeline and triggers hardware effects.

## Preprocess

Generate the demo timeline:

```bash
python -m preprocess
```

Equivalent explicit command:

```bash
python -m preprocess preprocess/subtitles/demo.srt -o preprocess/output/demo.timeline.json
```

Preview the generated timeline without waiting or opening the video:

```bash
python main.py preprocess/output/demo.timeline.json --preview
```

Run the timeline clock and module logs without opening the video player:

```bash
python main.py preprocess/output/demo.timeline.json --dry-run
```

Play the demo video and trigger effects on the same clock:

```bash
python main.py preprocess/output/demo.timeline.json --video preprocess/video/demo.mp4
```

The video backend defaults to `auto`, which tries `ffplay`, `cvlc`, then `vlc`. To force one:

```bash
python main.py --player ffplay
```

## Timeline Effects

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

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

Preview the generated timeline:

```bash
python main.py preprocess/output/demo.timeline.json
```

Run with real timing:

```bash
python main.py preprocess/output/demo.timeline.json --realtime
```

## Timeline Effects

The current preprocess rules map subtitle keywords into:

- `fan.speed`: 0-100
- `mist.enabled`: true or false
- `vibration.intensity`: 0-100
- `led.rgb` and `led.brightness`

The JSON file is intentionally hardware-neutral so GPIO code can be added later without changing the preprocess pipeline.

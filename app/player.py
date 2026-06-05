from __future__ import annotations

from pathlib import Path
import shutil
import subprocess


class VideoPlayer:
    def __init__(self, video_path: Path | None, player: str = "auto") -> None:
        self.video_path = video_path
        self.player = player
        self.process: subprocess.Popen[bytes] | None = None

    def start(self) -> None:
        command = self._build_command()
        if command is None:
            print("[player] video playback disabled")
            return

        print(f"[player] start {' '.join(command)}")
        self.process = subprocess.Popen(command)

    def stop(self) -> None:
        if self.process is None or self.process.poll() is not None:
            return

        self.process.terminate()
        try:
            self.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=3)

    def wait(self) -> None:
        if self.process is not None:
            self.process.wait()

    def _build_command(self) -> list[str] | None:
        if self.player == "none" or self.video_path is None:
            return None
        if not self.video_path.exists():
            raise FileNotFoundError(f"Video file not found: {self.video_path}")

        selected_player = self._select_player()
        if selected_player == "ffplay":
            return ["ffplay", "-autoexit", "-loglevel", "error", str(self.video_path)]
        if selected_player == "cvlc":
            return ["cvlc", "--play-and-exit", str(self.video_path)]
        if selected_player == "vlc":
            return ["vlc", "--play-and-exit", str(self.video_path)]
        raise ValueError(f"Unsupported player: {self.player}")

    def _select_player(self) -> str:
        if self.player != "auto":
            if shutil.which(self.player) is None:
                raise FileNotFoundError(f"Player executable not found: {self.player}")
            return self.player

        for candidate in ("ffplay", "cvlc", "vlc"):
            if shutil.which(candidate):
                return candidate
        raise FileNotFoundError("No video player found. Install ffmpeg/VLC or use --player none.")


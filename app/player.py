from __future__ import annotations

import multiprocessing
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Literal


PlayerBackend = Literal["python", "ffplay", "cvlc", "vlc"]


class VideoPlayer:
    def __init__(self, video_path: Path | None, player: str = "auto") -> None:
        self.video_path = video_path
        self.player = player
        self.process: subprocess.Popen[bytes] | multiprocessing.Process | None = None

    def start(self) -> None:
        backend = self._select_player()
        if backend is None:
            print("[player] video playback disabled")
            return

        if backend == "python":
            print(f"[player] start python video window {self.video_path}")
            self.process = multiprocessing.Process(target=_play_with_pygame, args=(self.video_path,))
            self.process.start()
            return

        command = self._build_external_command(backend)
        print(f"[player] start {' '.join(command)}")
        self.process = subprocess.Popen(command)

    def stop(self) -> None:
        if self.process is None or not self.is_running():
            return

        if isinstance(self.process, multiprocessing.Process):
            self.process.terminate()
            self.process.join(timeout=3)
            if self.process.is_alive():
                self.process.kill()
                self.process.join(timeout=3)
            return

        self.process.terminate()
        try:
            self.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=3)

    def wait(self) -> None:
        if isinstance(self.process, multiprocessing.Process):
            self.process.join()
        elif self.process is not None:
            self.process.wait()

    def is_running(self) -> bool:
        if isinstance(self.process, multiprocessing.Process):
            return self.process.is_alive()
        return self.process is not None and self.process.poll() is None

    def _validate_video_path(self) -> None:
        if self.player == "none" or self.video_path is None:
            return
        if not self.video_path.exists():
            raise FileNotFoundError(f"Video file not found: {self.video_path}")

    def _build_external_command(self, selected_player: PlayerBackend) -> list[str]:
        if self.video_path is None:
            raise ValueError("video_path is required for video playback")
        if selected_player == "python":
            raise ValueError("python player does not use an external command")
        if selected_player == "ffplay":
            return ["ffplay", "-autoexit", "-loglevel", "error", str(self.video_path)]
        if selected_player == "cvlc":
            return ["cvlc", "--play-and-exit", str(self.video_path)]
        if selected_player == "vlc":
            return ["vlc", "--play-and-exit", str(self.video_path)]
        raise ValueError(f"Unsupported player: {self.player}")

    def _select_player(self) -> PlayerBackend | None:
        if self.player == "none" or self.video_path is None:
            return None

        self._validate_video_path()

        if self.player != "auto":
            if self.player == "python":
                _validate_python_player()
                return "python"
            if shutil.which(self.player) is None:
                raise FileNotFoundError(f"Player executable not found: {self.player}")
            return self.player  # type: ignore[return-value]

        try:
            _validate_python_player()
            return "python"
        except RuntimeError as error:
            print(f"[player] python backend unavailable: {error}", file=sys.stderr)

        for candidate in ("ffplay", "cvlc", "vlc"):
            if shutil.which(candidate):
                return candidate
        raise FileNotFoundError("No video player found. Run `uv sync`, install ffmpeg/VLC, or use --player none.")


def _validate_python_player() -> None:
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    missing_packages: list[str] = []
    try:
        import imageio_ffmpeg  # noqa: F401
    except ImportError:
        missing_packages.append("imageio-ffmpeg")

    try:
        import pygame  # noqa: F401
    except ImportError:
        missing_packages.append("pygame-ce")

    if missing_packages:
        packages = ", ".join(missing_packages)
        raise RuntimeError(f"missing {packages}; run `uv sync`")


def _play_with_pygame(video_path: Path | None) -> None:
    if video_path is None:
        return

    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    import imageio_ffmpeg
    import pygame

    reader = imageio_ffmpeg.read_frames(str(video_path), pix_fmt="rgb24")
    pygame.init()
    try:
        metadata = next(reader)
        width, height = metadata["size"]
        fps = float(metadata.get("fps") or 30)
        screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(video_path.name)
        clock = pygame.time.Clock()

        for frame in reader:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return

            surface = pygame.image.frombuffer(frame, (width, height), "RGB")
            screen.blit(surface, (0, 0))
            pygame.display.flip()
            clock.tick(fps)
    finally:
        reader.close()
        pygame.quit()

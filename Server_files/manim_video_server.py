import re
import shutil
import subprocess
import sys
from pathlib import Path
from importlib.util import find_spec
from fastapi import FastAPI

try:
    from Server_files.models import VideoRequest
except ModuleNotFoundError:
    from models import VideoRequest


app = FastAPI()

GENERATED_DIR = Path("generated_manim")
SCENE_DIR = GENERATED_DIR / "scenes"
MEDIA_DIR = GENERATED_DIR / "media"


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower()).strip("_")
    return slug[:60] or "physics_concept"


def _scene_name(topic: str) -> str:
    return "".join(part.capitalize() for part in _slugify(topic).split("_")) + "Scene"


def _concept_kind(topic: str, question: str = "") -> str:
    text = f"{topic} {question}".lower()
    if "momentum" in text:
        return "momentum"
    if "projectile" in text or "trajectory" in text:
        return "projectile"
    if "simple harmonic" in text or "shm" in text or "oscillation" in text:
        return "shm"
    if "electric field" in text or "charge" in text:
        return "electric_field"
    return "generic"


def _projectile_scene(scene_name: str, topic: str) -> str:
    topic_literal = repr(topic)
    return f'''from manim import *


class {scene_name}(Scene):
    def construct(self):
        title = Text({topic_literal}, font_size=38).to_edge(UP)
        axes = Axes(
            x_range=[0, 8, 1],
            y_range=[0, 4, 1],
            x_length=9,
            y_length=4.5,
            tips=True,
        ).shift(DOWN * 0.4)
        labels = axes.get_axis_labels(Text("x"), Text("y"))
        path = axes.plot(lambda x: -0.18 * (x - 4) ** 2 + 3, x_range=[0.35, 7.65], color=YELLOW)
        ball = Dot(axes.c2p(0.35, -0.18 * (0.35 - 4) ** 2 + 3), color=RED)
        vx = Arrow(ORIGIN, RIGHT * 1.2, color=BLUE).next_to(ball, RIGHT, buff=0.15)
        vy = Arrow(ORIGIN, UP * 0.9, color=GREEN).next_to(ball, UP, buff=0.15)
        note = Text("Horizontal velocity stays constant; gravity changes vertical velocity.", font_size=24)
        note.to_edge(DOWN)

        self.play(Write(title), Create(axes), Write(labels))
        self.play(Create(path))
        self.play(FadeIn(ball), GrowArrow(vx), GrowArrow(vy), Write(note))
        self.play(MoveAlongPath(ball, path), run_time=4, rate_func=linear)
        self.wait(1)
'''


def _shm_scene(scene_name: str, topic: str) -> str:
    topic_literal = repr(topic)
    return f'''from manim import *
import numpy as np


class {scene_name}(Scene):
    def construct(self):
        title = Text({topic_literal}, font_size=38).to_edge(UP)
        line = NumberLine(x_range=[-4, 4, 1], length=8).shift(DOWN)
        mass = Square(side_length=0.55, color=BLUE, fill_opacity=0.7).move_to(line.n2p(3))
        spring = always_redraw(lambda: Line(line.n2p(-4), mass.get_left(), color=GREEN))
        equilibrium = DashedLine(UP * 1.2, DOWN * 2.0, color=WHITE).move_to(line.n2p(0))
        label = Text("Restoring force points toward equilibrium.", font_size=26).to_edge(DOWN)

        self.play(Write(title), Create(line), Create(equilibrium), FadeIn(mass), Create(spring))
        self.play(Write(label))
        self.play(mass.animate.move_to(line.n2p(-3)), run_time=1.5, rate_func=smooth)
        self.play(mass.animate.move_to(line.n2p(3)), run_time=1.5, rate_func=smooth)
        self.play(mass.animate.move_to(line.n2p(0)), run_time=1.2, rate_func=smooth)
        self.wait(1)
'''


def _electric_field_scene(scene_name: str, topic: str) -> str:
    topic_literal = repr(topic)
    return f'''from manim import *
import numpy as np


class {scene_name}(Scene):
    def construct(self):
        title = Text({topic_literal}, font_size=38).to_edge(UP)
        charge = Circle(radius=0.35, color=RED, fill_opacity=0.8)
        plus = Text("+", font_size=34).move_to(charge)
        lines = VGroup()
        for angle in np.linspace(0, TAU, 12, endpoint=False):
            start = 0.55 * np.array([np.cos(angle), np.sin(angle), 0])
            end = 3.0 * np.array([np.cos(angle), np.sin(angle), 0])
            lines.add(Arrow(start, end, buff=0, color=YELLOW))
        note = Text("Field lines point away from a positive charge.", font_size=26).to_edge(DOWN)

        self.play(Write(title), FadeIn(charge), Write(plus))
        self.play(LaggedStart(*[GrowArrow(line) for line in lines], lag_ratio=0.08))
        self.play(Write(note))
        self.wait(1)
'''


def _momentum_scene(scene_name: str, topic: str) -> str:
    topic_literal = repr(topic)
    return f'''from manim import *


class {scene_name}(Scene):
    def construct(self):
        title = Text({topic_literal}, font_size=38).to_edge(UP)
        track = Line(LEFT * 5, RIGHT * 5, color=GRAY).shift(DOWN * 1.2)
        cart = Square(side_length=0.7, color=BLUE, fill_opacity=0.75).move_to(LEFT * 3 + DOWN * 0.8)
        velocity_arrow = Arrow(cart.get_right(), cart.get_right() + RIGHT * 1.6, color=YELLOW, buff=0)
        velocity_label = Text("velocity v", font_size=24, color=YELLOW).next_to(velocity_arrow, UP)
        mass_label = Text("mass m", font_size=24, color=BLUE).next_to(cart, DOWN)
        formula = Text("momentum p = m x v", font_size=32).to_edge(DOWN)
        note = Text("More mass or more velocity means more momentum.", font_size=26).next_to(formula, UP)

        self.play(Write(title), Create(track))
        self.play(FadeIn(cart), Write(mass_label))
        self.play(GrowArrow(velocity_arrow), Write(velocity_label))
        self.play(Write(formula), Write(note))
        self.play(
            cart.animate.shift(RIGHT * 5.5),
            velocity_arrow.animate.shift(RIGHT * 5.5),
            velocity_label.animate.shift(RIGHT * 5.5),
            mass_label.animate.shift(RIGHT * 5.5),
            run_time=3,
            rate_func=linear,
        )
        self.wait(1)
'''


def _generic_scene(scene_name: str, topic: str) -> str:
    topic_literal = repr(topic)
    return f'''from manim import *


class {scene_name}(Scene):
    def construct(self):
        title = Text({topic_literal}, font_size=38).to_edge(UP)
        concept = Circle(radius=1.15, color=BLUE)
        idea = Text({topic_literal}, font_size=28).move_to(concept)
        relation = Text("definition -> key relation -> example", font_size=28).shift(DOWN * 0.8)
        note = Text("This template is a fallback; add a specific scene for richer animation.", font_size=24).to_edge(DOWN)

        self.play(Write(title))
        self.play(Create(concept), Write(idea))
        self.play(Transform(idea.copy(), relation), Write(note))
        self.wait(1)
'''


def build_manim_code(topic: str, question: str = "") -> tuple[str, str]:
    scene_name = _scene_name(topic)
    kind = _concept_kind(topic, question)
    if kind == "momentum":
        return scene_name, _momentum_scene(scene_name, topic)
    if kind == "projectile":
        return scene_name, _projectile_scene(scene_name, topic)
    if kind == "shm":
        return scene_name, _shm_scene(scene_name, topic)
    if kind == "electric_field":
        return scene_name, _electric_field_scene(scene_name, topic)
    return scene_name, _generic_scene(scene_name, topic)


def render_scene(scene_file: Path, scene_name: str, quality: str) -> dict:
    if find_spec("manim") is None:
        return {
            "rendered": False,
            "reason": "Manim is not installed in this Python environment.",
        }

    quality_flag = {
        "low": "-ql",
        "medium": "-qm",
        "high": "-qh",
    }.get(quality, "-ql")

    command = [
        sys.executable,
        "-m",
        "manim",
        quality_flag,
        "--media_dir",
        str(MEDIA_DIR),
        str(scene_file),
        scene_name,
    ]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=180)
    except FileNotFoundError as exc:
        return {
            "rendered": False,
            "reason": f"Unable to start Manim renderer: {exc}",
        }
    except subprocess.TimeoutExpired:
        return {
            "rendered": False,
            "reason": "Manim rendering timed out after 180 seconds.",
        }

    if completed.returncode != 0:
        diagnostic = completed.stderr[-2000:] or completed.stdout[-2000:]
        return {
            "rendered": False,
            "reason": diagnostic or "Manim exited with a non-zero status.",
        }

    videos = sorted(MEDIA_DIR.rglob(f"{scene_name}.mp4"), key=lambda path: path.stat().st_mtime, reverse=True)
    return {
        "rendered": bool(videos),
        "video_path": str(videos[0].resolve()) if videos else None,
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "manim_available": find_spec("manim") is not None,
        "manim_executable": shutil.which("manim"),
        "python": sys.executable,
    }


@app.post("/generate-video")
def generate_video(data: VideoRequest):
    SCENE_DIR.mkdir(parents=True, exist_ok=True)
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)

    scene_name, code = build_manim_code(data.topic, data.question)
    scene_file = SCENE_DIR / f"{_slugify(data.topic)}.py"
    scene_file.write_text(code, encoding="utf-8")

    result = {
        "topic": data.topic,
        "scene_name": scene_name,
        "scene_file": str(scene_file.resolve()),
        "code": code,
        "render_requested": data.render,
    }

    if data.render:
        result.update(render_scene(scene_file, scene_name, data.quality))
    else:
        result["rendered"] = False
        result["reason"] = "render flag was false; Manim code generated only."

    return result

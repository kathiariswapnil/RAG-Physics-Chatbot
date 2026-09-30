import math
import re
from pathlib import Path

from fastapi import FastAPI
from PIL import Image, ImageDraw, ImageFont

try:
    from Server_files.models import DiagramRequest
except ModuleNotFoundError:
    from models import DiagramRequest


app = FastAPI()
OUTPUT_DIR = Path("generated_diagrams")


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower()).strip("_")
    return slug[:70] or "physics_diagram"


def _font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def _draw_arrow(draw: ImageDraw.ImageDraw, start, end, fill, width=4):
    draw.line([start, end], fill=fill, width=width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    arrow_len = 16
    arrow_angle = math.pi / 7
    p1 = (
        end[0] - arrow_len * math.cos(angle - arrow_angle),
        end[1] - arrow_len * math.sin(angle - arrow_angle),
    )
    p2 = (
        end[0] - arrow_len * math.cos(angle + arrow_angle),
        end[1] - arrow_len * math.sin(angle + arrow_angle),
    )
    draw.polygon([end, p1, p2], fill=fill)


def _draw_projectile_trajectory(topic: str, output_path: Path):
    width, height = 1100, 700
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    title_font = _font(36)
    label_font = _font(24)
    small_font = _font(20)

    draw.text((40, 28), "Projectile Motion: Trajectory Graph", fill="#111827", font=title_font)
    draw.text((40, 76), topic, fill="#4b5563", font=small_font)

    origin = (110, 590)
    x_end = (1010, 590)
    y_end = (110, 135)
    _draw_arrow(draw, origin, x_end, "#111827", width=4)
    _draw_arrow(draw, origin, y_end, "#111827", width=4)
    draw.text((1018, 574), "x", fill="#111827", font=label_font)
    draw.text((94, 100), "y", fill="#111827", font=label_font)

    points = []
    for i in range(140):
        t = i / 139
        x = origin[0] + 810 * t
        y = origin[1] - 390 * (4 * t * (1 - t))
        points.append((x, y))
    draw.line(points, fill="#f59e0b", width=6)

    launch = points[0]
    apex = min(points, key=lambda point: point[1])
    landing = points[-1]
    draw.ellipse((launch[0] - 8, launch[1] - 8, launch[0] + 8, launch[1] + 8), fill="#ef4444")
    draw.ellipse((apex[0] - 8, apex[1] - 8, apex[0] + 8, apex[1] + 8), fill="#2563eb")
    draw.ellipse((landing[0] - 8, landing[1] - 8, landing[0] + 8, landing[1] + 8), fill="#16a34a")

    _draw_arrow(draw, (launch[0] + 10, launch[1] - 10), (launch[0] + 150, launch[1] - 110), "#2563eb", width=4)
    _draw_arrow(draw, (apex[0], apex[1] + 12), (apex[0], apex[1] + 95), "#dc2626", width=4)
    _draw_arrow(draw, (apex[0] - 80, apex[1] + 45), (apex[0] + 85, apex[1] + 45), "#2563eb", width=4)

    draw.text((launch[0] + 155, launch[1] - 130), "initial velocity", fill="#2563eb", font=small_font)
    draw.text((apex[0] + 18, apex[1] + 45), "g", fill="#dc2626", font=small_font)
    draw.text((apex[0] - 75, apex[1] + 15), "horizontal velocity", fill="#2563eb", font=small_font)
    draw.text((apex[0] - 45, apex[1] - 36), "highest point", fill="#111827", font=small_font)
    draw.text((landing[0] - 40, landing[1] + 18), "range", fill="#16a34a", font=small_font)

    caption = "Path is parabolic: horizontal motion is uniform, vertical motion is accelerated by gravity."
    draw.rounded_rectangle((145, 620, 985, 670), radius=14, fill="#f3f4f6", outline="#d1d5db")
    draw.text((165, 634), caption, fill="#111827", font=small_font)

    image.save(output_path)


def _draw_free_body_diagram(topic: str, output_path: Path):
    width, height = 900, 650
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    title_font = _font(34)
    label_font = _font(24)
    small_font = _font(20)

    draw.text((40, 30), "Free Body Diagram", fill="#111827", font=title_font)
    draw.text((40, 78), topic, fill="#4b5563", font=small_font)

    block = (390, 275, 510, 395)
    draw.rectangle(block, fill="#bfdbfe", outline="#1d4ed8", width=4)
    draw.text((420, 320), "m", fill="#111827", font=label_font)
    center = (450, 335)

    _draw_arrow(draw, center, (450, 170), "#16a34a", width=5)
    _draw_arrow(draw, center, (450, 510), "#dc2626", width=5)
    _draw_arrow(draw, center, (610, 335), "#2563eb", width=5)
    _draw_arrow(draw, center, (290, 335), "#7c3aed", width=5)

    draw.text((465, 178), "Normal N", fill="#16a34a", font=label_font)
    draw.text((465, 480), "Weight mg", fill="#dc2626", font=label_font)
    draw.text((615, 318), "Applied force", fill="#2563eb", font=label_font)
    draw.text((140, 318), "Friction", fill="#7c3aed", font=label_font)
    draw.line([(150, 395), (750, 395)], fill="#111827", width=4)
    draw.text((315, 430), "Forces are shown from the object's center.", fill="#111827", font=small_font)

    image.save(output_path)


def _diagram_kind(topic: str) -> str:
    text = topic.lower()
    if "projectile" in text or "trajectory" in text or "graph" in text:
        return "trajectory_graph"
    return "free_body_diagram"


def create_diagram(topic: str) -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    diagram_type = _diagram_kind(topic)
    output_path = OUTPUT_DIR / f"{_slugify(topic)}_{diagram_type}.png"

    if diagram_type == "trajectory_graph":
        _draw_projectile_trajectory(topic, output_path)
    else:
        _draw_free_body_diagram(topic, output_path)

    return {
        "diagram_type": diagram_type,
        "topic": topic,
        "status": "generated",
        "image_path": str(output_path.resolve()),
    }

@app.post("/generate-diagram")
def generate_diagram(data: DiagramRequest):
    return create_diagram(data.topic)

@app.get("/health")
def health():
    return {"status": "ok"}

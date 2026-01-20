# scale_4x.py
from PIL import Image
import sys
from pathlib import Path

def scale_4x(input_path: str, output_path: str | None = None) -> None:
    src = Path(input_path)
    if output_path is None:
        output_path = src.with_name(f"{src.stem}_4x{src.suffix}")

    img = Image.open(src)
    w, h = img.size
    img = img.resize((w * 4, h * 4), resample=Image.NEAREST)
    img.save(output_path)
    print(f"Saved: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scale_4x.py <input.png> [output.png]")
        raise SystemExit(1)
    scale_4x(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
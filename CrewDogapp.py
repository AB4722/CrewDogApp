from flask import Flask, request, render_template, send_file, abort
from PIL import Image
import os
import shutil
import sys

app = Flask(__name__)

def get_base_path():
    if getattr(sys, 'frozen', False):  # PyInstaller packaging
        return sys._MEIPASS
    return os.path.abspath(".")

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        base_path = get_base_path()
        crewneck_folder = os.path.join(base_path, "backgrounds", "Crewneck")

        if not os.path.exists(crewneck_folder):
            abort(400, "Crewneck backgrounds not found.")

        crewneck_files = [
            os.path.join(crewneck_folder, f)
            for f in os.listdir(crewneck_folder)
            if os.path.isfile(os.path.join(crewneck_folder, f))
        ]

        if not crewneck_files:
            abort(400, "No Crewneck files found.")

        crewneck_file_path = crewneck_files[0]

        design_file = request.files["design"]
        upload_dir = os.path.join(base_path, "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        design_path = os.path.join(upload_dir, "uploaded_design.png")
        design_file.save(design_path)

        output_dir = os.path.join(base_path, "output")
        os.makedirs(output_dir, exist_ok=True)

        with Image.open(crewneck_file_path).convert("RGBA") as background, Image.open(design_path).convert("RGBA") as design:
            dpi = background.info.get('dpi', (300, 300))
            design.info['dpi'] = dpi

            bg_width, bg_height = background.size
            design_aspect_ratio = design.width / design.height

            # Offsets
            extra_offset_mm_left = 11
            extra_offset_mm_down = 8
            offset_px_left = int((extra_offset_mm_left / 25.4) * dpi[0])
            offset_px_down = int((extra_offset_mm_down / 25.4) * dpi[1])

            # Resize design with warnings for low resolution
            design_width = int(bg_width * 0.255)
            design_height = int(design_width / design_aspect_ratio)

            if design.width < design_width or design.height < design_height:
                print("Warning: Input design resolution is low. Output may be pixelated.")

            design = design.resize((design_width, design_height), Image.Resampling.LANCZOS)

            x = bg_width - design_width - offset_px_left
            y = offset_px_down

            composite = background.copy()
            composite.alpha_composite(design, (x, y))

            output_file_name = f"output_{os.path.basename(crewneck_file_path)}"
            output_file_path = os.path.join(output_dir, output_file_name)
            composite.save(output_file_path, "PNG", optimize=True)

        return send_file(output_file_path, as_attachment=True)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
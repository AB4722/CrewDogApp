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
        # Define the path to the Crewneck folder
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

        # Process the Crewneck file
        with Image.open(crewneck_file_path).convert("RGBA") as background, Image.open(design_path).convert("RGBA") as design:
            # Set high DPI (600 DPI)
            high_dpi = 600

            # Resize background to match higher DPI
            bg_width, bg_height = background.size
            scale_factor = high_dpi / 300  # Assuming input is 300 DPI
            bg_width = int(bg_width * scale_factor)
            bg_height = int(bg_height * scale_factor)
            background = background.resize((bg_width, bg_height), Image.Resampling.LANCZOS)

            # Resize the design to match higher DPI
            design_width = int(bg_width * 0.255)  # 25.5% of the background width
            design_aspect_ratio = design.width / design.height
            design_height = int(design_width / design_aspect_ratio)
            design = design.resize((design_width, design_height), Image.Resampling.LANCZOS)

            # Define offsets (converted to 600 DPI)
            extra_offset_mm_left = 11  # Move 11mm to the left
            extra_offset_mm_down = 8  # Move 8mm down
            offset_px_left = int((extra_offset_mm_left / 25.4) * high_dpi)
            offset_px_down = int((extra_offset_mm_down / 25.4) * high_dpi)

            # Adjust position
            x = bg_width - design_width - offset_px_left
            y = offset_px_down

            # Composite the design onto the background
            composite = background.copy()
            composite.alpha_composite(design, (x, y))

            # Save the modified image with high DPI
            output_file_name = f"output_{os.path.basename(crewneck_file_path)}"
            output_file_path = os.path.join(output_dir, output_file_name)
            composite.save(output_file_path, "PNG", dpi=(high_dpi, high_dpi), optimize=True)

        # Send the modified image back to the user
        return send_file(output_file_path, as_attachment=True)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
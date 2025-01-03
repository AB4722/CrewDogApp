from flask import Flask, request, render_template, send_file, abort
from PIL import Image
import os
import sys
import io

app = Flask(__name__)

# Get the base path for the application (handles PyInstaller packaging)
def get_base_path():
    if getattr(sys, 'frozen', False):  # Check if running in a PyInstaller bundle
        return sys._MEIPASS  # PyInstaller sets this to the temporary directory
    return os.path.abspath(".")

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        # Get selected garment type
        garment_type = request.form.get("garment")
        if not garment_type:
            abort(400, description="No garment type selected.")

        # Define garment folder path
        base_path = get_base_path()
        garment_folder = os.path.join(base_path, "backgrounds", garment_type.capitalize())
        if not os.path.exists(garment_folder):
            abort(400, description=f"{garment_type.capitalize()} backgrounds not found.")

        # Get the first garment file
        garment_files = [
            os.path.join(garment_folder, f)
            for f in os.listdir(garment_folder)
            if os.path.isfile(os.path.join(garment_folder, f))
        ]
        if not garment_files:
            abort(400, description=f"No {garment_type.capitalize()} files found.")

        garment_file_path = garment_files[0]

        # Get uploaded design file
        design_file = request.files["design"]
        design = Image.open(design_file.stream)

        # Process garment file
        with Image.open(garment_file_path) as background:
            # Preserve original DPI and ensure both images support transparency
            bg_dpi = background.info.get("dpi", (300, 300))
            background = background.convert("RGBA")
            design = design.convert("RGBA")

            bg_width, bg_height = background.size
            design_width, design_height = design.size

            # Determine placement and size
            print_type = request.form.get("print_type")
            if print_type == "front":
                target_height = int(bg_height * 0.3)
            elif print_type == "side":
                target_height = int(bg_height * 0.3 * 0.9)  # 10% smaller for side print
            else:
                target_height = int(bg_height * 0.3)

            # Scale design proportionally only if resizing is required
            if target_height < design_height:
                scale_factor = target_height / design_height
                design_width = int(design_width * scale_factor)
                design_height = target_height
                design = design.resize((design_width, design_height), Image.Resampling.LANCZOS)

            # Compute placement
            if print_type == "side":
                x = int(bg_width * 0.70) - (design_width // 2)
                y = int(bg_height * 0.32) - (design_height // 2)
            else:  # Front placement
                x = (bg_width - design_width) // 2
                y = (bg_height - design_height) // 2

            # Paste the design onto the background
            composite = background.copy()
            composite.paste(design, (x, y), design)

            # Save the final image with high DPI
            output = io.BytesIO()
            composite.save(output, "PNG", dpi=bg_dpi)
            output.seek(0)

        return send_file(output, mimetype="image/png", as_attachment=True, download_name="output.png")

    # Render the HTML form
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
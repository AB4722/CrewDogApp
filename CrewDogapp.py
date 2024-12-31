from flask import Flask, request, render_template, send_file, abort
from PIL import Image
import os
import shutil
import sys

app = Flask(__name__)

# Get the base path for the application (handles PyInstaller packaging)
def get_base_path():
    if getattr(sys, 'frozen', False):  # Check if running in a PyInstaller bundle
        return sys._MEIPASS  # PyInstaller sets this to the temporary directory
    return os.path.abspath(".")

# Function to process images
def center_design_on_images(design_path, background_paths, output_dir, collection_name):
    design_height_mm = 120
    background_height_mm = 600
    offset_mmwidth = 95  # Offset in mm
    offset_mmheight = 147  # Offset in mm
    dpi = 300
    design_height_px = int((design_height_mm / 25.4) * dpi)
    background_height_px = int((background_height_mm / 25.4) * dpi)
    offset_pxwidth = int((offset_mmwidth / 25.4) * dpi)
    offset_pxheight = int((offset_mmheight / 25.4) * dpi)

    # Load and resize the design
    design = Image.open(design_path).convert("RGBA")
    aspect_ratio = design.width / design.height
    design = design.resize((int(design_height_px * aspect_ratio), design_height_px), Image.ANTIALIAS)

    for background_path in background_paths:
        background = Image.open(background_path).convert("RGBA")
        bg_aspect_ratio = background.width / background.height
        background = background.resize(
            (int(background_height_px * bg_aspect_ratio), background_height_px), Image.ANTIALIAS
        )

        composite = background.copy()
        bg_width, bg_height = composite.size
        design_width, design_height = design.size

        x = (bg_width - design_width) // 2 + offset_pxwidth
        y = (bg_height - design_height) // 2 - offset_pxheight

        composite.paste(design, (x, y), design)

        # Generate output filename with collection name and background filename
        background_name = os.path.basename(background_path)
        output_filename = f"{collection_name}_{background_name}"
        output_path = os.path.join(output_dir, output_filename)

        composite.save(output_path, "PNG")

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        # Define the path to the Crewneck folder
        base_path = get_base_path()
        crewneck_folder = os.path.join(base_path, "backgrounds", "Crewneck")

        # Ensure the folder exists
        if not os.path.exists(crewneck_folder):
            abort(400, description="Crewneck backgrounds not found.")

        # Get one Crewneck file (the first one)
        crewneck_files = [
            os.path.join(crewneck_folder, f)
            for f in os.listdir(crewneck_folder)
            if os.path.isfile(os.path.join(crewneck_folder, f))
        ]

        if not crewneck_files:
            abort(400, description="No Crewneck files found.")

        # Select the first Crewneck file
        crewneck_file_path = crewneck_files[0]

        # Get the uploaded design file
        design_file = request.files["design"]
        upload_dir = os.path.join(base_path, "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        design_path = os.path.join(upload_dir, "uploaded_design.png")
        design_file.save(design_path)

        # Output directory for the modified image
        output_dir = os.path.join(base_path, "output")
        os.makedirs(output_dir, exist_ok=True)

        # Process the Crewneck file
        with Image.open(crewneck_file_path).convert("RGBA") as background, Image.open(design_path).convert("RGBA") as design:
            # Resize the design to fit proportionally within the background
            bg_width, bg_height = background.size
            design_aspect_ratio = design.width / design.height

            # Define offsets
            extra_offset_mm_left = 4  # Additional offset to the left in millimeters
            extra_offset_mm_down = -5  # Additional offset downward in millimeters

            # Convert offsets to pixels
            dpi = 300  # Assuming 300 DPI
            offset_px_left = int(((10 + extra_offset_mm_left) / 25.4) * dpi)
            offset_px_down = int(((10 + extra_offset_mm_down) / 25.4) * dpi)

            # Resize the design to 90% of its original calculated size
            design_width = int(bg_width * 0.27)  # 30% reduced by 10%
            design_height = int(design_width / design_aspect_ratio)
            design = design.resize((design_width, design_height), Image.ANTIALIAS)

            # Adjust position
            x = bg_width - design_width - offset_px_left
            y = offset_px_down

            # Paste the design onto the background
            composite = background.copy()
            composite.paste(design, (x, y), design)

            # Save the modified image
            output_file_name = f"output_{os.path.basename(crewneck_file_path)}"
            output_file_path = os.path.join(output_dir, output_file_name)
            composite.save(output_file_path, "PNG")

        # Send the modified image back to the user
        return send_file(output_file_path, as_attachment=True)

    # Render the HTML form
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)

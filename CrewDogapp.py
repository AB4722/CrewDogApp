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
        base_path = get_base_path()

        # Get user inputs
        collection_name = request.form.get("collection_name", "DefaultCollection")

        # Define the folders for Crewneck and Hoodie backgrounds
        crewneck_folder = os.path.join(base_path, "backgrounds", "Crewneck")
        hoodie_folder = os.path.join(base_path, "backgrounds", "Hoodie")

        # Check if background folders exist
        if not os.path.exists(crewneck_folder):
            abort(400, description="Crewneck backgrounds not found.")
        if not os.path.exists(hoodie_folder):
            abort(400, description="Hoodie backgrounds not found.")

        # Get the background files
        crewneck_files = [
            os.path.join(crewneck_folder, f)
            for f in os.listdir(crewneck_folder)
            if os.path.isfile(os.path.join(crewneck_folder, f))
        ]
        hoodie_files = [
            os.path.join(hoodie_folder, f)
            for f in os.listdir(hoodie_folder)
            if os.path.isfile(os.path.join(hoodie_folder, f))
        ]

        # Get the design file
        design_file = request.files["design"]
        upload_dir = os.path.join(base_path, "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        design_path = os.path.join(upload_dir, "design.png")
        design_file.save(design_path)

        # Ensure output directories exist
        output_dir = os.path.join(base_path, "output")
        crewneck_output_dir = os.path.join(output_dir, "Crewneck")
        hoodie_output_dir = os.path.join(output_dir, "Hoodie")
        os.makedirs(crewneck_output_dir, exist_ok=True)
        os.makedirs(hoodie_output_dir, exist_ok=True)

        # Process Crewneck files
        center_design_on_images(design_path, crewneck_files, crewneck_output_dir, collection_name)

        # Process Hoodie files
        center_design_on_images(design_path, hoodie_files, hoodie_output_dir, collection_name)

        # Create the zip file
        zip_path = os.path.join(base_path, "output.zip")
        shutil.make_archive(zip_path.replace(".zip", ""), "zip", output_dir)

        # Send the zip file to the user
        return send_file(zip_path, as_attachment=True)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)

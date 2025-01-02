from flask import Flask, request, render_template, send_file, abort
from PIL import Image
import os
import sys

app = Flask(__name__)

# Get the base path for the application (handles PyInstaller packaging)
def get_base_path():
    if getattr(sys, 'frozen', False):  # Check if running in a PyInstaller bundle
        return sys._MEIPASS  # PyInstaller sets this to the temporary directory
    return os.path.abspath(".")

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        # Get the selected garment type
        garment_type = request.form.get("garment")
        if not garment_type:
            abort(400, description="No garment type selected.")

        # Define the path to the garment folder
        base_path = get_base_path()
        garment_folder = os.path.join(base_path, "backgrounds", garment_type.capitalize())

        # Ensure the folder exists
        if not os.path.exists(garment_folder):
            print(f"Error: {garment_folder} not found.")
            abort(400, description=f"{garment_type.capitalize()} backgrounds not found.")

        # Get the first garment file
        garment_files = [
            os.path.join(garment_folder, f)
            for f in os.listdir(garment_folder)
            if os.path.isfile(os.path.join(garment_folder, f))
        ]

        if not garment_files:
            print(f"Error: No files found in {garment_folder}.")
            abort(400, description=f"No {garment_type.capitalize()} files found.")

        garment_file_path = garment_files[0]

        # Get the uploaded design file
        design_file = request.files["design"]
        upload_dir = os.path.join(base_path, "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        design_path = os.path.join(upload_dir, "uploaded_design.png")
        design_file.save(design_path)

        # Output directory for the modified image
        output_dir = os.path.join(base_path, "output")
        os.makedirs(output_dir, exist_ok=True)

        # Process the selected garment file
        try:
            with Image.open(garment_file_path) as background, Image.open(design_path) as design:
                # Ensure high quality by preserving original dimensions and DPI
                target_dpi = (600, 600)  # High-quality DPI
                design_dpi = design.info.get("dpi", target_dpi)
                background_dpi = background.info.get("dpi", target_dpi)

                # Convert both images to RGBA for transparency support
                background = background.convert("RGBA")
                design = design.convert("RGBA")

                # Debugging: Print image sizes
                print(f"Background size: {background.size}, DPI: {background_dpi}")
                print(f"Design size: {design.size}, DPI: {design_dpi}")

                # Get background dimensions
                bg_width, bg_height = background.size

                # Determine placement based on selected print type
                print_type = request.form.get("print_type")
                if print_type == "side":
                    # Make the design 10% smaller for Side print
                    design_width = int(design.width * 0.9)
                    design_height = int(design.height * 0.9)

                    # Adjusted Side Placement: Move 5% left and 2% down
                    center_x = int(bg_width * 0.70)  # 75% - 5% = 70%
                    center_y = int(bg_height * 0.32)  # 30% + 2% = 32%
                    x = center_x - (design_width // 2)
                    y = center_y - (design_height // 2)
                elif print_type == "front":
                    # Place the design at the center of the background
                    design_width = design.width
                    design_height = design.height
                    x = (bg_width - design_width) // 2
                    y = (bg_height - design_height) // 2
                else:
                    # Default to center if no valid print type is provided
                    design_width = design.width
                    design_height = design.height
                    x = (bg_width - design_width) // 2
                    y = (bg_height - design_height) // 2

                # Resize only if necessary to fit the background
                if design_width > bg_width or design_height > bg_height:
                    scale_factor = min(bg_width / design_width, bg_height / design_height)
                    design_width = int(design_width * scale_factor)
                    design_height = int(design_height * scale_factor)
                    design = design.resize((design_width, design_height), Image.Resampling.LANCZOS)

                # Debugging: Print final placement and size
                print(f"Design placement: (x: {x}, y: {y}), size: ({design_width}, {design_height})")

                # Paste the design onto the background
                composite = background.copy()
                composite.paste(design, (x, y), design)

                # Save the modified image with high DPI
                output_file_name = f"output_{os.path.basename(garment_file_path)}"
                output_file_path = os.path.join(output_dir, output_file_name)
                composite.save(output_file_path, "PNG", dpi=target_dpi)

                print(f"Output saved at: {output_file_path}")
        except Exception as e:
            print(f"Error during image processing: {e}")
            abort(500, description="Error processing images.")

        # Send the modified image back to the user
        return send_file(output_file_path, as_attachment=True)

    # Render the HTML form
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
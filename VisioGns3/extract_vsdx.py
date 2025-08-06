import zipfile
import os

# Function to get the latest .vsdx file and list of older files
def get_latest_vsdx_file():
    uploads_dir = os.path.expanduser("~/INDA/VisioGns3/uploads")

    # Ensure the uploads folder exists
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)

    # Get all .vsdx files in the uploads directory
    vsdx_files = [f for f in os.listdir(uploads_dir) if f.endswith(".vsdx")]

    # If no .vsdx files are found, return None
    if not vsdx_files:
        print("No .vsdx files found in uploads folder.")
        return None, []

    # Sort files by modification time (newest first)
    vsdx_files.sort(key=lambda f: os.path.getmtime(os.path.join(uploads_dir, f)), reverse=True)

    # The latest file
    latest_vsdx = os.path.join(uploads_dir, vsdx_files[0])

    # All other files are older
    older_files = [os.path.join(uploads_dir, f) for f in vsdx_files[1:]]

    return latest_vsdx, older_files

# Function to delete old .vsdx files
def clean_old_vsdx_files(older_files):
    for file in older_files:
        try:
            os.remove(file)
            print(f"Deleted old file: {file}")
        except Exception as e:
            print(f"Error deleting {file}: {e}")

def save_vsdx_path(vsdx_file):
    # Save the path of the latest VSDX file
    path = os.path.expanduser("~/INDA/VisioGns3/vsdx_path.txt")
    with open(path, "w") as file:
        file.write(vsdx_file)

def main():
    # Get the latest .vsdx file and list of older ones
    latest_vsdx, older_files = get_latest_vsdx_file()

    if not latest_vsdx:
        print("No VSDX file available for processing.")
        return

    # Delete all old .vsdx files (except the latest one)
    clean_old_vsdx_files(older_files)

    # Save the selected file path
    save_vsdx_path(latest_vsdx)

    # Directory to extract the contents
    extract_dir = os.path.expanduser("~/INDA/VisioGns3/extracted_vsdx")

    # Ensure the extraction directory exists
    os.makedirs(extract_dir, exist_ok=True)

    # Open and extract the latest .vsdx file
    with zipfile.ZipFile(latest_vsdx, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)

    print(f'XML files extracted to: {extract_dir}')

if __name__ == "__main__":
    main()


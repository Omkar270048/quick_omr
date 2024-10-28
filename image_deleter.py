import os

def delete_all_images(folder='uploads'):
    """
    Deletes all image files from the specified folder.

    Parameters:
    - folder (str): The folder from which to delete images. Defaults to 'uploads'.
    """
    # Define common image file extensions
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff')
    
    try:
        # List all files in the folder
        files = os.listdir(folder)
        
        # Iterate over the files and delete the ones with image extensions
        for filename in files:
            if filename.lower().endswith(image_extensions):
                file_path = os.path.join(folder, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"Deleted: {filename}")
        
        print("All images deleted successfully.")
    
    except Exception as e:
        print(f"An error occurred: {e}")

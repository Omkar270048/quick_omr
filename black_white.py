import cv2
import sys

def convert_to_black_and_white(input_path, output_path):
    """
    Convert a color image to black and white (binary) and save it to the specified output path.

    Parameters:
    input_path (str): The path to the input color image.
    output_path (str): The path to save the black and white image.
    threshold_value (int): The threshold value for binary conversion (0-255). Default is 127.
    """
    try:
        # Load the color image
        color_image = cv2.imread(input_path)

        if color_image is None:
            raise FileNotFoundError(f"Error: The file {input_path} was not found or could not be opened.")

        # Convert the color image to grayscale
        gray_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)

        # Apply binary thresholding
        _, bw_image = cv2.threshold(gray_image, 160, 255, cv2.THRESH_BINARY)

        # Save the black and white image
        cv2.imwrite(output_path, bw_image)
        print(f"Image successfully converted to black and white and saved to {output_path}.")

    except FileNotFoundError as e:
        print(e)
    except cv2.error as e:
        print(f"Error: There was an issue with OpenCV: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Example usage
    if len(sys.argv) not in [3, 4]:
        print("Usage: python image_converter_opencv.py <input_image_path> <output_image_path> [threshold_value]")
    else:
        input_path = sys.argv[1]
        output_path = sys.argv[2]
        threshold_value = int(sys.argv[3]) if len(sys.argv) == 4 else 127
        convert_to_black_and_white(input_path, output_path, threshold_value)

import cv2
import numpy as np
import pytesseract
import imutils

# Configure the path to the Tesseract executable
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_roi(image, roi_top, roi_bottom, roi_left, roi_right):
    """
    Extracts text from a Region of Interest (ROI) within the given image.

    :param image: Input image (as a numpy array).
    :param roi_top: Top boundary of the ROI.
    :param roi_bottom: Bottom boundary of the ROI.
    :param roi_left: Left boundary of the ROI.
    :param roi_right: Right boundary of the ROI.
    :return: Extracted text from the ROI.
    """
    roi = image[roi_top:roi_bottom, roi_left:roi_right]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = np.ones((1, 1), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    custom_config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(binary, config=custom_config)
    return text.strip()


def process_image(image_path):
    """
    Processes the image to extract text from specific ROIs and annotate the image.

    :param image_path: Path to the input image file.
    :return: Dictionary containing extracted text data.
    """
    image = cv2.imread(image_path)
    image = imutils.resize(image, height=700)

    left_roi = 287
    right_roi = 470
    name_roi_top = 86
    name_roi_bottom = 129
    # admission_roi_top = name_roi_bottom
    # admission_roi_bottom = 255
    # date_roi_top = admission_roi_bottom
    # date_roi_bottom = 285

    name = extract_text_from_roi(image, name_roi_top, name_roi_bottom, left_roi, right_roi)
    # admissionno = extract_text_from_roi(image, admission_roi_top, admission_roi_bottom, left_roi, right_roi)
    # date = extract_text_from_roi(image, date_roi_top, date_roi_bottom, left_roi, right_roi)

    cv2.rectangle(image, (left_roi, name_roi_top), (right_roi, name_roi_bottom), (0, 255, 0), 2)
    # cv2.rectangle(image, (left_roi, admission_roi_top), (right_roi, admission_roi_bottom), (0, 255, 0), 2)
    # cv2.rectangle(image, (left_roi, date_roi_top), (right_roi, date_roi_bottom), (0, 255, 0), 2)

    # cv2.imwrite("annotated_image.png", image)

    return {
        "name": name,
        # "admissionno": admissionno,
        # "date": date
    }

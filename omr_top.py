import cv2
import numpy as np
import imutils

# gt = 0

def preprocess_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    equalized = cv2.equalizeHist(gray)
    blurred = cv2.GaussianBlur(equalized, (9, 9), 2)
    edges = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    return edges

def detect_circles_in_rectangle(image, x, y, w, h):
    admission_no = ''
    roi_image = image[y:y+h, x:x+w]
    gray = cv2.cvtColor(roi_image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (9, 9), 2)
    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=30,
        param1=50,
        param2=30,
        minRadius=10,
        maxRadius=20
    )

    circle_data = []
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for circle in circles[0, :]:
            center_x = circle[0] + x
            center_y = circle[1] + y
            radius = circle[2]

            circle_data.append({
                'x': center_x - radius,
                'y': center_y - radius,
                'w': 2 * radius,
                'h': 2 * radius,
            })

    circle_data.sort(key=lambda c: (c['y'], c['x']))

    if circle_data:
        min_x = min(c['x'] for c in circle_data)
        max_x = max(c['x'] + c['w'] for c in circle_data)
        min_y = min(c['y'] for c in circle_data)
        max_y = max(c['y'] + c['h'] for c in circle_data)

        bounding_w = max_x - min_x
        bounding_h = max_y - min_y

        # Draw rectangle around all detected circles on the original image
        cv2.rectangle(image, (min_x, min_y), (min_x + bounding_w, min_y + bounding_h), (255, 0, 0), 2)  # Blue rectangle

        # Draw grid within the bounding rectangle
        grid_cols, grid_rows = 8, 10
        cell_w = bounding_w // grid_cols
        cell_h = bounding_h // grid_rows

        # Draw vertical lines
        for i in range(grid_cols + 1):
            x_coord = min_x + i * cell_w
            cv2.line(image, (x_coord, min_y), (x_coord, min_y + bounding_h), (0, 255, 0), 1)  # Green vertical lines

        # Draw horizontal lines
        for i in range(grid_rows + 1):
            y_coord = min_y + i * cell_h
            cv2.line(image, (min_x, y_coord), (min_x + bounding_w, y_coord), (0, 255, 0), 1)  # Green horizontal lines

        # Detect mean intensity of each cell and annotate with text
        threshold = 170  # Threshold to differentiate black and white
        for col in range(grid_cols):
            col_start_x = min_x + col * cell_w
            col_end_x = col_start_x + cell_w
            
            for row in range(grid_rows):
                row_start_y = min_y + row * cell_h
                row_end_y = row_start_y + cell_h
                
                # Extract cell region
                cell = image[row_start_y:row_end_y, col_start_x:col_end_x]
                
                # Calculate mean intensity
                cell_gray = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)
                cell_mean_intensity = np.mean(cell_gray)
                
                # Determine text to display
                text = "black" if cell_mean_intensity < threshold else "white"
                
                # Annotate the cell with text
                text_position = (col_start_x + 5, row_start_y + cell_h // 2)  # Adjust text position as needed
                cv2.putText(image, text, text_position, cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1, cv2.LINE_AA)

                # Append column-row indices for black cells to admission_no
                if cell_mean_intensity < threshold:
                    admission_no += f"{row}"

    return image, admission_no

def adjust_rectangle_coordinates(img_w, img_h):
    if img_w / img_h <= 0.720:
        x, y = 130, 340
        w, h = 300, 400
    else:
        x, y = 140, 295
        w, h = 350, 500
    return x, y, w, h

def draw_largest_rectangle_and_circles(image):
    img_h, img_w = image.shape[:2]
    x, y, w, h = adjust_rectangle_coordinates(img_w, img_h)
    
    # Draw the rectangle in red on the original image
    cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)

    # Detect and draw circles within the specified rectangle on the original image
    image, admission_no = detect_circles_in_rectangle(image, x, y, w, h)

    return admission_no

def process_image(image_path):
    image = cv2.imread(image_path)
    
    if image is None:
        print(f"Error: Unable to load image at {image_path}")
        return None
    
    image = imutils.resize(image, height=1600)
    img_h, img_w = image.shape[:2]

    # Detect the largest rectangle, circles, and high-intensity cells
    admission_no = draw_largest_rectangle_and_circles(image)

    # Save the result
    # global gt
    # cv2.imwrite(f"top{gt}.png", image)
    # gt += 1

    return admission_no

# Example usage
# if __name__ == "__main__":
#     image_path = "your_image_path_here.jpg"  # Replace with your image path
#     admission_no = process_image(image_path)
#     print(f"Admission Number: {admission_no}")

import cv2
import imutils
import numpy as np
from collections import Counter

gt = 0  

def preprocess_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    equalized = cv2.equalizeHist(gray)
    blurred = cv2.GaussianBlur(equalized, (5, 5), 0)
    edges = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    return edges

def find_rectangles(edges):
    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    rectangles = []
    for contour in contours:
        epsilon = 0.04 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        if len(approx) == 4:
            area = cv2.contourArea(contour)
            if area > 500:  # Adjust minimum area threshold if needed
                rectangles.append((approx, area))
    rectangles.sort(key=lambda x: x[1], reverse=True)
    return rectangles

def draw_rectangles(image, rectangles, roi_top, roi_bottom):
    blue_contour = None
    bounding_box = None
    largest_area = 0
    for rect in rectangles:
        contour, area = rect
        x, y, w, h = cv2.boundingRect(contour)
        if y + h > roi_top and y < roi_bottom:
            if area > largest_area:
                largest_area = area
                blue_contour = contour
                bounding_box = (x, y, w, h)

    if blue_contour is not None and bounding_box is not None:
        cv2.drawContours(image, [blue_contour], -1, (255, 0, 0), 2)
        x, y, w, h = bounding_box
        text = f"X: {x}, Y: {y}, W: {w}, H: {h}"
        cv2.putText(image, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    return blue_contour, bounding_box

def adjust_coordinates_based_on_aspect_ratio(img_w, img_h):
    if img_w / img_h <= 0.720:
        fx, fy = 120, 790  # Top-left corner coordinates
        fw, fh = 978, 685
    else:
        fx, fy = 140, 840  # Top-left corner coordinates
        fw, fh = 1027, 725  # Width and height of the rectangle
    return fx, fy, fw, fh

def divide_contour_into_columns(bounding_box, fx, fy, fw, fh, num_columns=5):
    column_width = fw // num_columns
    columns = []

    for i in range(num_columns):
        roi_left = fx + i * column_width
        roi_right = fx + (i + 1) * column_width if i < num_columns - 1 else fx + fw
        columns.append((roi_left, roi_right, fy, fy + fh))

    return columns

def detect_circles_in_region(image, roi_left, roi_right, roi_top, roi_bottom):
    roi_image = image[roi_top:roi_bottom, roi_left:roi_right]
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
            center = (circle[0] + roi_left, circle[1] + roi_top)
            radius = circle[2]

            # No filled or ring-like circle detection here
            cv2.circle(image, center, radius, (0, 255, 0), 2)  # Green for circles
            cv2.circle(image, center, 2, (0, 255, 0), 3)

            circle_data.append({
                'center_x': center[0],
                'center_y': center[1],
                'radius': radius
            })

    circle_data.sort(key=lambda x: (x['center_y'], x['center_x']))

    adjusted_circle_data = []
    for i in range(0, len(circle_data), 4):
        group = circle_data[i:i + 4]
        if len(group) < 4:
            adjusted_circle_data.extend(group)
            continue

        y_values = [circle['center_y'] for circle in group]
        most_common_y = Counter(y_values).most_common(1)[0][0]

        for circle in group:
            circle['center_y'] = most_common_y
            adjusted_circle_data.append(circle)

    adjusted_circle_data.sort(key=lambda x: (x['center_y'], x['center_x']))

    return adjusted_circle_data

def draw_continuous_boxes_around_circles(image, circles):
    if not circles:
        return

    min_x = min(circle['center_x'] - circle['radius'] for circle in circles)
    max_x = max(circle['center_x'] + circle['radius'] for circle in circles)
    min_y = min(circle['center_y'] - circle['radius'] for circle in circles)
    max_y = max(circle['center_y'] + circle['radius'] for circle in circles)

    cv2.rectangle(image, (min_x, min_y), (max_x, max_y), (255, 0, 0), 2)  # Blue box

def draw_grid_on_region(image, circles):
    global ans_index_list
    if not circles:
        return

    min_x = min(circle['center_x'] - circle['radius'] for circle in circles)
    max_x = max(circle['center_x'] + circle['radius'] for circle in circles)
    min_y = min(circle['center_y'] - circle['radius'] for circle in circles)
    max_y = max(circle['center_y'] + circle['radius'] for circle in circles)

    grid_width = max_x - min_x
    grid_height = max_y - min_y
    num_columns = 4
    num_rows = 20
    cell_width = grid_width // num_columns
    cell_height = grid_height // num_rows

    intensities = []
    cell_data = []  # List to store intensity and color labels for cells

    for i in range(num_columns + 1):
        x = min_x + i * cell_width
        cv2.line(image, (x, min_y), (x, max_y), (0, 0, 255), 1)  # Red lines

    for i in range(num_rows + 1):
        y = min_y + i * cell_height
        cv2.line(image, (min_x, y), (max_x, y), (0, 0, 255), 1)  # Red lines

    # Define a threshold to distinguish between black and white
    intensity_threshold = 150  # This value can be adjusted

    for row in range(num_rows):
        for col in range(num_columns):
            roi_left = min_x + col * cell_width
            roi_right = roi_left + cell_width
            roi_top = min_y + row * cell_height
            roi_bottom = roi_top + cell_height

            # Extract the ROI from the image
            cell_roi = image[roi_top:roi_bottom, roi_left:roi_right]
            
            # Calculate the average intensity of the cell
            gray_cell_roi = cv2.cvtColor(cell_roi, cv2.COLOR_BGR2GRAY)
            mean_intensity = np.mean(gray_cell_roi)
            
            color_label = "White" if mean_intensity > intensity_threshold else "Black"
            
            # Append the data to the list
            cell_data.append({
                'roi': (roi_left, roi_right, roi_top, roi_bottom),
                'mean_intensity': mean_intensity,
                'color_label': color_label
            })

            # Draw a rectangle around each cell and display intensity
            cv2.rectangle(image, (roi_left, roi_top), (roi_right, roi_bottom), (0, 255, 0), 1)  # Green box
            cv2.putText(image, color_label, (roi_left + 5, roi_top + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1, cv2.LINE_AA)


    # Process cell data in groups of 4
    global ans_index_list
    # print("Region Detected")
    for i in range(0, len(cell_data), 4):
        group = cell_data[i:i + 4]
        group_index = i // 4 + 1
        black_indices = [i + j + 1 for j, cell in enumerate(group) if cell['color_label'] == "Black"]

        if len(black_indices) > 1:
            answer[group_index] = None
        elif len(black_indices) == 1:
            answer[group_index] = black_indices[0]
        else:
            answer[group_index] = None

        # Print the result for verification
        # print(f"Group {group_index}:")
        # for cell_index, cell in enumerate(group):
            # print(f"  Cell {i + cell_index + 1}: {cell['color_label']} (Intensity: {cell['mean_intensity']:.2f})")
        ans = answer.get(group_index, None)
        if ans is not None:
            ans_pos = ans % 4
            if ans_pos == 0:
                ans_pos = 4
            ans_index_list.append(ans_pos)
            # print(f"Answer for Group {group_index}: {ans_pos}")
        else:
            ans_index_list.append(None)
            # print(f"Answer for Group {group_index}: None")

    return cell_data


def process_image(image_path):
    global gt  # Declare gt as global here
    global ans_index_list, answer

    # Reset global variables
    answer = {}
    ans_index_list = []

    # Rest of the code remains the same
    image = cv2.imread(image_path)
    image = imutils.resize(image, height=1600)
    image_copy = image.copy()  # Keep a copy for drawing boxes without detecting circles

    if image is None:
        # print("Error: Image not found.")
        return

    height, width = image.shape[:2]
    img_w, img_h = width, height
    fx, fy, fw, fh = adjust_coordinates_based_on_aspect_ratio(img_w, img_h)

    edges = preprocess_image(image)
    rectangles = find_rectangles(edges)

    if not rectangles:
        # print("No rectangles found.")
        return

    roi_bottom = (height - 1)
    roi_top = ((height // 2) - 50)
    cv2.rectangle(image, (0, roi_top), (width, roi_bottom), (0, 255, 0), 2)

    blue_contour, bounding_box = draw_rectangles(image, rectangles, roi_top, roi_bottom)

    if blue_contour is not None and bounding_box is not None:
        columns = divide_contour_into_columns(bounding_box, fx, fy, fw, fh)
        for i, region in enumerate(columns):
            roi_left, roi_right, roi_top, roi_bottom = region
            cv2.rectangle(image, (roi_left, roi_top), (roi_right, roi_bottom), (255, 0, 255), 2)

            circle_data = detect_circles_in_region(image, roi_left, roi_right, roi_top, roi_bottom)
            draw_continuous_boxes_around_circles(image, circle_data)
            draw_continuous_boxes_around_circles(image_copy, circle_data)
            draw_grid_on_region(image_copy, circle_data)

            # for index, circle in enumerate(circle_data):
            #     x, y = circle['center_x'], circle['center_y']
            #     text = str(index + 1)
            #     cv2.putText(image, text, (x - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)

    # print("----------------------")
    for i, ans in enumerate(ans_index_list):
    #     print(i+1, ans)
        answer[i+1] = ans

        #this code is new

    # print("----------------------")
    # cv2.imwrite(f"output_copy{gt}.png", image_copy)
    # cv2.imwrite(f"output_{gt}.png", image)
    # gt += 1


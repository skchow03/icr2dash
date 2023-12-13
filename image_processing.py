from PIL import Image
import numpy as np

def is_in_cockpit_view(cropped_screenshot, pixel_color_mapping, tolerance=3):
    """
    Checks if the cropped screenshot is in the cockpit view based on specific pixel colors with a tolerance.
    """
    
    def is_color_close(color1, color2, tol):
        return all(abs(c1 - c2) <= tol for c1, c2 in zip(color1, color2))

    for coord, expected_color in pixel_color_mapping.items():
        pixel_color = cropped_screenshot.getpixel(coord)
        if not is_color_close(pixel_color[:3], expected_color, tolerance):  # Compare only RGB values, ignore alpha if present
            return False
    return True


def resize_image(image, width, height):
    img = image.resize((width, height), Image.NEAREST)
    return img

def crop_to_aspect_ratio(image, aspect_ratio=4/3):
    # Calculate the aspect ratio of the given image
    img_width, img_height = image.size
    img_aspect = img_width / img_height

    # If it's already roughly 4:3, return the image as-is
    print (img_aspect)
    if 1.325 < img_aspect < 1.335:
        return image

    # Otherwise, adjust the image to fit 4:3
    if img_aspect > aspect_ratio:  # Too wide
        new_width = int(img_height * aspect_ratio)
        left = (img_width - new_width) // 2
        return image.crop((left, 0, left + new_width, img_height))
    else:  # Too tall
        new_height = int(img_width / aspect_ratio)
        top = (img_height - new_height) // 2
        return image.crop((0, top, img_width, top + new_height))

def crop_black_borders_with_coords(image):
    # Convert image to grayscale
    grayscale = image.convert("L")
    
    # Convert to numpy array and find non-black rows and columns
    np_img = np.array(grayscale)
    non_empty_columns = np.where(np_img.max(axis=0) > 0)[0]
    non_empty_rows = np.where(np_img.max(axis=1) > 0)[0]
    
    # Calculate cropping box
    if non_empty_rows.size and non_empty_columns.size:
        crop_box = (
            min(non_empty_columns),
            min(non_empty_rows),
            max(non_empty_columns) + 1,
            max(non_empty_rows) + 1,
        )
        cropped_image = image.crop(crop_box)
        #cropped_image = crop_to_aspect_ratio(cropped_image)
        resized_image = resize_image(cropped_image, 1280, 960)
        return resized_image, crop_box

    image = resize_image(image, 1280, 960)
    return image, (0, 0, image.width, image.height)

def overlay_rotated_needle(cockpit_img, needle_img_path, angle, position):
    """
    Overlays a rotated gauge needle onto the cockpit image.
    """
    
    # Load the needle image
    needle_img = Image.open(needle_img_path).convert('RGBA')
    
    # Calculate the center of the needle image
    center_x, center_y = needle_img.size[0] // 2, needle_img.size[1] // 2
    
    # Rotate the needle image around its center
    rotated_needle = needle_img.rotate(-angle, resample=Image.BICUBIC, center=(center_x, center_y))
    
    # Calculate the offset introduced by the rotation
    offset_x = position[0] - center_x
    offset_y = position[1] - center_y
    
    # Paste the rotated needle onto the cockpit image at the adjusted position
    cockpit_img.paste(rotated_needle, (offset_x, offset_y), mask=rotated_needle)
    
    return cockpit_img



import os
from PIL import Image
import openai
import numpy as np
import cv2
import requests
from datetime import datetime


# Set your OpenAI API key
openai.api_key = ""

def open_file_explorer():
    try:
        from tkinter import Tk
        from tkinter.filedialog import askopenfilename
    except ImportError:
        raise ImportError("Please install tkinter to run this script.")

    root = Tk()
    root.withdraw()
    file_path = askopenfilename(filetypes=[("PNG Images", "*.png")])
    return file_path

def process_image(image_path):
    # Step 1: Create a blank image
    original_image = Image.open(image_path)
    new_width = original_image.width + 150
    new_image = Image.new("RGBA", (new_width, original_image.height), (255, 255, 255, 0))

    # Step 2: Paste the original image in the top left corner
    new_image.paste(original_image, (0, 0))

    # Step 3: Copy left 50 pixels and paste on the top right
    left_50_pixels = new_image.crop((0, 0, 50, original_image.height))
    new_image.paste(left_50_pixels, (original_image.width + 100, 0))

    # resize image
    np_image=np.array(new_image)
    res = cv2.resize(np_image, dsize=(original_image.size), interpolation=cv2.INTER_LINEAR)
    resized_img = Image.fromarray(res)

    # Step 4: Save the mask image
    mask_image_path = os.path.splitext(image_path)[0] + "_mask.png"
    resized_img.save(mask_image_path)

    # Step 5: Save the image with "_image" added to the filename
    image_with_suffix_path = os.path.splitext(image_path)[0] + "_image.png"
    resized_img.save(image_with_suffix_path)

    return mask_image_path, image_with_suffix_path


def seamless_edit(image_path, mask_image_path):
    # Step 6: Use OpenAI API to call openai.Image.create_edit with the two images
    response = openai.Image.create_edit(
        image=open(image_path, 'rb'),
        mask=open(mask_image_path, 'rb'),
        prompt="hawaiian flower shirt pattern",
        n=1,
        size="512x512"
    )
    image_url = response['data'][0]['url']
    print(image_url)

    image_data = requests.get(image_url).content

    # Save the image as a PNG file
    side_image_path = os.path.splitext(image_path)[0] + "_side.png"
    with open(side_image_path, "wb") as f:
        f.write(image_data)

    print(f"Image saved as {side_image_path}")
    return side_image_path

if __name__ == "__main__":
    # Open file explorer and get the selected PNG image path
    image_path = open_file_explorer()

    if image_path:
        original_img = Image.open(image_path)
        # Process the image and get the mask and image with suffix paths
        mask_path, image_with_suffix_path = process_image(image_path)

        # Perform seamless side edit using OpenAI API
        side_seamless = seamless_edit(image_with_suffix_path, mask_path)
        os.remove(image_with_suffix_path)
        os.remove(mask_path)
        
        opened_img = Image.open(side_seamless)
        rotated = opened_img.rotate(90)
        rotated_image_path = os.path.splitext(image_path)[0] + "_rotated.png"
        rotated.save(rotated_image_path)

        mask_path, image_with_suffix_path = process_image(rotated_image_path)

        # Perform seamless side edit using OpenAI API
        final_seamless = seamless_edit(image_with_suffix_path, mask_path)
        os.remove(image_with_suffix_path)
        os.remove(mask_path)
        os.remove(side_seamless)
        os.remove(rotated_image_path)

        opened_img = Image.open(final_seamless)

        np_image=np.array(opened_img)
        res = cv2.resize(np_image, dsize=(original_img.height + 150, original_img.width + 150), interpolation=cv2.INTER_LINEAR)
        resized_img = Image.fromarray(res)
        resized_image_path = os.path.splitext(image_path)[0] + "_resized.png"
        resized_img.save(resized_image_path)

        rotated = resized_img.rotate(270)

        final_img = Image.new("RGBA", (original_img.width + 100, original_img.height + 100), (255, 255, 255, 0))
        final_section = rotated.crop((0, 0, original_img.width + 100, original_img.height + 100))
        final_img.paste(final_section, (0, 0))
        np_image=np.array(final_img)
        res = cv2.resize(np_image, dsize=(original_img.height, original_img.width), interpolation=cv2.INTER_LINEAR)
        final_img = Image.fromarray(res)
        save_directory = "E:\stable_diffusion_project\generated images"
        os.remove(resized_image_path)

        # Create the directory if it doesn't exist
        os.makedirs(save_directory, exist_ok=True)

        # Generate a unique filename using the current timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"final_image_{timestamp}.png"

        # Combine the directory and file name
        save_path = os.path.join(save_directory, file_name)

        final_img.save(save_path)
        os.remove(final_seamless)
        
    else:
        print("No image selected.")

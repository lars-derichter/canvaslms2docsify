import os
import re
import logging
import shutil
from canvasapi import Canvas
from canvasapi.exceptions import ResourceDoesNotExist
from panflute import *

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set environment variables or use default values
api_endpoint = os.getenv("API_ENDPOINT", "https://canvas.instructure.com")
auth_token = os.getenv("AUTH_TOKEN", "YOUR_AUTH")
course_id = os.getenv("COURSE_ID", "YOUR_COURSE_ID")
output_dir = os.getenv("OUTPUT_DIR", "docs")

# Helper functions
def sanitize_name(name):
    name = re.sub(r'[^a-zA-Z0-9\s]', '', name)
    name = re.sub(r'\s+', '-', name.strip()).lower()
    return name

def get_images(content, download_directory):
    image_ids = re.findall(r'/files/(\d+)', content)
    for image_id in image_ids:
        try:
            logging.info(f"Attempting to download image with ID: {image_id}")
            image = course.get_file(image_id)
            image_name = sanitize_name(image.display_name)
            image_path = os.path.join(download_directory, image_name)
            
            if not os.path.exists(image_path):
                logging.info(f"Downloading image: {image_name}")
                image.download(image_path)
            else:
                logging.info(f"Image already exists: {image_path}")
            
            image_alt = re.sub(r'\..*$', '', image_name)
            content = re.sub(r'<img.*?src=".*?/files/' + image_id + '".*?>', f'<img src="{image_name}" alt="{image_alt}" />', content)
        
        except ResourceDoesNotExist:
            logging.error(f"File with ID {image_id} not found in course {course_id}. Skipping this image.")
            continue  # Skip to the next image if this one fails
    
    return content

def content_to_markdown(content, title):
    markdown_content = f"# {title}\n\n"
    markdown_content += convert_text(content, input_format="html", output_format="gfm")
    return markdown_content

def save_content_to_file(content, file_path):
    with open(file_path, "w") as file:
        file.write(content)
    logging.info(f"Saved content to: {file_path}")

def process_module_item(module_item, directory_path, counter, current_depth):
    module_item_title = module_item.title
    logging.info(f"Processing module item: {module_item_title}")
    
    file_path = os.path.join(directory_path, f"{counter:02d}-{sanitize_name(module_item_title)}.md")
    module_item_type = module_item.type
    
    if module_item_type == "Page":
        page = course.get_page(module_item.page_url)
        content = get_images(page.body, directory_path)
        markdown_content = content_to_markdown(content, module_item_title)
        save_content_to_file(markdown_content, file_path)
        return file_path, module_item_title, current_depth
    
    elif module_item_type == "Assignment":
        assignment = course.get_assignment(module_item.content_id)
        content = get_images(assignment.description, directory_path)
        markdown_content = content_to_markdown(content, module_item_title)
        save_content_to_file(markdown_content, file_path)
        return file_path, module_item_title, current_depth
    
    elif module_item_type == "ExternalUrl":
        content = f'[Link naar {module_item_title}]({module_item.external_url})'
        save_content_to_file(content, file_path)
        return file_path, module_item_title, current_depth
    
    elif module_item_type == "SubHeader":
        # For subheaders, no file is created; only add a non-link list item to the index.
        current_depth = 2  # Set depth to 2 after encountering a SubHeader
        counter -= 1 # Decrement counter to avoid skipping a number in the file name
        return None, f'{module_item_title}', current_depth
    
    else:
        logging.warning(f"Module item type not supported: {module_item_type}")
        counter -= 1 # Decrement counter to avoid skipping a number in the file name
        return None, None, current_depth

def get_relative_path(file_path):
    return os.path.relpath(file_path, output_dir)

# Main script
canvas = Canvas(api_endpoint, auth_token)
course = canvas.get_course(course_id)
logging.info(f"Course Name: {course.name}")

content_index = f'- [{course.name}](/)\n'

modules = course.get_modules()
for module in modules:
    directory_name = sanitize_name(module.name)
    directory_path = os.path.join(output_dir, directory_name)
    os.makedirs(directory_path, exist_ok=True)
    
    logging.info(f"Processing module: {module.name}")
    content_index += f'- {module.name}\n'
    
    module_items = module.get_module_items()
    current_depth = 1  # Initialize depth at the start of each module
    
    for counter, module_item in enumerate(module_items, 1):
        file_path, item_title, current_depth = process_module_item(module_item, directory_path, counter, current_depth)
        if item_title:
            if file_path:
                relative_file_path = get_relative_path(file_path)
                content_index += f'{"    " * current_depth}- [{item_title}]({relative_file_path})\n'
            else:
                content_index += f'    - {item_title}\n' # Add a non-link list item for SubHeader

save_content_to_file(content_index, os.path.join(output_dir, "_sidebar.md"))

# copy inex.html from template to output_dir
shutil.copyfile("templates/index.html", os.path.join(output_dir, "index.html"))
# create .nojekyll to prevent GitHub Pages from ignoring files starting with an underscore
with open(os.path.join(output_dir, ".nojekyll"), "w") as file:
    pass    

logging.info("Script completed successfully.")

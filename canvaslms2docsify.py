import os
import re
import logging
import shutil
import pystache
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
template_dir = os.getenv("TEMPLATE_DIR", "template")

# Helper functions
def sanitize_name(name):
    return re.sub(r'\s+', '-', re.sub(r'[^a-zA-Z0-9\s]', '', name.strip()).lower())

def markdownify_name(name):
    markdown_name = re.sub(r'([*_`])', r'\\\1', name)
    markdown_name = re.sub(r'(\d+)\. ', r'\1\\. ', markdown_name)
    return markdown_name

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
            continue
    
    return content

def content_to_markdown(content, title):
    return f"# {title}\n\n{convert_text(content, input_format='html', output_format='gfm')}"

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
        current_depth = 1
        return None, module_item_title, current_depth
    
    else:
        logging.warning(f"Module item type not supported: {module_item_type}")
        return None, None, current_depth

def get_relative_path(file_path, base_directory):
    return os.path.relpath(file_path, base_directory)

def copy_template_directory(template_directory, output_directory, context):
    try:
        if os.path.exists(template_directory):
            for root, dirs, files in os.walk(template_directory):
                relative_path = os.path.relpath(root, template_directory)
                dest_dir = os.path.join(output_directory, relative_path)
                os.makedirs(dest_dir, exist_ok=True)
                
                for file_name in files:
                    template_file_path = os.path.join(root, file_name)
                    
                    if file_name.endswith('.tmpl'):
                        logging.info(f"Processing template file: {template_file_path}")
                        with open(template_file_path, 'r') as template_file:
                            template_content = template_file.read()
                        
                        rendered_content = pystache.render(template_content, context)
                        output_file_path = os.path.join(dest_dir, file_name[:-5])
                        with open(output_file_path, 'w') as output_file:
                            output_file.write(rendered_content)
                        logging.info(f"Rendered template saved to: {output_file_path}")
                    
                    else:
                        shutil.copy2(template_file_path, dest_dir)
                        logging.info(f"Copied file: {template_file_path} to {dest_dir}")
        else:
            logging.error(f"Template directory {template_directory} does not exist. Skipping copy.")
    except Exception as e:
        logging.error(f"Error copying template directory: {e}")

def generate_sidebars(modules_info, output_dir, course_name, course_index_path):
    root_sidebar_path = os.path.join(output_dir, "_sidebar.md")
    root_content = f"- [{course_name}]({get_relative_path(course_index_path, output_dir)})\n"
    
    for module_name, module_info in modules_info.items():
        if module_info['pages']:
            first_page_path = module_info['pages'][0]['relative_path']
            if first_page_path:
                root_content += f"- [{module_name}]({get_relative_path(first_page_path, output_dir)})\n"
            else:
                root_content += f"- {module_name}\n"
        else:
            root_content += f"- {module_name}\n"

    save_content_to_file(root_content, root_sidebar_path)

    for module_name, module_info in modules_info.items():
        module_sidebar_path = os.path.join(module_info['directory'], "_sidebar.md")
        module_content = f"- [{course_name}]({get_relative_path(course_index_path, module_info['directory'])})\n"

        for other_module_name, other_module_info in modules_info.items():
            if other_module_name != module_name:
                if other_module_info['pages']:
                    first_page_path = other_module_info['pages'][0]['relative_path']
                    if first_page_path:
                        module_content += f"- [{other_module_name}]({get_relative_path(first_page_path, module_info['directory'])})\n"
                    else:
                        module_content += f"- {other_module_name}\n"
                else:
                    module_content += f"- {other_module_name}\n"
        
        module_content += f"\n- {module_name}\n"
        for page_info in module_info['pages']:
            if page_info['relative_path']:
                module_content += f"{'    ' * page_info['depth']}- [{page_info['title']}]({get_relative_path(page_info['relative_path'], module_info['directory'])})\n"
            else:
                module_content += f"{'    ' * page_info['depth']}- {page_info['title']}\n"
        
        save_content_to_file(module_content, module_sidebar_path)

# Main script

canvas = Canvas(api_endpoint, auth_token)
course = canvas.get_course(course_id)
logging.info(f"Course Name: {course.name}")

context = {
    'course_name': course.name,
    'api_endpoint': api_endpoint,
}

modules_info = {}
course_index_path = os.path.join(output_dir, "_index.md")

modules = course.get_modules()
for module in modules:
    directory_name = sanitize_name(module.name)
    directory_path = os.path.join(output_dir, directory_name)
    os.makedirs(directory_path, exist_ok=True)
    
    logging.info(f"Processing module: {module.name}")
    
    module_items = module.get_module_items()
    current_depth = 1

    counter = 1
    module_pages = []
    
    for module_item in module_items:
        file_path, module_item_title, current_depth = process_module_item(module_item, directory_path, counter, current_depth)
        if module_item_title:
            if file_path:
                relative_file_path = get_relative_path(file_path, directory_path)
                module_pages.append({
                    'title': module_item_title,
                    'relative_path': relative_file_path,
                    'depth': current_depth - 1
                })
                current_depth = 2
                counter += 1
            else:
                module_pages.append({
                    'title': module_item_title,
                    'relative_path': None,
                    'depth': current_depth - 1
                })
                current_depth = 2
    
    modules_info[module.name] = {
        'directory': directory_path,
        'pages': module_pages
    }

# Generate _sidebar.md files
generate_sidebars(modules_info, output_dir, course.name, course_index_path)

# Copy the contents of the template directory to the output directory, processing .tmpl files
copy_template_directory(template_dir, output_dir, context)

logging.info("Script completed successfully.")

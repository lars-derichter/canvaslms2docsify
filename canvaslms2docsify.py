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

# New function to generate module-specific sidebars
def generate_sidebars_from_index(index_file, output_dir):
    with open(index_file, 'r') as f:
        lines = f.readlines()
    
    module_links = {}
    current_module = None

    for line in lines:
        indent_level = len(line) - len(line.lstrip())
        if indent_level == 0 and line.startswith('- '):
            # Top-level module link
            match = re.match(r'- \[(.*?)\]\((.*?)\)', line)
            if match:
                module_name, link = match.groups()
                module_links[module_name] = {'first_page': link, 'pages': [], 'raw_lines': [line]}
                current_module = module_name
            else:
                module_links[line.strip('- ').strip()] = {'first_page': None, 'pages': [], 'raw_lines': [line]}
                current_module = line.strip('- ').strip()
        elif current_module:
            # Subheader or page link
            module_links[current_module]['raw_lines'].append(line)
            if indent_level > 0 and ']' in line:
                module_links[current_module]['pages'].append(line.strip())
    
    # Generate root _sidebar.md
    root_sidebar = '- [Course Home](_index.md)\n'
    for module_name, info in module_links.items():
        if info['first_page']:
            root_sidebar += f'- [{module_name}]({info["first_page"]})\n'
    
    save_content_to_file(root_sidebar, os.path.join(output_dir, '_sidebar.md'))
    
    # Generate module-specific _sidebar.md files
    for module_name, info in module_links.items():
        module_dir = os.path.join(output_dir, sanitize_name(module_name))
        if not os.path.exists(module_dir):
            continue

        sidebar_content = '- [Course Home](_index.md)\n'
        
        for other_module_name, other_info in module_links.items():
            if other_module_name != module_name:
                if other_info['first_page']:
                    sidebar_content += f'- [{other_module_name}](../{sanitize_name(other_module_name)}/{other_info["first_page"]})\n'
                else:
                    sidebar_content += f'- {other_module_name}\n'
        
        # Add localized content for the current module
        sidebar_content += '\n'.join(info['raw_lines'])
        sidebar_content = re.sub(r'\(' + re.escape(sanitize_name(module_name)) + r'/', '(', sidebar_content)

        save_content_to_file(sidebar_content, os.path.join(module_dir, '_sidebar.md'))

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
    for module_item in module_items:
        file_path, module_item_title, current_depth = process_module_item(module_item, directory_path, counter, current_depth)
        if module_item_title:
            if file_path:
                relative_file_path = get_relative_path(file_path)
                content_index += f'{"    " * current_depth}- [{item_title}]({relative_file_path})\n'
                current_depth = 2
                counter += 1
            else:
                content_index += f'    - {item_title}\n'
                current_depth = 2

index_file_path = os.path.join(output_dir, "_index.md")
save_content_to_file(content_index, index_file_path)

# Generate _sidebar.md files based on _index.md
generate_sidebars_from_index(index_file_path, output_dir)

# Copy the contents of the template directory to the output directory, processing .tmpl files
copy_template_directory(template_dir, output_dir, context)

logging.info("Script completed successfully.")

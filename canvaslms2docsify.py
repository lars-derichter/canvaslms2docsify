import os
import re
from canvasapi import Canvas
from panflute import *

# Define the LMS API endpoint and authentication token
api_endpoint = os.environ.get("API_ENDPOINT") 
auth_token = os.environ.get("AUTH_TOKEN")

# Define the course ID
course_id = os.environ.get("COURSE_ID") 

# Define the directory where the markdown files will be saved
output_dir = os.environ.get("OUTPUT_DIR")

# Initialize a new Canvas object
canvas = Canvas(api_endpoint, auth_token)

# Get the course object
course = canvas.get_course(course_id)

# Get the course name
course_name = course.name

print(f"Course Name: {course_name}")

# Get the course modules
modules = course.get_modules()

# Function to sanitize module names
def sanitize_module_name(module_name):
    # Remove special characters
    module_name = re.sub(r'[^a-zA-Z0-9\s]', '', module_name)
    # Replace spaces with underscores
    module_name = module_name.replace(" ", "_")
    return module_name

# Loop through each module
for module in modules:
    # Get the module name
    module_name = module.name

    # Sanitize the module name
    directory_name = sanitize_module_name(module_name)
    # strip leading and trailing underscores
    directory_name = directory_name.strip('_')
    directory_path = os.path.join(output_dir, directory_name)

    # Create the directory if it does not exist
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f"Created directory: {directory_path}")
    else:
        print(f"Directory already exists: {directory_path}")

    # Get the module items
    module_items = module.get_module_items()

    # Loop through each module item
    for module_item in module_items:
        # Get the module item title
        module_item_title = module_item.title
        print(f"Module Item Title: {module_item_title}")

        # Get the module item type
        module_item_type = module_item.type
        print(f"    Module Item Type: {module_item_type}")

        # If it is a page get its content
        if module_item_type == "Page":
            module_item_page_url = module_item.page_url
            print(f"      Module Item Page URL: {module_item_page_url}")
            page = course.get_page(module_item_page_url)
            content = page.body

        # If it is an assignment get its content
        elif module_item_type == "Assignment":
            module_item_assignment_id = module_item.content_id
            assignment = course.get_assignment(module_item_assignment_id)
            content = assignment.description

        # Check if the content contains any images
        if '<img' in content:
            # Get the images data-api-endpoint file numbers
            image_ids = re.findall(r'/files/(\d+)', content)
            print(f"      Images: {image_ids}")

            # Get the file objects for the images
            for image_id in image_ids:
                image = course.get_file(image_id)
                image_name = image.display_name
                print(f"      Image Name: {image_name}")

                # Remove the extension from the image name for the alt text
                image_alt = re.sub(r'\..*$', '', image_name)

                # Download the image
                image_path = os.path.join(directory_path, image_name)
                if not os.path.exists(image_path):
                    print(f"      Downloading image: {image_name}")
                    image.download(image_path)
                else:
                    print(f"      Image already exists: {image_path}")

                # Replace the original image tag with our own
                content = re.sub(r'<img.*?src=".*?/files/' + image_id + '".*?>', f'<img src="{image_name}" alt="{image_alt}" />', content)
        
        # Set the title as h1 and convert the content to github flavoured markdown
        markdown_content = f"# {module_item_title}\n\n" 
        markdown_content += convert_text(content, input_format="html", output_format="gfm")

        # Save the content to a markdown file
        file_name = module_item_title + ".md"
        file_path = os.path.join(directory_path, file_name)
        with open(file_path, "w") as file:
            file.write(markdown_content)
            print(f"Saved page content to: {file_path}")

# Exit the script
exit(0) 

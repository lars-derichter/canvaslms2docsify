import os
import re
from canvasapi import Canvas

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
        print(f"Module Item Type: {module_item_type}")

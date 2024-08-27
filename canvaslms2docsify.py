import os
from canvasapi import Canvas

# Define the LMS API endpoint and authentication token
api_endpoint = os.environ.get("API_ENDPOINT") 
auth_token = os.environ.get("AUTH_TOKEN")

# Define the course ID
course_id = os.environ.get("COURSE_ID") 

# Initialize a new Canvas object
canvas = Canvas(api_endpoint, auth_token)

# Get the course object
course = canvas.get_course(course_id)

# Get the course name
course_name = course.name

print(f"Course Name: {course_name}")

# Get the course modules
modules = course.get_modules()

# Loop through each module
for module in modules:
    # Get the module name
    module_name = module.name
    print(f"Module Name: {module_name}")

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

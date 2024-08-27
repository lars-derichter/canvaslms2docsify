import os
from canvasapi import Canvas

# Define the LMS API endpoint and authentication token
api_endpoint = os.environ.get("API_ENDPOINT") 
auth_token = os.environ.get("AUTH_TOKEN")

# Define the course ID
course_id = os.environ.get("COURSE_ID")pyt  

# Initialize a new Canvas object
canvas = Canvas(api_endpoint, auth_token)

# Get the course object
course = canvas.get_course(course_id)

# Get the course name
course_name = course.name

print(f"Course Name: {course_name}")
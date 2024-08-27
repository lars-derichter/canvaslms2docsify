import requests
import os

# Define the LMS API endpoint and authentication token
api_endpoint = os.environ.get("API_ENDPOINT")
auth_token = os.environ.get("AUTH_TOKEN")

# Define the course ID
course_id = os.environ.get("COURSE_ID")

# Make a GET request to retrieve the pages from the course
url = f"{api_endpoint}/courses/{course_id}/pages"
headers = {"Authorization": f"Bearer {auth_token}"}
response = requests.get(url, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    pages = response.json()
    # Process the retrieved pages as needed
    for page in pages:
        page_title = page["title"]
        page_content = page["content"]
        # Do something with the page title and content
        print(f"Page Title: {page_title}")
else:
    print("Failed to retrieve pages from the LMS.")
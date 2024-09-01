import logging
import os
import re

# Helper function to parse the content index and generate sidebar files
def save_content_to_file(content, file_path):
    # Ensure the parent directory exists
    parent_directory = os.path.dirname(file_path)
    if parent_directory:
        os.makedirs(parent_directory, exist_ok=True)

    # Write the content to the file
    with open(file_path, "w") as file:
        file.write(content)

    logging.info(f"Saved content to: {file_path}")

def sanitize_name(name):
    sanitized_name = re.sub(r'\s+', '-', re.sub(r'[^a-zA-Z0-9\s]', '', name.strip()).lower())
    # Remove leading and trailing hyphens, and replace multiple hyphens with a single hyphen
    return re.sub(r'(^-+|-+$|-{2,})', '', sanitized_name)

def parse_directory_index(content_index, indent_spaces=4):
    dirs = []
    lines = content_index.split('\n')
    current_directory_content = []

    for n, line in enumerate(lines):
        # Match directories
        if line.startswith('- '):
            # Save previous directory details if it exists
            if current_directory_content:
                dirs.append({'dir_name': dir_name, 'dir_link': dir_link, 'dir_content': current_directory_content})
                current_directory_content = []

            # dir_name is everything after the first space
            dir_name = line.split(' ', 1)[1]
            logging.info(f"Directory name: {dir_name}")
            # find the first string part between round brackets and save it to the dir_link variable
            for i in range(n, len(lines)):
                match = re.search(r'\]\((.*?)\)', lines[i])
                if match:
                    dir_link = match.group(1)
                    break
            logging.info(f"Directory link: {dir_link}")
        # Match subheaders and files
        elif line.startswith(f'{" " * indent_spaces}'):
            # push line to current_directory_content
            current_directory_content.append(line)
            logging.info(f"Adding line to current_directory_content: {line}")

    # Save the last directory details
    if current_directory_content:
        dirs.append({'dir_name': dir_name, 'dir_link': dir_link, 'dir_content': current_directory_content})

    logging.info(f'dirs: \n\n{dirs}')
    return dirs

def create_root_sidebar(dirs, output_dir="docs"):
    root_sidebar = ""
    for dir in dirs:
        root_sidebar = f"{root_sidebar}- [{dir['dir_name']}]({dir['dir_link']})\n"
    logging.info(f'root_sidebar: \n\n{root_sidebar}')
    save_content_to_file(root_sidebar, os.path.join(output_dir, "_sidebar.md"))
    return root_sidebar

def create_directory_sidebars(dirs, output_dir="docs"):
    for dir in dirs:
        sidebar_content = ""
        dir_name = dir['dir_name']
        dir_path = sanitize_name(dir_name)

        for directory in dirs:
            if directory['dir_name'] == dir_name:
                sidebar_content = f"{sidebar_content}- {directory['dir_name']})\n"
                for line in directory['dir_content']:
                    sidebar_content = f"{sidebar_content}{line}\n"
            else:
                sidebar_content = f"{sidebar_content}- [{directory['dir_name']}]({directory['dir_link']})\n"

        logging.info(f"sidebar_content for {dir_name}: \n\n{sidebar_content}")
        save_content_to_file(sidebar_content, os.path.join(output_dir, dir_path, "_sidebar.md"))
    return True

def create_sidebars(index, output_dir="docs"):
    dirs = parse_directory_index(index)
    root_sidebar = create_root_sidebar(dirs, output_dir)
    directory_sidebars = create_directory_sidebars(dirs, output_dir)
    return root_sidebar, directory_sidebars
            

# Main script

# Set variables
output_dir = os.getenv("OUTPUT_DIR", "docs")

content_index = r"""- ✅ Evaluaties
    - [Opdracht 1 (20 %)](evaluaties/01-opdracht-1-20.md)
    - [Voorbereiding test 1 (30%)](evaluaties/02-voorbereiding-test-1-30.md)
    - [Eindopdracht (50%)](evaluaties/03-eindopdracht-50.md)
- 1\. Les 1
    - [Pagina 1](1-les-1/01-pagina-1.md)
        - [Opdracht 1](1-les-1/02-opdracht-1.md)
    - Subheader 1
        - [Pagina 2](1-les-1/03-pagina-2.md)
        - [Opdracht 2](1-les-1/04-opdracht-2.md)
    - Subheader 2
        - [Pagina 3](1-les-1/05-pagina-3.md)
        - [Pagina 4](1-les-1/06-pagina-4.md)
- 02.01.a
    - [0.01.a.01 stomme naam](0201a/01-001a01-stomme-naam.md)
    - [* laatste pagina van een niet default module](0201a/02-laatste-pagina-van-een-niet-default-module.md)
- 🧰 Praktisch
    - [⚠️ Afspraken](praktisch/01-afspraken.md)
    - [🏥 Afwezig](praktisch/02-afwezig.md)
    - [✉️ Contact [personaliseren]](praktisch/03-contact-personaliseren.md)"""

create_sidebars(content_index, output_dir)

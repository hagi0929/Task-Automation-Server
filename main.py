from typing import Union
import uvicorn
from fastapi import FastAPI
import os
import urllib.request
from dotenv import load_dotenv
import requests, json, shutil
from json.decoder import JSONDecodeError
from notionDBParser import NotionParser
from git import Repo, Git, exc

app = FastAPI()

# Constants
TEMP_DIR = "./temp"
LAST_UPDATED_FILE = 'last_updated_time.json'
GIT_URL = 'https://github.com/hagi0929/hagi0929.github.io'
BRANCH_NAME = 'static-automation'
REPO_DIR = './git_src/hagi0929.github.io'
ASSET_DIR = f'{REPO_DIR}/src/assets'
R_ASSET_DIR = f'./src/assets'

# Load environment variables
load_dotenv()
NOTION_TOKEN = os.getenv('NOTION_API_TOKEN')
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-02-22"
}
LIST_OF_DB = ['fa7d1f6065604c1283c0c96185198215', '861b73a06a3b45e09f24dab539306123']

@app.get("/force-export")
def force_export():
    check_updated_database()
    return {"message": "Forced export completed"}

def read_json_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf8') as file:
            return json.load(file)
    except (JSONDecodeError, FileNotFoundError):
        return {}

def write_json_file(filepath, data):
    with open(filepath, 'w', encoding='utf8') as file:
        json.dump(data, file, ensure_ascii=False)

def query_database(database_id):
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    response = requests.post(url, headers=HEADERS)
    print(response.status_code)
    return response.json()

def retrieve_database_info(database_id):
    url = f"https://api.notion.com/v1/databases/{database_id}"
    response = requests.get(url, headers=HEADERS)
    return response.json()

def import_from_notion(database_id, database_name):
    print("database_import")
    raw_data = query_database(database_id)
    parser = NotionParser(raw_data)
    parsed_data = parser.data
    parsed_files = parser.files

    variable_file = os.path.join(TEMP_DIR, 'variables', f'{database_name}.json')
    files_dir = os.path.join(TEMP_DIR, 'files', database_name)

    os.makedirs(os.path.dirname(variable_file), exist_ok=True)
    os.makedirs(files_dir, exist_ok=True)

    for hash_key, static_file in parsed_files.items():
        file_type = static_file['type']
        file_url = static_file[file_type]['url']
        file_path = os.path.join(files_dir, hash_key)
        print(f"Downloading {file_url} to {file_path}")
        urllib.request.urlretrieve(file_url, file_path)

    write_json_file(variable_file, parsed_data)

def remove_all_in_directory(directory_path):
    if os.path.exists(directory_path):
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)

def setup_repo():
    Repo.clone_from(GIT_URL, REPO_DIR, branch=BRANCH_NAME)

def pull_git():
    g = Git(REPO_DIR)
    g.pull('origin', BRANCH_NAME)


def check_updated_database():
    last_updated_obj = read_json_file(LAST_UPDATED_FILE)
    list_of_updated_db = []

    for database_id in LIST_OF_DB:
        data = retrieve_database_info(database_id)
        print("list_of_files_to_update: ", last_updated_obj)
        database_name = data['title'][0]['plain_text']

        if database_id not in last_updated_obj or data['last_edited_time'] > last_updated_obj[database_id]:
            import_from_notion(database_id, database_name)
            list_of_updated_db.append((database_name, database_id))

        last_updated_obj[database_id] = data['last_edited_time']

    write_json_file(LAST_UPDATED_FILE, last_updated_obj)

    if list_of_updated_db:
        update_target()

def update_target():
    remove_all_in_directory(ASSET_DIR)
    shutil.copytree(TEMP_DIR, ASSET_DIR, dirs_exist_ok=True)
    repo = Repo(REPO_DIR)
    repo.git.add(R_ASSET_DIR)
    repo.git.commit('-m', 'Update assets')
    repo.git.push('origin', BRANCH_NAME)

try:
    repo = Repo(REPO_DIR)
except exc.NoSuchPathError:
    setup_repo()
    repo = Repo(REPO_DIR)

pull_git()
check_updated_database()
# update_target()

# if __name__ == "__main__":
#     main()
    # uvicorn.run(app, host="0.0.0.0", port=8000)

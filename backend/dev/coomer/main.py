import requests
from bs4 import BeautifulSoup
import mysql.connector
import uuid
from datetime import datetime
import re
from tqdm import tqdm
import time
import os

BASE_URL = "https://coomer.su"
IMAGE_URL = "https://img.coomer.su/thumbnail/data"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Accept": "application/json, text/plain, */* image/jpeg",
    "Refer": BASE_URL,
}

DB_CONFIG = {
    "host": "localhost",
    "user": "picdash_user",
    "password": "secretpass",
    "database": "picdash",
}


def test_reachable() -> bool:
    url = f"{BASE_URL}/api/v1/app_version"
    try:
        response = requests.get(f"{url}", timeout=5, headers=HEADERS)
        if response.status_code == 200:
            data = response.text
            print("Version is:", data)
            return True
        else:
            print(f"{url} returned status code {response.status_code}.")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error reaching {url}: {e}")
        return False
    

def get_profiles() -> list:
    """
    Fetches profiles from the Coomer.su API and returns a list of profile dictionaries.
    Each profile dictionary contains 'name', 'id', 'service', and 'favorited' keys.
    Returns:
        list: A list of dictionaries containing profile information.
    Raises:
        requests.exceptions.RequestException: If there is an error during the API request.
    """
    list_profiles = []
    SAFE_NAME_REGEX = re.compile(r"^[a-zA-Z0-9_.\-\s]{1,100}$", re.UNICODE)

    try:
        response = requests.get(f"{BASE_URL}/api/v1/creators.txt", timeout=5, headers=HEADERS)
        if response.ok:
            respdata = response.json()
            print("Profiles fetched successfully:")
            for profile in respdata:
                # Assuming each profile has 'name', 'id', 'service', and 'favorited' keys
                if not all(key in profile for key in ['name', 'id', 'service', 'favorited']):
                    print("Profile data is missing some keys.")
                    continue
                if not SAFE_NAME_REGEX.match(profile['name']):
                    print(f"Profile name '{profile['name']}' is not safe. Skipping.")
                    continue
                # Ensure profile name is safe
                profile_info = {
                    "name": profile['name'],
                    "id": profile['id'],
                    "service": profile['service'],
                    "favorited": profile['favorited']
                }
                list_profiles.append(profile_info)
            print(f"Total profiles fetched: {len(list_profiles)}")
            return list_profiles
        else:
            print(f"Failed to fetch profiles: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"Error fetching profiles: {e}")
        return []
    

def get_profile_data(profile_id: str, service: str) -> dict:
    """
    Fetches detailed profile data from the Coomer.su API for a given profile ID.
    Args:
        profile_id (str): The ID of the profile to fetch data for.
        service (str): The service associated with the profile (e.g., 'onlyfans').
    Returns:
        dict: A dictionary containing the profile's detailed information.
    Raises:
        requests.exceptions.RequestException: If there is an error during the API request.
    """
    try:
        response1 = requests.get(f"{BASE_URL}/api/v1/{service}/user/{profile_id}/posts-legacy", timeout=5, headers=HEADERS)
        if response1.ok:
            profile_data = response1.json()
            # Get Props
            props = profile_data.get('props', {})
            amount_posts = props.get('count', 0)
            last_update = props.get('artist', {}).get('updated', '00:00:00')

            print(f"Profile {profile_id} has {amount_posts} posts and was last updated at {last_update}")

            return {
                "id": profile_id,
                "posts_count": amount_posts,
                "updated_at": last_update,
            }
        else:
            print(f"Failed to fetch profile data for {profile_id}: {response1.status_code}")
            return {}

    except requests.exceptions.RequestException as e:
        print(f"Error fetching profile data for {profile_id}: {e}")
        return {}
    

def get_posts(profile_id: str, service: str) -> list:
    """
    Fetches posts for a given profile ID from the Coomer.su API.
    Args:
        profile_id (str): The ID of the profile to fetch posts for.
        service (str): The service associated with the profile (e.g., 'onlyfans').
    Returns:
        list: A list of dictionaries containing post information.
    Raises:
        requests.exceptions.RequestException: If there is an error during the API request.
    """
    try:
        data_profile = get_profile_data(profile_id, service)
        if not data_profile:
            print(f"No profile data found for {profile_id}.")
            return []
        max_posts = data_profile.get('posts_count', 0)
        if max_posts == 0:
            print(f"No posts found for {profile_id}.")
            return []
        
        loop_num = max_posts / 50
        print(loop_num)
        files = []
        for i in range(int(loop_num) + 1):
            response = requests.get(f"{BASE_URL}/api/v1/{service}/user/{profile_id}?o={i*50}", timeout=5, headers=HEADERS)
            if response.ok:
                posts_data = response.json()
                """
                {'id': '1815702164', 
                'user': 'sweetiefox_of', 
                'service': 'onlyfans', 
                'title': "POV: I'm on top and your life's about to flash before your e..", 
                'content': "<p>POV: I'm on top and your life's about to flash before your eyes! 🥵</p>",
                  'embed': {}, 
                  'shared_file': False, 
                  'added': '2025-07-09T22:36:02.774206', 
                  'published': '2025-07-09T16:37:04', 
                  'edited': None, 
                  'file': {'name': '2316x3088_d73375abc22141f1bc22c17692b71079.jpg', 
                  'path': '/fe/a7/fea72891fabb8f42df0011ec54a5201072750da086a47fcd57d2f1cfa1cc6e1b.jpg'}, 
                  'attachments': [{'name': '2316x3088_8962911c2214803a10543b8f39014150.jpg', 'path': '/b8/2e/b82e22bdf634e27a443823b59956731d78862d8019f403c41f29832a819fc1ee.jpg'}], 
                  'poll': None, 'captions': None, 'tags': None}
                """
                
                for post in posts_data:
                    file1 = post['file']
                    file2 = post['attachments']
                    if all(key in file1 for key in ['name', 'path']):
                        files.append(file1['path'])
                    if isinstance(file2, list):
                        for attachment in file2:
                            files.append(attachment['path'])
            else:
                print(f"Failed to fetch posts for {profile_id}: {response.status_code}")
        
        print(f"Total files fetched for profile {profile_id}: {len(files)}")
        return files
            
    except requests.exceptions.RequestException as e:
        print(f"Error fetching posts for {profile_id}: {e}")
        return []


def download_files(files: list, save_path: str, profile_id: str) -> None:
    # if not files:
    #     print("No files to download.")
    #     return
    # if not save_path:
    #     print("No save path provided.")
    #     return
    # if not isinstance(files, list):
    #     print(f"Expected a list of files, got {type(files)}")
    #     return
    # if not isinstance(save_path, str):
    #     print(f"Expected a string for save path, got {type(save_path)}")
    #     return
    # print(f"Downloading {len(files)} files to {save_path}...")
    if not os.path.exists(f"{save_path}/{profile_id}"):
        os.makedirs(save_path + f"/{profile_id}")
    session = requests.Session()
    for file_path in tqdm(files, desc="Downloading files"):
        try:
            file_url = f"{IMAGE_URL}/{file_path}"
            file_name = os.path.basename(file_path)
            save_file_path = os.path.join(save_path, profile_id, file_name)

            response = session.get(file_url, headers=HEADERS, timeout=5)
            if response.ok:
                with open(save_file_path, 'wb') as f:
                    f.write(response.content)
            else:
                print(f"Failed to download {file_name}: {response.status_code}")
                print(response.text)
        except requests.exceptions.RequestException as e:
            print(f"Error downloading {file_name}: {e}")




def main():
    if not test_reachable():
        print("Coomer.su is not reachable. Exiting.")
        return

    files_posts = get_posts("600245459348365312", "fansly")
    download_files(files=files_posts, save_path=".", profile_id="600245459348365312")



def test_image():
    url1 = "/3c/e9/3ce9f0e6363024e7f6b41c12a160d9150f8c9c95c649ae1ef4bb9971f385dd0d.jpg"
    full_url = f"https://img.coomer.su/thumbnail/data{url1}"
    try:
        response = requests.get(full_url, headers=HEADERS, timeout=5)
        if response.ok:
            print("Image is reachable.")
        else:
            print(f"Failed to reach image: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error reaching image: {e}")



if __name__ == "__main__":
    main()
    #test_image()
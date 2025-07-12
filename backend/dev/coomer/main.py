import requests
from bs4 import BeautifulSoup
import mysql.connector
import uuid
from datetime import datetime
import re
from tqdm import tqdm
import time

BASE_URL = "https://coomer.su"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Accept": "application/json, text/plain, */*",
    "Origin": BASE_URL,
}

DB_CONFIG = {
    "host": "localhost",
    "user": "picdash_user",
    "password": "secretpass",
    "database": "picdash",
}


def test_reachable() -> bool:
    try:
        response = requests.get(f"{BASE_URL}/api/v1/app_version", timeout=5, headers=HEADERS)
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
                "service": service,
                "posts_count": amount_posts,
                "updated_at": last_update,
                "name": profile_data.get('props', {}).get('artist', {}).get('name', 'Unknown'),
                "external_id": profile_data.get('props', {}).get('artist', {}).get('external_id', 'Unknown'),
            }

    except requests.exceptions.RequestException as e:
        print(f"Error fetching profile data for {profile_id}: {e}")
        return {}
    
        




def main():
    if not test_reachable():
        print("Coomer.su is not reachable. Exiting.")
        return

    get_profile_data("sweetiefox_of", "onlyfans")

if __name__ == "__main__":
    main()
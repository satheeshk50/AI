import requests
import os
from dotenv import load_dotenv


load_dotenv()
ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
PROFILE_URN = os.getenv("PROFILE_URN")
# print("Access Token:", ACCESS_TOKEN)
# print("PROFILE URN:", PROFILE_URN)

def linkedin_api(text:str):
    """
    Post a text update to LinkedIn using the REST API.
    
    Args:
        text (str): The text content to post.
    """
    url = "https://api.linkedin.com/rest/posts"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}", 
        "X-Restli-Protocol-Version": "2.0.0",
        "LinkedIn-Version": "202506",
        "Content-Type": "application/json"
    }

    post_data = {
        "author": PROFILE_URN,
        "commentary": text,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": []
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False
    }

    response = requests.post(url, headers=headers, json=post_data)

    if response.status_code == 201:
        return {'content': 'Post created successfully', 'status_code': response.status_code}
    else:
        return {'error': response.text, 'status_code': response.status_code}
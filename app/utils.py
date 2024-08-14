import os
from django.utils import timezone
from .models import *
from django.shortcuts import get_object_or_404
from datetime import timedelta
import requests


def check_and_refresh_token(location_id): 
    token = get_object_or_404(AccessToken, location_id=location_id) 
    if token.expiry <= timezone.now()-timedelta(minutes=5):
        print("refreshing access token since expired")
               
        #  refresh access token when expired
        url ="https://services.leadconnectorhq.com/oauth/token"  
        
        payload = {
            "client_id": os.getenv('CLIENT_ID'),
            "client_secret":  os.getenv('CLIENT_SECRET'),
            "grant_type": "refresh_token",
            "refresh_token": token.refresh,
            "user_type": "Location",
            
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }

        response = requests.post(url, data=payload, headers=headers)

        print(response.json())
        token = get_object_or_404(AccessToken, location_id=location_id)
        token.access = response.json()['access_token']
        token.refresh = response.json()['refresh_token']
        token.expiry = timezone.now() + timedelta(seconds=response.json()['expires_in'])
        token.save()

    return token.access




def get_pipeline_name(id,stage):
    url = "https://services.leadconnectorhq.com/opportunities/pipelines"

    querystring = {"locationId":"NqyhE9rC0Op4IlSj2IIZ"}
    

    token = check_and_refresh_token("NqyhE9rC0Op4IlSj2IIZ")
    headers = {
        "Authorization": f"Bearer {token}",
        "Version": "2021-07-28",
        "Accept": "application/json"
    }

    response = requests.get(url, headers=headers, params=querystring)
    
    data = {}
    if response.status_code == 200:
        # print(response.json())
        res = response.json()['pipelines']
        for each_res in res:
            if each_res['id'] == id:
                data['pipeline'] = each_res['name']
                for st in  each_res['stages']:
                    if st['id'] == stage:
                        data['stage'] = st['name']
                    
                return data
    else:
        print("error fetching pipelines")
        return False
    

def get_assigned_user(id):
    url = f"https://services.leadconnectorhq.com/users/{id}"


    token = check_and_refresh_token("NqyhE9rC0Op4IlSj2IIZ")
    headers = {
        "Authorization": f"Bearer {token}",
        "Version": "2021-07-28",
        "Accept": "application/json"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()['name']
    
    else:
        print(response.json())
        return None
    
import os
import requests
from dotenv import load_dotenv
from django.utils import timezone
from datetime import datetime,timedelta
from rest_framework.serializers import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from .models import AccessToken
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
import time
load_dotenv()


@api_view(['GET'])
def list_pipelines(request):
    url = "https://services.leadconnectorhq.com/opportunities/pipelines"

    querystring = {"locationId":"NqyhE9rC0Op4IlSj2IIZ"}
    

    token = check_and_refresh_token("NqyhE9rC0Op4IlSj2IIZ")
    headers = {
        "Authorization": f"Bearer {token}",
        "Version": "2021-07-28",
        "Accept": "application/json"
    }

    response = requests.get(url, headers=headers, params=querystring)
    
    data = []
    if response.status_code == 200:
        # print(response.json())
        res = response.json()['pipelines']
        for each_res in res:
            each_dict = {}
            each_dict['id'] = each_res['id']
            each_dict['name'] = each_res['name']
            data.append(each_dict)

        return Response({'pipelines':data},status=status.HTTP_200_OK)
    
    else:
        print("error fetching pipelines")
        return Response({"message":"error fetching pipelines list"},status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def opp_list_by_pipeline(request):
    search = request.GET.get('searchId',None)
    pipelineId = request.GET.get('pipelineId')

    if  not pipelineId:
        return Response({"error": "Missing 'pipelineId' parameter"}, status=status.HTTP_400_BAD_REQUEST)
     
    stages = get_stages_by_pipeline(pipelineId)
    # print(stages)
    if stages is None or not stages['stages_list'] or 'pipelineName' not in stages:
        return Response({"error": "Error fetching stages from pipeline or wrong pipelineId"}, status=status.HTTP_404_NOT_FOUND)
    
    data = {"stages":{},"counts":{}}
    for stage in stages['stages_list']:
        data['stages'][stage['name']] = []
        data['counts'][stage['name']] = 0

    
    # search for opportunities with search and pipelineId query
    opportunities = search_opp(pipelineId,search,stage=None)

    if opportunities is None:
        return Response({"error": "Error fetching opportunities from pipeline"}, status=status.HTTP_404_NOT_FOUND)
    
 
    print(f"Total opportunities {len(opportunities)}")
    data_limit = False
    opp_stage_name = ""
    for opportunity in opportunities:
        opp_data = {}
        for stage in stages['stages_list']:
            if stage['stage_id'] == opportunity['pipelineStageId']:
                opp_stage_name = stage['name']
        # print(opp_stage_name)
        
        if data_limit is False:
            opp_data['id'] = opportunity['id']
            opp_data['name'] = opportunity['name']
            opp_data['contactName'] = opportunity['contact']['name']
            opp_data['source'] = opportunity['source'] if 'source' in opportunity else None
            opp_data['monetaryValue'] = opportunity['monetaryValue'] if 'monetaryValue' in opportunity else 0
            opp_data['pipelineStage'] = opp_stage_name
            opp_data['pipelineName'] = stages['pipelineName']
            opp_data['opportunityStage'] = None
            opp_data['closingDueDate'] = None

            if opportunity['customFields'] != []:
                for field in opportunity['customFields']:
                    if field['id'] == "Bfnik1BkCUNhvDPWJrvI":
                        opp_data['opportunityStage'] = field['fieldValueString']

                    if field['id'] == "TQXTPRZqpXKMy9aaP42A":
                        date_str = datetime.fromtimestamp(field['fieldValueDate']/1000)
                        opp_data['closingDueDate'] = date_str.date()
            
        
        if opp_data['opportunityStage'] is None:
            pass
        else:
            data['counts'][opp_stage_name] += 1
            if len(data['stages'][opp_stage_name]) < 10:
                # print(opp_data)
                data['stages'][opp_stage_name].append(opp_data)
            
        all_stages_limit = False
        for stage in stages['stages_list']:
            if len(data['stages'][stage['name']]) < 10:
                all_stages_limit = True

        if not all_stages_limit:
            data_limit = True
                
    return Response({"data":data},status=status.HTTP_200_OK)

@api_view(['GET'])
def opp_list_by_stage(request):

    search = request.GET.get('searchId',None)
    limit = request.GET.get('limit',10)
    offset = request.GET.get('offset',0)
    received_stage = request.GET.get('stage')
    pipelineId = request.GET.get('pipelineId')

    if not received_stage or not pipelineId:
        return Response({"error": "Missing 'stage' or 'pipelineId' parameter"}, status=status.HTTP_400_BAD_REQUEST)
    
    offset = int(offset)
    limit = int(limit)
    stages = get_stages_by_pipeline(pipelineId)
    # print(stages)

    if stages is None or not stages['stages_list'] or 'pipelineName' not in stages:
        return Response({"error": "Error fetching stages from pipeline or wrong pipelineId or wrong stage"}, status=status.HTTP_404_NOT_FOUND)
    
    pipelineName = stages['pipelineName']
    pipelineStageId = ""
    for stage in stages['stages_list']:
        if stage['name'] == received_stage:
            pipelineStageId = stage['stage_id']

    if pipelineStageId == "":
        return Response({"message":"wrong stage name"},status=status.HTTP_404_NOT_FOUND)  


    data = []

    
    opportunities = search_opp(pipelineId,search,pipelineStageId)

    if opportunities is None:
        return Response({"error": "Error fetching opportunities from pipeline"}, status=status.HTTP_404_NOT_FOUND)


    needed_opportunities = [o for o in opportunities if o['customFields'] for f in o['customFields']  if f['id'] ==  "Bfnik1BkCUNhvDPWJrvI"]
    
    
    # print(offset)
    count=0
    not_count = 0
    print("----------------------------------------------------------------------")
    for opportunity in needed_opportunities[offset:]:
        opp_data = {}
        
        opp_data['id'] = opportunity['id']
        opp_data['name'] = opportunity['name']
        opp_data['contactName'] = opportunity['contact']['name']
        opp_data['source'] = opportunity['source'] if 'source' in opportunity else None
        opp_data['monetaryValue'] = opportunity['monetaryValue'] if 'monetaryValue' in opportunity else 0
        opp_data['pipelineStage'] = received_stage
        opp_data['pipelineName'] = pipelineName
        opp_data['opportunityStage'] = None
        opp_data['closingDueDate'] = None

        if opportunity['customFields'] != []:
            for field in opportunity['customFields']:
                if field['id'] == "Bfnik1BkCUNhvDPWJrvI":
                    opp_data['opportunityStage'] = field['fieldValueString']

                if field['id'] == "TQXTPRZqpXKMy9aaP42A":
                    date_str = datetime.fromtimestamp(field['fieldValueDate']/1000)
                    opp_data['closingDueDate'] = date_str.date()
        # print(opp_data['opportunityStage'])
        if opp_data['opportunityStage'] is None:
            print(opportunity['id'])
            not_count+=1
            # print(f"not added to list is {not_count}")
        else:
            count+=1
            # print(count)
            if len(data) < limit:
                data.append(opp_data)
            else:
                break

    return Response({received_stage:data},status=status.HTTP_200_OK)



def search_opp(pipeline_id,search,stage):
    print(f"stage is {stage}")
    url = f"https://services.leadconnectorhq.com/opportunities/search"

    token = check_and_refresh_token("NqyhE9rC0Op4IlSj2IIZ")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Version": "2021-07-28",
        "Accept": "application/json"
    }
    
    querystring = {
        "pipeline_id":pipeline_id,
        "limit":100,
        "location_id":"NqyhE9rC0Op4IlSj2IIZ"
    }

    if search:
        querystring['id'] = search
    if stage:
        querystring['pipeline_stage_id'] = stage

    opportunities = []
    count = 0 
    while url:
        print(f"url is {url}")
        print(querystring)
        
        # to handle requests exceeded limit 
        max_retries = 5
        retry_delay = 10  

        for attempt in range(max_retries):
            opp_search_response = requests.get(url, headers=headers, params=querystring)
            if opp_search_response.status_code == 200:
                if 'opportunities' in opp_search_response.json():
                    opportunities.extend(opp_search_response.json()['opportunities'])
                    count+=len(opp_search_response.json()['opportunities'])
                    print(f"Appended {count} opportunities to list")
                else:
                    print("NO 'opportunities key in response dict")

                url = opp_search_response.json()['meta']['nextPageUrl']

                if url:                
                    # Update querystring for the next request
                    querystring={}

                break
            elif opp_search_response.status_code == 429:
                print(f"Rate limit exceeded. Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
                retry_delay *= 2 
            else:
                print(f"Unexpected error: {opp_search_response.status_code}")
                try:
                    print(opp_search_response.json())
                except ValueError:
                    print("Response content is not valid JSON")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                print(opp_search_response.headers)

    
    return opportunities


def get_stages_by_pipeline(id):
    url = "https://services.leadconnectorhq.com/opportunities/pipelines"

    querystring = {"locationId":"NqyhE9rC0Op4IlSj2IIZ"}
    

    token = check_and_refresh_token("NqyhE9rC0Op4IlSj2IIZ")
    headers = {
        "Authorization": f"Bearer {token}",
        "Version": "2021-07-28",
        "Accept": "application/json"
    }

    max_retries = 5
    retry_delay = 10  
    data = {"stages_list":[]}
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            # print(response.json())
            res = response.json()['pipelines']
            for pipeline in res:
                if pipeline['id']==id:
                    data['pipelineName'] = pipeline['name']
                    for stage in pipeline['stages']:
                        data['stages_list'].append({"stage_id":stage['id'],"name":stage['name']})

            # print(data)
            return data
        elif response.status_code == 429:
            print(f"Rate limit exceeded. Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
            time.sleep(retry_delay)
            retry_delay *= 2 
        else:
            print(f"Unexpected error: {response.status_code}")
            try:
                print(response.json())
            except ValueError:
                print("Response content is not valid JSON")
                time.sleep(retry_delay)
                retry_delay *= 2
            print(response.headers)

    
    return None

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


#  create access token
class CreateAccessToken(APIView):
    def post(self,request):
        
        try:
            user_location_id = request.data['location_id']
            code = request.data.get('code')
            if not user_location_id or not code:
                raise ValidationError("location_id and code are required fields.")
        
            access_token_instance = AccessToken.objects.get(location_id=user_location_id)
            if access_token_instance:  
                print("access token exists")
                return Response({'message': "Acces token already exists"},status=200)
            
        except AccessToken.DoesNotExist:
            print("doesnot exist")
            url ="https://services.leadconnectorhq.com/oauth/token"  
            
            payload = {
                "client_id": os.getenv('CLIENT_ID'),
                "client_secret": os.getenv('CLIENT_SECRET'),
                "grant_type": "authorization_code",
                "code": code,
                "user_type": "Location",
                
            }
        
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
            }

            response = requests.post(url, data=payload, headers=headers)
        
            if response.ok:
            
                access_token = response.json()['access_token']
                refresh_token = response.json()['refresh_token']
                expiry_time = timezone.now() + timedelta(seconds=response.json()['expires_in'])

                # Check if AccessToken instance exists for the given location ID
                response_location_id = response.json()['locationId']

                if response_location_id == user_location_id:

                    # Create new AccessToken instance            
                    AccessToken.objects.create(
                        location_id=response_location_id,
                        access=access_token,
                        refresh=refresh_token,
                        expiry=expiry_time
                    )
                    return Response({'message':  "Successfully created access token"},status=200)

                else:
                    return Response({'message': "Wrong Location Id"},status=400)
                
            else:
                print(response.json())
                return Response({'message': response.json()['error_description']},status=response.status_code)

        except Exception as e:
            print(e)
            return Response({'message': str(e)}, status=500)       
        
import os
import requests
from dotenv import load_dotenv
from django.utils import timezone
from datetime import datetime,timedelta
from rest_framework.serializers import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from .models import *
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
import time
from .tasks import fetch_opportunities
from .utils import get_assigned_user,get_pipeline_name,check_and_refresh_token
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import pytz
from .cron_task import cron_task
load_dotenv()



def search_opp(search):
    url = f"https://services.leadconnectorhq.com/opportunities/search"

    token = check_and_refresh_token("NqyhE9rC0Op4IlSj2IIZ")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Version": "2021-07-28",
        "Accept": "application/json"
    }
    
    querystring = {
        "limit":100,
        "location_id":"NqyhE9rC0Op4IlSj2IIZ",
        "pipeline_id":"kk0EeBcUijsZJG1vJyn9"
    }
    
    if search:
        querystring['q'] = search

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


def get_opp(id):
    url = f"https://services.leadconnectorhq.com/opportunities/{id}"
    token = check_and_refresh_token("NqyhE9rC0Op4IlSj2IIZ")
    headers = {
        "Authorization": f"Bearer {token}",
        "Version": "2021-07-28",
        "Accept": "application/json"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()['opportunity']
    
    else:
        return None
    


@api_view(['GET'])
def opp_by_name(request):
    opp_name = request.GET.get('opportunityName')

    if not opp_name:
      return Response({"error": "Missing 'opportunityName' parameter"}, status=status.HTTP_400_BAD_REQUEST)
    
    opportunities = search_opp(opp_name)

    if opportunities is None:
        return Response({"error": "Error fetching opportunities from location"}, status=status.HTTP_404_NOT_FOUND)
    
    opportunities_with_name = []
    for opportunity in opportunities:
        opp_data = {}
        if opp_name.lower() in opportunity['name'].lower():
            opp_data['id'] = opportunity['id']
            opp_data['name'] = opportunity['name']
            opp_data['contactName'] = opportunity['contact']['name']
            opp_data['source'] = opportunity['source'] if 'source' in opportunity else None
            opp_data['monetaryValue'] = opportunity['monetaryValue'] if 'monetaryValue' in opportunity else 0
            opp_data['opportunityStage'] = None
            opp_data['closingDueDate'] = None

            if 'customFields' in opportunity and opportunity['customFields'] != []:
                for field in opportunity['customFields']:
                    if field['id'] == "Bfnik1BkCUNhvDPWJrvI":
                        opp_data['opportunityStage'] = field['fieldValueString']

                    if field['id'] == "TQXTPRZqpXKMy9aaP42A":
                        date_str = datetime.fromtimestamp(field['fieldValueDate']/1000)
                        opp_data['closingDueDate'] = date_str.date()


            pipeline_details = get_pipeline_name(opportunity['pipelineId'],opportunity['pipelineStageId'])
            if pipeline_details:
                opp_data['pipelineStage'] = pipeline_details['stage']
                opp_data['pipelineName'] = pipeline_details['pipeline']

            opportunities_with_name.append(opp_data)

    return Response({"opportunities":opportunities_with_name},status=200)
       
@api_view(['POST'])
def opportunities_webhook(request):
        print(request.headers)
        print("opportunities webhook called")
        if not AccessToken.objects.filter(location_id=request.data['locationId']).exists():
            print("location not onboarded")
            return Response({"message":"location not onboarded"},status=400)
   

        loan_pipelines = {
            "iET1Mx1H0C2mN2ExvI7t":"Loan Officer - Adam",
            "3GUjztY5QxawecchRTEQ":"Loan Officer - Dan",
            "sgiIIXS9ccUA32HuVzyp":"Loan Officer - Dawn",
            "VgzPhjLCDIrqfc27nuke":"Loan Officer - Liz",
            "JvD2NiqvELeBQwJmegAG":"Loan Officer - Nicole",
            "634NUynY3fM1vIPmZIDR":"Loan Officer- Kevin",
            "kk0EeBcUijsZJG1vJyn9":"Processing"
        }
        data = request.data
        print(request.data)

        req_type = data['type']

        if req_type == "OpportunityCreate" or req_type == "OpportunityUpdate" or req_type == "OpportunityAssignedToUpdate" or req_type == "OpportunityStageUpdate" or req_type == "OpportunityMonetaryValueUpdate":
            # create or update existing tables rows
            print("req for opp create or update received")
            if data['pipelineId'] in loan_pipelines:
                print(f"updating totalopportunities table for opp {data['id']}")
                total_opp_instance, total_created= TotalOpportunties.objects.get_or_create(opp_id=data['id'])
                print(total_created if total_created else total_opp_instance)
            
                total_opp_instance.pipeline_id = data['pipelineId']
                total_opp_instance.stage_id = data['pipelineStageId']
                
                pipeline_details = get_pipeline_name(data['pipelineId'],data['pipelineStageId'])
                if pipeline_details:
                    total_opp_instance.stage_name = pipeline_details['stage']
                    total_opp_instance.pipeline_name = pipeline_details['pipeline']

                total_opp_instance.save()

                if total_created:
                    print("created opp in total opportunities")
                else:
                    print("updated opp in total opportunities")
            

            if data['pipelineId'] == "kk0EeBcUijsZJG1vJyn9":
                print(f"updating processingopportunities table for opp {data['id']}")
                opp_instance, created = ProcessingOpportunities.objects.get_or_create(opp_id=data['id'])
                
                opp_instance.opp_name = data['name']
                opp_instance.pipeline_id = data['pipelineId']
                opp_instance.stage_id = data['pipelineStageId']
                opp_instance.assigned_user_id = data.get('assignedTo')
                opp_instance.monetary_value = data.get('monetaryValue',0)
                
                pipeline_details = get_pipeline_name(data['pipelineId'],data['pipelineStageId'])
                if pipeline_details:
                    opp_instance.stage_name = pipeline_details['stage']
                    opp_instance.pipeline_name = pipeline_details['pipeline']
                
                assigned_name = get_assigned_user(data['assignedTo'])
                if assigned_name:
                    opp_instance.assigned_user_name = assigned_name
                
                get_opp_details = get_opp(data['id'])
                if get_opp_details:
                    
                    location_timezone = "America/New_York"
                    target_timezone = pytz.timezone(location_timezone)
                    date_str = get_opp_details['lastStageChangeAt'] 
                    date_datetime = datetime.fromisoformat(date_str)
                    date_in_timezone = date_datetime.astimezone(target_timezone)
                    date_required = date_in_timezone.strftime("%Y-%m-%d")
                    opp_instance.actual_closed_date = date_required

                    if 'customFields' in get_opp_details and get_opp_details['customFields'] != []:
                        for field in get_opp_details['customFields']:
                            if field['id'] == "5hOAqmsYZs4U9e8K4EsJ":
                                opp_instance.loan_type = field['fieldValue'][0]

                            if field['id'] == "UE5SWIOEeAjs8SGnNAUr":
                                opp_instance.explanation = field['fieldValue']

                            if field['id'] == "tF6ULs19sWBsNp23jjEF":
                                opp_instance.how_many_times_lender_change = field['fieldValue']

                            if field['id'] == "TQXTPRZqpXKMy9aaP42A":
                                opp_instance.close_due_date = field['fieldValue']

                            if field['id'] == "tS1UTzx50RhppuQMJTVs":
                                opp_instance.original_close_due_date = field['fieldValue']

                opp_instance.save()

                if created:
                    print("created opp in processing table")
                else:
                    print("updated opp processing table")
            print("succesfully updated db")
            return Response({"message":"succesfully updated db"},status=200)
        
        if request.data['type'] == "OpportunityDelete":
            print("opp deleted req received")
            pro_opp_instance = None
            total_opp_instance = None

            try:
                pro_opp_instance = ProcessingOpportunities.objects.get(opp_id=request.data['id'])
            except ProcessingOpportunities.DoesNotExist:
                pro_opp_instance = None
            
            try:
                total_opp_instance = TotalOpportunties.objects.get(opp_id=request.data['id'])
            except TotalOpportunties.DoesNotExist:
                total_opp_instance = None

            if pro_opp_instance:
                pro_opp_instance.delete()
                print("deleted processing instance")

            if total_opp_instance:
                total_opp_instance.delete()
                print("deleted total instance")

             
            print("succesfully deleted opportunities from db")
            return Response({"message":"succesfully deleted opportunities from db"},status=200)

        return Response({"message":"bad request"},status=400)

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
                fetch_opportunities.delay()
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
        
from .models import *
from datetime import datetime
import requests
import time
from celery import shared_task
from .utils import check_and_refresh_token,get_assigned_user,get_pipeline_name

@shared_task(bind=True, max_retries=30, default_retry_delay=10)
def fetch_opportunities(self, *args):
    print("celerey task started - fetching opportunties")
    opportunities = search_opportunities()

    loan_pipelines = {
        "iET1Mx1H0C2mN2ExvI7t":"Loan Officer - Adam",
        "3GUjztY5QxawecchRTEQ":"Loan Officer - Dan",
        "sgiIIXS9ccUA32HuVzyp":"Loan Officer - Dawn",
        "VgzPhjLCDIrqfc27nuke":"Loan Officer - Liz",
        "JvD2NiqvELeBQwJmegAG":"Loan Officer - Nicole",
        "634NUynY3fM1vIPmZIDR":"Loan Officer- Kevin",
        "kk0EeBcUijsZJG1vJyn9":"Processing"
    }
    count = 0
    print(len(opportunities))
    for opp in opportunities:
        count+=1
        print("looping over started",count)

        if opp['pipelineId'] in loan_pipelines:
            total_opp_instance, created = TotalOpportunties.objects.get_or_create(opp_id=opp['id'])
            
            total_opp_instance.pipeline_id = opp['pipelineId']
            total_opp_instance.stage_id = opp['pipelineStageId']
            
            pipeline_details = get_pipeline_name(opp['pipelineId'],opp['pipelineStageId'])
            if pipeline_details:
                total_opp_instance.stage_name = pipeline_details['stage']
                total_opp_instance.pipeline_name = pipeline_details['pipeline']

            total_opp_instance.save()
            
        # if opp['pipelineId'] == "kk0EeBcUijsZJG1vJyn9":
        #     opp_instance, created = ProcessingOpportunities.objects.get_or_create(opp_id=opp['id'])
            
        #     opp_instance.opp_name = opp['name']
        #     opp_instance.pipeline_id = opp['pipelineId']
        #     opp_instance.stage_id = opp['pipelineStageId']
        #     opp_instance.assigned_user_id = opp['assignedTo']
        #     opp_instance.monetary_value = opp['monetaryValue']
        #     opp_instance.actual_closed_date = opp['lastStageChangeAt']
            
        #     pipeline_details = get_pipeline_name(opp['pipelineId'],opp['pipelineStageId'])
        #     if pipeline_details:
        #         opp_instance.stage_name = pipeline_details['stage']
        #         opp_instance.pipeline_name = pipeline_details['pipeline']
            
        #     assigned_name = get_assigned_user(opp['assignedTo'])
        #     if assigned_name:
        #         opp_instance.assigned_user_name = assigned_name

        #     if 'customFields' in opp and opp['customFields'] != []:
        #         for field in opp['customFields']:
        #             if field['id'] == "5hOAqmsYZs4U9e8K4EsJ":
        #                 opp_instance.loan_type = field['fieldValueArray'][0]

        #             if field['id'] == "UE5SWIOEeAjs8SGnNAUr":
        #                 opp_instance.explanation = field['fieldValueString']

        #             if field['id'] == "tF6ULs19sWBsNp23jjEF":
        #                 opp_instance.how_many_times_lender_change = field['fieldValueString']

        #             if field['id'] == "TQXTPRZqpXKMy9aaP42A":
        #                 date_str = datetime.fromtimestamp(field['fieldValueDate']/1000)
        #                 opp_instance.close_due_date = date_str.date()

        #     opp_instance.save()

    return "succesfully saved to db"



def search_opportunities():
    print("searching opps")
    url = f"https://services.leadconnectorhq.com/opportunities/search"

    token = check_and_refresh_token("NqyhE9rC0Op4IlSj2IIZ")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Version": "2021-07-28",
        "Accept": "application/json"
    }
    
    querystring = {
        "limit":100,
        "location_id":"NqyhE9rC0Op4IlSj2IIZ"
    }
    
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



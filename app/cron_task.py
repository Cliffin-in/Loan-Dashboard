from .tasks import search_opportunities
from .models import *
def cron_task():
    print("cron task call")
    opportunities = search_opportunities()
    api_opp = []

    for opp in opportunities:
        id = opp.get('id')
        api_opp.append(id)
    
    print(f"length of api opps {len(api_opp)}")

    total_table = TotalOpportunties.objects.all()
    pro_table = ProcessingOpportunities.objects.all()

    for i in total_table:
        if i.opp_id in api_opp:
            i.exists_in_ghl = True
            i.save()
            print(f"updated opp {i.opp_id} in total table")

    
    for j in pro_table:
        if j.opp_id in api_opp:
            j.exists_in_ghl = True
            j.save()
            print(f"updated opp {j.opp_id} in processing table")

    
    # deleting those opps which are not in ghl
    deleted_count = delete_items_not_in_ghl()
    print(deleted_count)
    return {"message":"Updated db succesfully","deleted count":deleted_count}

def delete_items_not_in_ghl():
    print("delete fun call")
    opp_to_delete = TotalOpportunties.objects.filter(exists_in_ghl=False)
    deleted_opp_count = 0
    
    pro_table_delete = ProcessingOpportunities.objects.filter(exists_in_ghl=False)
    pro_table_delete_count = 0

    for opp in opp_to_delete:
        print(f"Deleting opp : {opp.opp_id}")
        opp.delete()
        deleted_opp_count+=1
        print("Deleted opp succesfully from total table")

    for pro in pro_table_delete:
        print(f"Deleting opp : {pro.opp_id}")
        pro.delete()
        pro_table_delete_count+=1
        print("Deleted opp succesfully from processing table")

    print(f"Total opp deleted from total table is {deleted_opp_count}")
    print(f"Total opp deleted from processing table  is {pro_table_delete_count}")

    return {
        "total table delete count": deleted_opp_count,
        "processing delete count": pro_table_delete_count
    }



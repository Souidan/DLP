import DLP_DB
import DLP_Web


ids_list = DLP_DB.Get_Unreleased_Incidents()
print(ids_list)
print(len(ids_list))
print(ids_list[0])
if(len(ids_list)>0):
    if(DLP_Web.Release_Incidents(ids_list)):
        print("here")
        for incident_id in ids_list:
            DLP_DB.Release_Incident(incident_id)

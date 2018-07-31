from requests import Session
from zeep import Client
from zeep.transports import Transport
from requests.auth import AuthBase, HTTPBasicAuth
import datetime
import uuid
import configparser
import DLP_DB
import json


class SymantecAuth(AuthBase):
    def __init__(self, username, password, host):
        self.basic = HTTPBasicAuth(username, password)
        self.host = host

    def __call__(self, r):
        if r.url.startswith(self.host):
            return self.basic(r)
        else:
            return r
def Handle_Errors():
        config = configparser.ConfigParser()
        config.read('DLP_Error_Handler.ini')
        wsdl = config ['CONNECTION']['SERVER_URL']
        username = config  ['CONNECTION']['USER_NAME']
        password = config['CONNECTION']['PASSWORD']
        server_ip_address = config ['CONNECTION']['SERVER_IP']

        session = Session()
        session.auth = SymantecAuth(username, password,server_ip_address)

        session.verify = False
        transport = Transport(session=session)


        client = Client(wsdl=wsdl, transport=Transport(session=session))
        Delete_Released_Incidents(client)
        UnRelease_Errored_Incidents(client)
        
        
        
      

def Get_Successful_Incidents(incidentDetailsList):
     successfulIncidents=[]
     for incident in incidentDetailsList:
                incidentHistory = incident["incident"]["incidentHistory"]
                for event in incidentHistory :
                    if (event["actionType"]["actionTypeId"]) == 26:
                        successfulIncidents.append(incident["incident"]["incidentId"])
     return successfulIncidents

def Get_All_IncidentsId(incidentDetailsList):
     incidentsId=[]
     for incident in incidentDetailsList:
            incidentsId.append(incident["incident"]["incidentId"])
     return incidentsId

def Delete_Released_Incidents(client):
        releasedIncidents = DLP_DB.Get_All_Released_Incidents()
        incidentDetailsList = client.service.incidentDetail(incidentLongId=releasedIncidents , incidentId=0,includeHistory=True)
        successfulIncidents = Get_Successful_Incidents(incidentDetailsList)
        for successfulIncident in successfulIncidents:
            DLP_DB.Delete_Incident(successfulIncident)


def UnRelease_Errored_Incidents(client):
        incidents = DLP_DB.Get_All_Incidents()
        incidentDetailsList = client.service.incidentDetail(incidentLongId=incidents , incidentId=0,includeHistory=False)
        incidentIdsList = Get_All_IncidentsId(incidentDetailsList)
        for incidentId in incidentIdsList:
            DLP_DB.UnRelease_Incident(incidentId)

Handle_Errors()
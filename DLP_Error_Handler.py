""" 
This code is a helper code for the main function it does mainly a functionality 
that will clean up the DB from failed values or successful values.

Successful values will be deleted from the local DB that the code is running on in order to achieve high performance
as we are sure that we will not need these records any more as the enforce server has released them succesffuly
. On the other hand the records that have failed from the enforce server due to SSL faliure or connection timeouts
will be updated and the code will set the flags of released to being zero thus the next iteration from the main  code will help releasing it
in order to stop any stuck entries from being released

The code is inline documeneted . We create a log file in the same path as the running file in order to keep you
updated with whats going on. Then we read from the configuration files the needed parameters such as the username , ips ,password
After that we create a session using "requests" library in order to have a persistant connection with the server.

Then we connect to the enforce server the server uses SOAP requests and the response is a wsdl thus we chose to use "zeep" library to avoid the headache caused by wsdls
we then delete all successful entries from the database while writing the incident ids in the log files for further need. After making sure from the enforce server of course

we the run a second iteration on the database on the remaining entries to check if they were hung incidents (incidentes where they have an approval value of 1 and release value of 1 however they  have not beenreleased on the enforce server)
we update them by setting their release flag back to 0 or False. And wait for a second iteration of the main code to run and try to release them again.

The wsdl response is handled as a JSON string thus manipulation will be easy as any JSON String manipulation.

The code works well on Python version 3.6.5 and has been tested and all exception have been handled and are written into the logfiles.

Proudly Developed by Share Technologies
"""








from requests import Session
from zeep import Client
from zeep.transports import Transport
from requests.auth import AuthBase, HTTPBasicAuth
import datetime
import uuid
import configparser
import DLP_DB
import json
import logging
import sys
import time

## creating logging file with name of the day##
## Adding the current run to the log file starting off with the header having the **** then the time in seconds ##
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
handler = logging.FileHandler(datetime.datetime.now().strftime('%Y-%m-%d'))
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.info("\n\n\t*********************************** \t"+datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+"\t*************************************")



## class responsible for the whole program
class SymantecAuth(AuthBase):
    #HTTP Authentication from DLP Server this method is from zeep library to auhtenticate with server
        def __init__(self, username, password, host):
            self.basic = HTTPBasicAuth(username, password)
            self.host = host

        def __call__(self, r):
            if r.url.startswith(self.host):
                return self.basic(r)
            else:
                return r
#main function that handles the release of incidents
def Handle_Errors():
            
            #Reading username and password and url and ip from config file for privacy and securtiy
            try:
                config = configparser.ConfigParser()
                config.read('DLP_Error_Handler.ini')
                wsdl = config ['CONNECTION']['SERVER_URL']
                username = config  ['CONNECTION']['USER_NAME']
                password = config['CONNECTION']['PASSWORD']
                server_ip_address = config ['CONNECTION']['SERVER_IP']
                logger.info('Read from DLP_Error_Handler.ini values:\n\tUsername: %s\n\tPassword: %s\n\tServer IP: %s\n\tURL: %s',username,password,server_ip_address,wsdl)


            except Exception as e:
                logger.error('Failed to read from DLP_Error_Handler.ini\nPlease make sure the file exists and is in the same path as the program.\nAlso Make Sure the parameters are correct',exc_info=True)   
                return False

        
            #creating sesion for persistance of log in and authentication
            session = Session()
            session.auth = SymantecAuth(username, password,server_ip_address)
            session.verify = False
            transport = Transport(session=session)
            logger.info("Connecting to URL: %s .....",wsdl)
            client = Client(wsdl=wsdl, transport=Transport(session=session))

            ## calling the function to delete the incidents from the database that have been correctly been released from the enforce server##
            Delete_Released_Incidents(client)
            ## calling the function to reset the incidents from the database that have failed to be released from the enforce server##
            UnRelease_Errored_Incidents(client)         
           
                
                
                
def Delete_Released_Incidents(client):
            ## Getting from database the incidents with released and approved booleans set to be true"
            try:
                releasedIncidents = DLP_DB.Get_All_Released_Incidents()
            except Exception as e:
                logger.error("Failed to connect to SQLITE DB\n Exception Message: ",str(e))
                return False
            try:
                ##getting from the enforce server these incidents to make sure they have been released successfully##
                incidentDetailsList = client.service.incidentDetail(incidentLongId=releasedIncidents , incidentId=0,includeHistory=True)
                ## extracting from json the incidents that have been successfuly released from enforce server##
                successfulIncidents = Get_Successful_Incidents(incidentDetailsList)
                i=0
                for successfulIncident in successfulIncidents:
                    # deleting each incident from the Database
                    DLP_DB.Delete_Incident(successfulIncident)
                    i+=1
                logger.info("Deleting released and Approved Incidents")
                logger.info("Deleted %i incidents",i)
                logger.info("Deleted Incidents with ids "+str(successfulIncidents))

            except Exception as e:
                logger.error("Failed to Retrieve Incidents due to authentication or connection error\n EXCEPTION MESSAGE: "+str(e))
                return False

def UnRelease_Errored_Incidents(client):
                # getting all incidents from database whether released or not
                try:
                    incidents = DLP_DB.Get_All_Incidents()
                except Exception as e:
                    logger.error("Failed to connect to SQLITE DB\n Exception Message: ",str(e))
                    return False
                try:
                    # getting all incidents from enforce server to update the failed ones in the database
                    incidentDetailsList = client.service.incidentDetail(incidentLongId=incidents , incidentId=0,includeHistory=False)
                    # helper method to extract ids from json
                    incidentIdsList = Get_All_IncidentsId(incidentDetailsList)
                    i=0
                    logger.info("UnReleasing Incidents ")
                    for incidentId in incidentIdsList:
                       #unreleasing the incidents
                       DLP_DB.UnRelease_Incident(incidentId)
                       i=i+1
                    logger.info("Unreleasing %i incidents",i)
                    logger.info("Unreleased Incidents with ids "+str(incidentIdsList))
                    
                except Exception as e:
                     logger.error("Failed to Retrieve Incidents due to authentication or connection error\n EXCEPTION MESSAGE: "+str(e))
                     return False

#helper method to extract from json the successful incident ids
def Get_Successful_Incidents(incidentDetailsList):
            successfulIncidents=[]
            for incident in incidentDetailsList:
                        incidentHistory = incident["incident"]["incidentHistory"]
                        for event in incidentHistory :
                            # checking for success code whic is 26
                            if (event["actionType"]["actionTypeId"] == config  ['CONNECTION']['SUCCESS_RESPONSE_CODE']):
                                successfulIncidents.append(incident["incident"]["incidentId"])
            return successfulIncidents


#helper method to extract from json the incidents id that have failed
def Get_All_IncidentsId(incidentDetailsList):
            incidentsId=[]
            for incident in incidentDetailsList:
                    incidentsId.append(incident["incident"]["incidentId"])
            return incidentsId


Handle_Errors()
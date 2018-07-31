import DLP_eMail
import DLP_DB
import configparser
import re

config = configparser.ConfigParser()
config.read('DLP_eMail_Config.ini')

quarantine_subject_regex = config['REGEX']['QUARANTINE_SUBJECT_REGEX']
approve_subject_regex = config['REGEX']['APPROVE_SUBJECT_REGEX']
disapprove_subject_regex = config['REGEX']['DISAPPROVE_SUBJECT_REGEX']
new_incidents_mail_from = config['REGEX']['NEW_INCIDENTS_MAIL_FROM']
dlp_script_mailbox = config['CONNECTION']['IMAP_USERNAME']

new_emails = DLP_eMail.Fetch_New_eMails()
#print(new_emails)

if(len(new_emails)>0):
    new_emails.reverse()
    for new_email in new_emails:
        if(new_incidents_mail_from.lower() in new_email[0].lower() and quarantine_subject_regex.lower() in new_email[3].lower() and dlp_script_mailbox.lower() in new_email[2].lower()):
            search_obj = re.search(r"\d{1,9}",new_email[3])
            print(search_obj)
            if(search_obj!=None):
                incident_id = search_obj.group()
                print(incident_id)
                DLP_DB.Add_New_Incident(incident_id,new_email[4],new_email[1].lower())

        elif(dlp_script_mailbox.lower() in new_email[1].lower() and approve_subject_regex.lower() in new_email[3].lower()):
            search_obj = re.search(r"\d{1,9}",new_email[3])
            print(search_obj)
            if(search_obj!=None):
                incident_id = search_obj.group()
                print(incident_id)
                search_obj = re.search(r"<.*>",new_email[0].lower())
                print(search_obj)
                if(search_obj!=None):
                    owner_email = search_obj.group()
                    print(owner_email)
                    if(DLP_DB.Search_Incident(incident_id,owner_email)):
                        DLP_DB.Approve_Incident(incident_id)
                    
                

import requests
#import re
import configparser
###----------------------------------------------------------------------------------------------------------------------------###    
def Login():
    
    config = configparser.ConfigParser()
    config.read("DLP_Web_Config.ini")

    web_server = config["CONNECTION"]["WEB_SERVER"]
    web_username = config["CONNECTION"]["WEB_USERNAME"]
    web_password = config["CONNECTION"]["WEB_PASSWORD"]
    web_domain = config["CONNECTION"]["WEB_DOMAIN"]

    post_request_url = "https://" + web_server + "/ProtectManager/j_security_check"

    post_request_data = {}
    post_request_data["username"] = web_username
    post_request_data["j_username"] = web_username + ":" + web_domain
    post_request_data["j_password"] = web_password
    post_request_data["domain"] = web_domain

    session_id = ""
    
    try:
        post_request = requests.post(post_request_url , allow_redirects = False , verify = False , data = post_request_data)
        if (post_request.headers["Location"]=="/ProtectManager/"):
            session_id = post_request.cookies["JSESSIONID"]
        else:
            print("Login Failed")
    except:
        print("Login Exception")

    return session_id
###----------------------------------------------------------------------------------------------------------------------------###
def Logout(inSessionID,inCSRFToken):
    
    config = configparser.ConfigParser()
    config.read("DLP_Web_Config.ini")

    web_server = config["CONNECTION"]["WEB_SERVER"]
    web_user_agent = config["CONNECTION"]["WEB_USER_AGENT"]

    post_request_url = "https://" + web_server + "/ProtectManager/Logoff"

    post_request_data = {}
    post_request_data["userid"] = 1
    post_request_data["type"] = "STANDARD"
    post_request_data["csrfProtectionToken"] = inCSRFToken
    post_request_data["value(csrfProtectionToken)"] = inCSRFToken

    post_request_headers = {}
    post_request_headers["User-Agent"] = web_user_agent
    

    post_request_cookies = {}
    post_request_cookies["JSESSIONID"] = inSessionID
    
    try:
        post_request = requests.post(post_request_url, data = post_request_data , allow_redirects = False , verify = False , cookies = post_request_cookies , headers = post_request_headers)
        print(post_request.text)
        if (post_request.status_code == requests.codes.FOUND):
            if(post_request.headers["Location"] == "/ProtectManager/GlobalDialog?type=LOGOFF_SUCCESS"):
                print("Logout Done")
            else:
                print("Logout Error Page")
        else:
            print("Logout Error Page")
    except:
        print("Logout Exception")

    return
###----------------------------------------------------------------------------------------------------------------------------###    
def Get_CSRF(inSessionID):
    
    config = configparser.ConfigParser()
    config.read("DLP_Web_Config.ini")

    web_server = config["CONNECTION"]["WEB_SERVER"]
    web_user_agent = config["CONNECTION"]["WEB_USER_AGENT"]
    
    get_request_url = "https://" + web_server + "/ProtectManager/enforce/ui/dashboard/endpoint"

    get_request_headers = {}
    get_request_headers["User-Agent"] = web_user_agent

    get_request_cookies = {}
    get_request_cookies["JSESSIONID"] = inSessionID

    csrf_token = ""

    try:
        get_request = requests.get(get_request_url , verify = False , cookies = get_request_cookies , headers = get_request_headers)
        if (get_request.status_code == requests.codes.ok):
            csrf_token = get_request.text.splitlines()[23][44:68]
            print(csrf_token)
    except:
        print("CSRF Exception")

    return csrf_token
###----------------------------------------------------------------------------------------------------------------------------###
def Approve_Incident(inSessionID , inIncidentIDs , inCSRFToken):

    config = configparser.ConfigParser()
    config.read("DLP_Web_Config.ini")

    web_server = config["CONNECTION"]["WEB_SERVER"]
    web_user_agent = config["CONNECTION"]["WEB_USER_AGENT"]

    post_request_url = "https://" + web_server + "/ProtectManager/UpdateExecuteResponseRule.do"

    post_request_data = {}
    post_request_data["value(ruleID)"] = 65
    post_request_data["value(incidentIDs)"] = inIncidentIDs
    post_request_data["value(reportType)"] = "NETWORK"
    post_request_data["csrfProtectionToken"] = inCSRFToken
    post_request_data["value(csrfProtectionToken)"] = inCSRFToken
    post_request_data["value(state_menuID)"] = "network.3"
    post_request_data["value(state_selectedTab)"] = "undefined"
    
    print(post_request_data)
    print("*****************")

    post_request_headers = {}
    post_request_headers["User-Agent"] = web_user_agent
    #post_request_headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    #post_request_headers["Accept-Language"] = "en-US,en;q=0.5"
    #post_request_headers["Accept-Encoding"] = "gzip, deflate"
    #post_request_headers["Content-Type"] = "application/x-www-form-urlencoded"
    #post_request_headers["Referer"] = "https://" + web_server + "/ProtectManager/SelectResponseForManualExecute.do"
    #post_request_headers["Upgrade-Insecure-Requests"] = 1
    print(post_request_headers)
    print("*****************")
    

    post_request_cookies = {}
    post_request_cookies["JSESSIONID"] = inSessionID
    #post_request_cookies["snapshot-selected-tab-index"] = ""
    #post_request_cookies["uidevmode"] = 0

    print(post_request_cookies)
    print("*****************")

    try:
        post_request = requests.post(post_request_url, data = post_request_data , allow_redirects = False , verify = False , cookies = post_request_cookies , headers = post_request_headers)
        print(post_request.text)
        print(post_request.headers["Location"])
        if (post_request.status_code == requests.codes.FOUND):
            if(post_request.headers["Location"] != "/ProtectManager/enforce/navigate?menuID=error_page"):
                return True
            else:
                return False
        else:
            return False
    except:
        return False

    return False
###----------------------------------------------------------------------------------------------------------------------------###
def Get_Incident(inSessionID , inIncidentID , inCSRFToken):

    config = configparser.ConfigParser()
    config.read("DLP_Web_Config.ini")

    web_server = config["CONNECTION"]["WEB_SERVER"]
    web_user_agent = config["CONNECTION"]["WEB_USER_AGENT"]

    get_request_url = "https://" + web_server + "/ProtectManager/IncidentDetail.do"

    get_request_data = {}
    get_request_data["value(variable_1)"] = "incident.id"
    get_request_data["value(operator_1)"] = "incident.id_in"
    get_request_data["value(operand_1)"] = inIncidentID
    get_request_data["value(state_menuID)"] = "network.3"

    
    print(get_request_data)
    print("*****************")

    get_request_headers = {}
    get_request_headers["User-Agent"] = web_user_agent
    print(get_request_headers)
    print("*****************")
    

    get_request_cookies = {}
    get_request_cookies["JSESSIONID"] = inSessionID


    print(get_request_cookies)
    print("*****************")

    try:
        get_request = requests.get(get_request_url, params = get_request_data , allow_redirects = False , verify = False , cookies = get_request_cookies , headers = get_request_headers)
        #print(get_request.text)
        #print(post_request.headers["Location"])
        #if (post_request.status_code == requests.codes.FOUND):
        #    if(post_request.headers["Location"] != "/ProtectManager/enforce/navigate?menuID=error_page"):
         #       print("done")
          #  else:
           #     print("error page")
        #else:
         #   print("failed")
    except:
        print("Fuck")

    return
###----------------------------------------------------------------------------------------------------------------------------###
def PreApprove_Incident(inSessionID , inIncidentIDs , inCSRFToken):

    config = configparser.ConfigParser()
    config.read("DLP_Web_Config.ini")

    web_server = config["CONNECTION"]["WEB_SERVER"]
    web_user_agent = config["CONNECTION"]["WEB_USER_AGENT"]

    post_request_url = "https://" + web_server + "/ProtectManager/SelectResponseForManualExecute.do"

    post_request_data = {}
    post_request_data["value(responseRuleID)"] = 65
    post_request_data["value(incidentIDs)"] = inIncidentIDs
    post_request_data["value(reportType)"] = "NETWORK"
    post_request_data["csrfProtectionToken"] = inCSRFToken
    post_request_data["value(csrfProtectionToken)"] = inCSRFToken
    post_request_data["value(state_menuID)"] = "network.3"
    post_request_data["value(incidentID)"] = inIncidentIDs
    post_request_data["value(variable_1)"] = "incident.id"
    post_request_data["value(operator_1)"] = "incident.id_in"
    post_request_data["value(operand_1)"] = inIncidentIDs
    
    print(post_request_data)
    print("*****************")

    post_request_headers = {}
    post_request_headers["User-Agent"] = web_user_agent
    #post_request_headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    #post_request_headers["Accept-Language"] = "en-US,en;q=0.5"
    #post_request_headers["Accept-Encoding"] = "gzip, deflate"
    #post_request_headers["Content-Type"] = "application/x-www-form-urlencoded"
    #post_request_headers["Referer"] = "https://" + web_server + "/ProtectManager/SelectResponseForManualExecute.do"
    #post_request_headers["Upgrade-Insecure-Requests"] = 1
    print(post_request_headers)
    print("*****************")
    

    post_request_cookies = {}
    post_request_cookies["JSESSIONID"] = inSessionID
    #post_request_cookies["snapshot-selected-tab-index"] = ""
    #post_request_cookies["uidevmode"] = 0

    print(post_request_cookies)
    print("*****************")

    try:
        post_request = requests.post(post_request_url, data = post_request_data , allow_redirects = False , verify = False , cookies = post_request_cookies , headers = post_request_headers)
        #print(post_request.text)
        #print(post_request.headers["Location"])
        if (post_request.status_code == requests.codes.OK):
            #if(post_request.headers["Location"] != "/ProtectManager/enforce/navigate?menuID=error_page"):
            print("done")
            #else:
            #    print("error page")
        else:
            print("failed")
    except:
        print("Fuck")

    return 
###----------------------------------------------------------------------------------------------------------------------------###
def Release_Incidents(inIncidentsIDsList):
    released = False
    
    session_id = Login()
    if (session_id != ""):
        csrf_token = Get_CSRF(session_id)
        #Get_Incident(Session_ID,1416,csrf1)
        PreApprove_Incident(session_id,inIncidentsIDsList[0],csrf_token)

        if(len(inIncidentsIDsList)>1):
            inIncidentsIDsSet = ",".join(inIncidentsIDsList)
        else:
            inIncidentsIDsSet = inIncidentsIDsList[0]

        released = Approve_Incident(session_id,inIncidentsIDsSet,csrf_token)

        Logout(session_id,csrf_token)

    return released

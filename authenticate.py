from requests import Session
from zeep import Client
from zeep.transports import Transport
from requests.auth import AuthBase, HTTPBasicAuth
import datetime
import uuid

class SymantecAuth(AuthBase):
    def __init__(self, username, password, host):
        self.basic = HTTPBasicAuth(username, password)
        self.host = host

    def __call__(self, r):
        if r.url.startswith(self.host):
            return self.basic(r)
        else:
            return r


wsdl = 'https://192.168.1.233/ProtectManager/services/v2011/incidents?wsdl'

session = Session()
session.auth = SymantecAuth('Administrator', 'P@ssw0rd', "https://192.168.1.233")

session.verify = False
transport = Transport(session=session)


client = Client(wsdl=wsdl, transport=Transport(session=session))


print(client.service.incidentDetail(incidentLongId=1362 , incidentId=3, incidentAttributes=,includeHistory=True))

batchIdUid = uuid.uuid4()
batchId = str(batchIdUid)
print(5)
#!/usr/bin/python
import imaplib
import socket
import re
import email
import datetime
import random
import urllib2
from urllib import urlencode
import sqlite3 as lite
import smtplib
import logging
import os
import signal
import time
#imaplib.Debug = 4


# Username and Password of DLP mailbox
USERNAME = "Em.dlp"
PASSWORD = "*****"

SENDER = "EMD@etisalat.com"
RECEIVERS = ["EnterpriseSystemsSecurity.eg@etisalat.com"]

# choose random host from 4 mail server
SERVERS = [
    "caincehc01.eg01.etisalat.net",
    "caincehc02.eg01.etisalat.net",
    "caincehc03.eg01.etisalat.net",
    "caincehc04.eg01.etisalat.net"
]

# DLP Release Or Discard Approval Justifications
JUSTIFICATIONS = {
    '1': "My manager approved this transfer",  # Approval to Release
    '2': "One time exception has been authorized",  # Approval to Release
    '3': "Data is not confidential",  # Approval to Release
    '4': ""  # Approval to Discard
}

RELEASE_DISCARD_IDS = ['0', '1']

RELEASE_COMMENTS_IDS = ['1', '2', '3']
DISCARD_COMMENTS_IDS = ['4']

APPROVED = 1
NOT_APPROVED = 0

RELEASE = 1
RELEASE_ID = '1'

DISCARD = 0
DISCARD_ID = '0'

NOT_IMPLEMENTED = 0
IMPLEMENTED = 1

EXPIRY_DAYS = 3  # three days before mail to be discarded
RETENTION_DAYS = 180  # clean database records which is older than RETENTION_DAYS
RUN_EVERY_SEC = 5  # run the script every 120 second

DB_FILE = '/root/dlp-mail-approval/dlp-mail-approvals.db'
PID_FILE = '/root/dlp-mail-approval/dlp-mail-approvals.pid'
LOG_FILENAME = '/root/dlp-mail-approval/dlp-mail-approvals.log'

FORMAT = '%(asctime)s - %(name)s - %(levelname)s : %(message)s'
# Dec 29 20:10:20 r00t-XPS kernel: bbswitch: disabling discrete graphics

logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO,format=FORMAT, datefmt='%m/%d/%Y %I:%M:%S %p')
LOGGER = logging.getLogger('dlp_mail_approvals')

list_response_pattern = re.compile(r'\((?P<flags>.*?)\) "(?P<delimiter>.*)" (?P<name>.*)')


def send_mail(mail_server, sender, receivers, content):

  SERVER = mail_server

  FROM = sender
  TO = receivers

  SUBJECT = "DLP Mail Approval"

  TEXT = "Dear Team,\nkindly check the below message from DLP Mail Approval Script which is hosted on 10.203.201.201.\n"+content

# Prepare actual message

  message = """\
From: %s
To: %s
Subject: %s

%s
""" % (FROM, ", ".join(TO), SUBJECT, TEXT)


  try:
    smtpObj = smtplib.SMTP(host=mail_server)
    smtpObj.sendmail(sender, receivers, message)
    LOGGER.info("Successfully sent Email")
  except smtplib.SMTPException, e:
    LOGGER.error("Couldnot Send Mail", exc_info=True)


def parse_list_response(line):
  flags, delimiter, mailbox_name = list_response_pattern.match(line).groups()
  mailbox_name = mailbox_name.strip('"')
  return (flags, delimiter, mailbox_name)


def list_all_directories(mail):
  LOGGER.debug("Listing All Directories:")
  typ, data = mail.list()
  LOGGER.debug('Response code:%s', typ)
  for line in data:
    LOGGER.debug('Server response:%s', line)
    flags, delimiter, mailbox_name = parse_list_response(line)
    LOGGER.debug('Parsed response:%s', (flags, delimiter, mailbox_name))


def get_summary(mail):
  LOGGER.debug("Summary Of All Folders:")
  typ, data = mail.list()
  for line in data:
    flags, delimiter, mailbox_name = parse_list_response(line)
    LOGGER.debug(mail.status(mailbox_name, '(MESSAGES RECENT UIDNEXT UIDVALIDITY UNSEEN)'))


def search_mailbox(mail, search_subject, regex_pattern):

  LOGGER.debug('Search in mailbox For Mail Subject:%s', search_subject)
  LOGGER.debug("Get Mail and match for Regex:%s", regex_pattern)
  msgids = []
  list_msg_content = []  # list of dictionaries, each on is message contnent

  typ, mailbox_data = mail.list()
  for line in mailbox_data:
    flags, delimiter, mailbox_name = parse_list_response(line)
    if 'Noselect' not in flags:
      mail.select(mailbox_name, readonly=False)
      typ, msg_ids = mail.search( None, '(UNSEEN SUBJECT "%s")' % search_subject)
      # print mailbox_name, typ, msg_ids
      # splitting msg ids from space separated string to list
      id_list = msg_ids[0].split()
      if len(id_list) == 0 or '' in id_list:
        continue
      else:
        msgids.extend(id_list)

      for i in msgids:
                # dictonary contain message details
        msg_content = {'Subject': '', 'Date': '', 'Pattern': [], 'LocalDate': ''}

        rv, data = mail.fetch(i, '(RFC822)')
        if rv != 'OK':
          LOGGER.warning("ERROR getting message ID[%s]", i)

        # if data is not None or data[0] is not None:#There is Message and not
        # None
        if all(x is not None for x in data):
          msg = email.message_from_string(data[0][1])
          # msg = email.message_from_bytes(data[0][1])
          # print "MSG:",msg
          partCounter = 1
          for part in msg.walk():
            if part.get_content_maintype() == "multipart":
              continue
            name = part.get_param("name")
            if name == None:
              name = "part-%i" % partCounter
            partCounter += 1
            htmlpart = part.get_payload(decode=1)
            # print "Part: ", htmlpart
            for regex in regex_pattern:
              pattern = re.search(regex, htmlpart)
              if pattern:
                LOGGER.debug("Pattern: %s", pattern.group(0))
                msg_content['Pattern'].append(pattern.group(0))

          typ, data = mail.store(i, '+FLAGS', '\Seen')

          # print 'Message %s: %s' % (i, msg['Subject'])
          msg_content['Subject'] = msg['Subject']
          # print 'Raw Date:', msg['Date']
          msg_content['Date'] = msg['Date']
          date_tuple = email.utils.parsedate_tz(msg['Date'])
          if date_tuple:
            local_date = datetime.datetime.fromtimestamp(
                email.utils.mktime_tz(date_tuple))
            # print "Local Date:", local_date.strftime("%Y-%m-%d")
            msg_content['LocalDate'] = local_date.strftime("%Y-%m-%d")

          list_msg_content.append(msg_content)

  return list_msg_content


def get_notifications(mail):
  notifications = search_mailbox(mail, search_subject=r'Attention - Sensitive Data Discovered - Action Needed',
                                 regex_pattern=[r'https.*incidentId=\d+&amp;ticket=.{43}',
                                                r'<br>From:(.*)<br>To:(.*)<br>Subject:(.*)<br>Case'])
  for notification in notifications:
    if len(notification['Pattern']) == 2 and 'ticket' in notification['Pattern'][0]:
      LOGGER.debug("Notification Pattern:%s", notification['Pattern'])
      incident_id, ticket = re.search(r'incidentId=(\d+)&amp;ticket=(.{43})', notification['Pattern'][0]).groups()

      mail_from, mail_to, subject = re.search(r'<br>From:(.*)<br>To:(.*)<br>Subject:(.*)<br>Case',  notification['Pattern'][1]).groups()
      #mail_from = re.sub('<.*?>', '', mail_from)
      mail_from = mail_from.strip()
      mail_to = mail_to.strip()
      subject = subject.strip()#buffer below to handle arabic subject
      data_tuble = (int(incident_id), mail_from, mail_to, buffer(subject),notification['Date'], notification['LocalDate'], ticket)
      # write to database
      with lite.connect(DB_FILE) as con:
        cur = con.cursor()
        # approved, releasedOrDiscarded, comments will be fulfilled with approval msg
        # insert the details of notification or ignore it if it exist
        cur.execute("select incidentid from INCIDENTS where incidentid = {0};".format(incident_id))
        results = cur.fetchone()
        LOGGER.debug("NOTIFICATION Result:%s", results )

        # if incident exist
        if results != None:
          LOGGER.info( "Incident no[%s]: Already Existed in Database", incident_id)
        else:
          LOGGER.info("Incident no[%s]: Recieved Notification and Waiting for Approval", incident_id)
          LOGGER.debug("Incident no[%s]: %s", incident_id, data_tuble)
          cur.execute("INSERT OR IGNORE INTO INCIDENTS(incidentId, mailFrom, mailTo, subject, date, localDate,ticket)VALUES(?,?,?,?,?,?,?);", data_tuble)


def get_apptovals(mail):
  # search for user approval message
  approval_msgs = search_mailbox(mail, search_subject=r'ETISALAT_DLP_APPROVAL_MSG', regex_pattern=[
                                 r'ETISALAT_DLP_APPROVAL_MSG:.*\d:\d+:\d'])
  LOGGER.debug(approval_msgs)

  for msg in approval_msgs:
    LOGGER.debug("Approval Pattern:%s", msg['Pattern'])
    # check Approval Mail to contain Pattern, if not found pass to next
    # mail
    if len(msg['Pattern']) != 1:
      continue

    pattern = msg['Pattern'][0]
    LOGGER.debug("Pattern with html: %s", pattern)
    pattern = re.sub('<.*?>', '', pattern)
    LOGGER.debug("Pattern without html: %s", pattern)
    release_or_discard, incident_id, comment_id = re.search('ETISALAT_DLP_APPROVAL_MSG:(\d):(\d+):(\d)', pattern).groups()
    LOGGER.debug("Extracted from Pattern release/discard:%s IncidentId:%s CommentId:%s", release_or_discard, incident_id, comment_id)

    #check if approval mail have a valid release or discard [0,1]
    if release_or_discard not in RELEASE_DISCARD_IDS:
      LOGGER.warning("Incident no[%s]: User Tried Invalid Release or Discard ID[%s]", incident_id, release_or_discard)
      return

    try:
      comments = JUSTIFICATIONS[comment_id]

      if release_or_discard == DISCARD_ID and comment_id not in DISCARD_COMMENTS_IDS: # User Chose to Discard but changed Comment ID other than 4
        LOGGER.warning("Inciden no[%s]: Invalid Comments[%s] with Discard", incident_id, comments)
        return
      elif release_or_discard == RELEASE_ID and comment_id not in RELEASE_COMMENTS_IDS: #User chose to release but changed Comment ID other than [1,2,3]
        LOGGER.warning("Inciden no[%s]: Invalid Comments[%s] with Release", incident_id, comments)
        return
    except KeyError,e:
      LOGGER.warning("Inciden no[%s]: Invalid Comment ID[%s]", incident_id, comment_id)
      return
    except Exception, e:
      LOGGER.error("Incident no[%s]: Invalid Release or Discard ID[%s] and Comment ID [%s]", incident_id, release_or_discard, comment_id, exc_info=True)
      return
            
    # write to database
    with lite.connect(DB_FILE) as con:
      cur = con.cursor()
      cur.execute("SELECT incidentId  FROM INCIDENTS where (incidentId in (select incidentId from INCIDENTS where incidentId ={0}));".format(incident_id))
      results = cur.fetchone()
      if results != None:      #check if there is notification for this incidentid else ignore the approval
        LOGGER.debug("Inciden no[%s]: Notification Found", incident_id)
        cur.execute("SELECT incidentId  FROM INCIDENTS where (incidentId in (select incidentId from INCIDENTS where incidentId ={0} and localdate >= date('now', '-{1}day')));".format(incident_id, EXPIRY_DAYS))
        results = cur.fetchone()
        if results != None:       #check if incident is not expired else ignore the approval
          LOGGER.debug("Inciden no[%s]: Not Expired Yet", incident_id)
          cur.execute("SELECT incidentId  FROM INCIDENTS where (incidentId in (select incidentId from INCIDENTS where incidentId ={0} and approved = {1} and localdate >= date('now', '-{2}day')));".format(incident_id, NOT_APPROVED, EXPIRY_DAYS))
          results = cur.fetchone()
          if results != None:      #check if there is incident not approved else ignore the approval
            LOGGER.debug("Inciden no[%s]: Not Approved Yet", incident_id)
            cur.execute("UPDATE INCIDENTS SET approved = ?, releasedOrDiscarded = ?, comments = ? where incidentId = ? and (approved = ?);",(APPROVED, release_or_discard, comments, incident_id, NOT_APPROVED))
            LOGGER.info("Incident no[%s]: Approved with comment[%s]", incident_id, comments)

            cur.execute("SELECT incidentId,releasedOrDiscarded,comments, ticket FROM INCIDENTS where (incidentId = {0} and approved = {1} );".format(incident_id, APPROVED))
            results = cur.fetchone()
            if results != None:              
              finished = construct_release_or_discard_url(results[0], results[1], results[2], results[3])#return true or false
              if finished:
                cur.execute("UPDATE INCIDENTS SET implemented = ? where incidentId = ? and (approved = ?);",(IMPLEMENTED, results[0], APPROVED))
                LOGGER.info("Incident no[%s]: Action Has been Taken by DLP",results[0])
              else:
                LOGGER.warning("Incident no[%s]: Approved with comment[%s] but Action not Implemented Yet", results[0], results[2])
          else:
            LOGGER.warning("Inciden no[%s]: Approved Before", incident_id)    
        else:
          LOGGER.warning("Inciden no[%s]: Expired", incident_id)  
      else:
        LOGGER.warning("Inciden no[%s]: No Previous Notification", incident_id)



#for incidents that approved but have faced a problem and the action taken by the user not implemented by DLP
def implement_approved_incidents():
  with lite.connect(DB_FILE) as con:
    cur = con.cursor()
    cur.execute("SELECT incidentId,releasedOrDiscarded,comments, ticket FROM INCIDENTS where (approved = {0} and implemented = {1});".format(APPROVED, NOT_IMPLEMENTED))
    rows = cur.fetchall()
    
    #get all incidents that approved but not implemented
    for row in rows:
      results = row   
      if results != None:
        incident_id = results[0]
        finished = construct_release_or_discard_url(results[0], results[1], results[2], results[3])#return true or false
        if finished:         
          cur.execute("UPDATE INCIDENTS SET implemented = ? where incidentId = ? and (approved = ?);",(IMPLEMENTED, incident_id, APPROVED))
	  LOGGER.info("Incident no[%s]: Action Has been Taken by DLP",results[0])



def construct_release_or_discard_url(incident_id, release_or_discard, comments, ticket):

  parms = {'incidentId': incident_id, 'comments': comments, 'ticket': ticket}
  url = ''
  implemented = False
  if release_or_discard == RELEASE:
    url = "https://CAINCEMP02.EG01.Etisalat.net:443/notification/quarantineselfreleaserelease.html?%s" % (urlencode(parms))
    try:
      (message, finished) = release_or_discard_url(url)
      LOGGER.info("Incident no[%s]: Return Message [%s]", incident_id, message)
      implemented = finished
    except urllib2.URLError, e:
      LOGGER.error("Incident no[%s]: Couldnot be Released.", incident_id, exc_info=True)      
    except httplib.BadStatusLine:
      LOGGER.error("Incident no[%s]: unknow HTTP status, Check DLP Services for hanged service", incident_id, exc_info=True)    
  elif release_or_discard == DISCARD:
    url = "https://CAINCEMP02.EG01.Etisalat.net:443/notification/quarantineselfreleasediscard.html?%s" % (urlencode(parms))
    try:
      (message, finished) = release_or_discard_url(url)
      LOGGER.info("Incident no[%s]: Return Message [%s]", incident_id, message)
      implemented = finished
    except urllib2.URLError, e:
      LOGGER.error("Incident no[%s]: Couldnot be Discarded.", incident_id, exc_info=True)
    except httplib.BadStatusLine:
      LOGGER.error("Incident no[%s]: unknown HTTP status, Check DLP Services for hanged service", incident_id, exc_info=True)
  else:
    LOGGER.warning("Incident no[%s]: Invalid Release or Discard [%s]", incident_id, release_or_discard)

  return implemented


def release_or_discard_url(url):

  req = urllib2.Request(url)
  req.add_header('Cookie', 'JSESSIONID=y4lzwhwk73sc1mwzj1g3dt5mq')
  req.add_header('Host', 'caincemp02.eg01.etisalat.net:443')
  req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36')
  req.add_header('Accept', 'text/css,*/*;q=0.1')
  req.add_header('Accept-Encoding', 'gzip, deflate, sdch')
  req.add_header('Accept-Language', 'en-US,en;q=0.8')
  req.add_header('Upgrade-Insecure-Requests', '1')
  resp = urllib2.urlopen(req)
  page = resp.read()
  code = resp.getcode()
  finished = False
  
  if code == 200:
    finished = True

  message = re.search(r'<span class="quarantineMessage">.*<strong>(.*)</strong>', page, re.DOTALL)
  message = message.group(1)
  message = re.sub(r'\n', '', message)
  message = re.sub(r'\t', '', message)
  message = message.strip()
  return (message,finished)
      

def clean_database(retention_days):
  with lite.connect(DB_FILE) as con:
    cur = con.cursor()
    cur.execute(
        "SELECT * FROM INCIDENTS where (incidentId in (select incidentId from INCIDENTS where localdate < date('now','-{0}day')));".format(retention_days))
    results = cur.fetchone()
    # check if there are incidents older than retention period
    if results != None:
      LOGGER.info(
          "Cleaning Database: removing Records Older than Retention Period[%s].", retenion_days)
      cur.execute(
          "DELETE FROM INCIDENTS where (incidentId in (select incidentId from INCIDENTS where localdate < date('now','-{0}day')));".format(retention_days))

def signal_handler(signum, frame):
  LOGGER.error('PID[%s] Received Signal [%s] at Time[%s]',os.getpid(), signum, time.ctime())
  exit(1)

def main():
  signal.signal(signal.SIGINT, signal_handler)
  signal.signal(signal.SIGUSR1, signal_handler)
  signal.signal(signal.SIGTERM, signal_handler)
  signal.signal(signal.SIGHUP, signal_handler)

  #get pid which is needed by monit, to restart the script when it's stoped
  pid = str(os.getpid())
  #if pid file exist, means process is running
  if os.path.isfile(PID_FILE):
    old_pid = open(PID_FILE).read()
    if os.path.exists("/proc/%s"%old_pid):
      LOGGER.info("DLP Mail Approval is Already Running with PID[%s]",old_pid)
      exit(1)

  with open(PID_FILE, 'w') as f:
    f.write(pid)
    LOGGER.info("DLP Mail Approval Started with PID[%s]", pid)

  try:
    # infinite loop until the connection is established
    mail = None
    mail_server = ''
    while True:
      try:
        host = SERVERS[random.randint(0, len(SERVERS) - 1)]
        LOGGER.info("Connecting to Server[%s]", host)
        mail = imaplib.IMAP4_SSL(host)
        mail_server = host
        break  # Break the infinite loop when connection is done
      except socket.error, e:
        LOGGER.error("Error: can't open IMAP connection with[%s] ", host, exc_info=True)
        exit(1)

    try:
      LOGGER.info("Login using Username:%s", USERNAME)
      mail.login(USERNAME, PASSWORD)
    except imaplib.IMAP4.error, e:
      message = "Invalid Credentials Username:{0}, password:{1}".format(USERNAME, PASSWORD)
      LOGGER.error(message, exc_info=True)
      send_mail(mail_server, SENDER, RECEIVERS, message)  # send mail to check the password
      exit(1)

    while True:
      get_notifications(mail)
      get_apptovals(mail)
      implement_approved_incidents()
      clean_database(RETENTION_DAYS)
      time.sleep(1*60) #added to process mails every 1 minute

    try:
      mail.close()
      mail.logout()
      LOGGER.info("Closing connection...")
    except imaplib.IMAP4.error, e:
      LOGGER.error("Error: Couldnot close connection and logout", exc_info=True)
      exit(1)
  except Exception:#handling exception
    LOGGER.error("Exception happend:", exc_info=True)

  finally:
    os.unlink(PID_FILE)
    LOGGER.info("DLP Mail Approval Exited with PID[%s]", pid)


if __name__ == '__main__':
  main()


# https://pymotw.com/2/imaplib/
#sqlite>.restore dlp-mail-approval/dlp-mail-approvals.db
#sqlite>ALTER TABLE INCIDENTS ADD COLUMN implemented INTEGER DEFAULT 0;
#sqlite>select incidentid, approved, releasedordiscarded,implemented from incidents;
#sqlite> select incidentid, approved, releasedordiscarded,comments from incidents where approved = 1;
#sqlite> update incidents set implemented = 1 where approved = 1;
#sqlite> select incidentid, approved, releasedordiscarded,comments, implemented from incidents where approved = 1;


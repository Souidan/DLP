import imaplib
import email
import configparser

def Fetch_New_eMails():

    config = configparser.ConfigParser()
    config.read('DLP_eMail_Config.ini')

    imap_server = config['CONNECTION']['IMAP_SERVER']
    imap_username = config['CONNECTION']['IMAP_USERNAME']
    imap_password = config['CONNECTION']['IMAP_PASSWORD']
    imap_port = config['CONNECTION']['IMAP_PORT']

    new_messages = []

    try:    
        imap_connection = imaplib.IMAP4_SSL(host=imap_server,port=imap_port)
    except:
        print("Connection to Mail Server Failed")
        #print(sys.exc_info()[1])              
        return new_messages
    
    try:
        (return_code, capabilities) = imap_connection.login(imap_username, imap_password)
    except:
        print("Login to Failed")
        #print(sys.exc_info()[1])
        return new_messages
              
    imap_connection.select('inbox') # Select inbox or default namespace

    (return_code, messages) = imap_connection.search(None, '(ALL)')

    if return_code == 'OK':
        messages_list = messages[0].decode("utf-8").split()
        if(len(messages_list)>0):
            messages_set = ",".join(messages_list)

            for message_id in messages_list:
                print('Processing :', message_id)
                message_data = imap_connection.fetch(message_id,'(RFC822)')
                message_data = message_data[1][0][1]
                message_data = message_data.decode("utf-8")
                message_data = email.message_from_string(message_data)

                new_messages.append([message_data['From'],message_data['To'],message_data['Cc'],message_data['Subject'],message_data['Date']])

            imap_connection.copy(messages_set,'DLP')
            imap_connection.store(messages_set, '+FLAGS', '\\Deleted')
            imap_connection.expunge()
        
    imap_connection.close()

    return new_messages

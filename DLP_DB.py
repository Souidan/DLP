import sqlite3
import configparser

def Add_New_Incident(ID,Date,OwnerEmail):

    config = configparser.ConfigParser()
    config.read('DLP_DB_Config.ini')
    db_name = config['CONNECTION']['DB_NAME']
    print(db_name)
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    add_new_incident_tuple = (ID,Date,OwnerEmail,0,0)
    c.execute("INSERT INTO INCIDENTS VALUES (?,?,?,?,?)",add_new_incident_tuple)
    conn.commit()
    conn.close()

def Search_Incident(ID,OwnerEmail):

    config = configparser.ConfigParser()
    config.read('DLP_DB_Config.ini')
    db_name = config['CONNECTION']['DB_NAME']
    print(db_name)
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("SELECT * FROM INCIDENTS WHERE ID = ? AND OwnerEmail = ?",(ID,OwnerEmail))
    rows = c.fetchall()
    conn.commit()
    conn.close()
    if(len(rows)>0):
        return True
    else:
        return False

def Get_Unreleased_Incidents():
    config = configparser.ConfigParser()
    config.read('DLP_DB_Config.ini')
    db_name = config['CONNECTION']['DB_NAME']
    print(db_name)
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("SELECT ID FROM INCIDENTS WHERE Approved = ? AND Released = ?",(1,0))
    rows = c.fetchall()
    rows = [r[0] for r in rows]
    conn.commit()
    conn.close()
    return rows
    
def Approve_Incident(ID):

    config = configparser.ConfigParser()
    config.read('DLP_DB_Config.ini')
    db_name = config['CONNECTION']['DB_NAME']
    print(db_name)
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute( "UPDATE INCIDENTS SET Approved = ? WHERE ID = ?" , (1 , ID))
    conn.commit()
    conn.close()

def Release_Incident(ID):
    print(ID)
    config = configparser.ConfigParser()
    config.read('DLP_DB_Config.ini')
    db_name = config['CONNECTION']['DB_NAME']
    print(db_name)
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute( "UPDATE INCIDENTS SET Released = ? WHERE ID = ?" , (1 , ID))
    conn.commit()
    conn.close()


def UnRelease_Incident(ID):
    print(ID)
    config = configparser.ConfigParser()
    config.read('DLP_DB_Config.ini')
    db_name = config['CONNECTION']['DB_NAME']
    print(db_name)
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute( "UPDATE INCIDENTS SET Released = ? WHERE ID = ?" , (0 , ID))
    conn.commit()
    conn.close()

def Get_All_Released_Incidents():
    config = configparser.ConfigParser()
    config.read('DLP_DB_Config.ini')
    db_name = config['CONNECTION']['DB_NAME']
    print(db_name)
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute( "SELECT * FROM INCIDENTS WHERE Released = ? AND Approved =?" , (1,1))
    rows = c.fetchall()
    rows = [r[0] for r in rows]
    conn.commit()
    conn.close()
    return rows

def Delete_Incident(ID):
    print(ID)
    config = configparser.ConfigParser()
    config.read('DLP_DB_Config.ini')
    db_name = config['CONNECTION']['DB_NAME']
    print(db_name)
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute( "DELETE FROM INCIDENTS WHERE ID = ?" , (ID,))
    conn.commit()
    conn.close()

def Get_All_Incidents():
    config = configparser.ConfigParser()
    config.read('DLP_DB_Config.ini')
    db_name = config['CONNECTION']['DB_NAME']
    #print(db_name)
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute( "SELECT * FROM INCIDENTS")
    rows = c.fetchall()
    rows = [r[0] for r in rows]
    conn.commit()
    conn.close()
    return rows




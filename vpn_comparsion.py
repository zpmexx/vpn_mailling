from pyzabbix import ZabbixAPI
from dotenv import load_dotenv
import json
import os
import csv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from datetime import datetime
from collections import Counter

load_dotenv()

# Replace these with your actual Zabbix server details
zabbix_server = os.getenv('zabbix_server')
zabbix_username = os.getenv('zabbix_username')
zabbix_password = os.getenv('zabbix_password')
email_suffix = os.getenv('email_suffix')
from_address = os.getenv('from_address')
password = os.getenv('password')


now = formatDateTime = formatted_date = None
try:
    now = datetime.now()
    formatDateTime = now.strftime("%d/%m/%Y %H:%M")
    formatted_date = now.strftime("%Y-%m-%d")
except Exception as e:
    pass

#Connect to Zabbix API, data in .env file
zapi = ZabbixAPI(zabbix_server)
zapi.login(zabbix_username, zabbix_password)
print(f"Connected to Zabbix API Version {zapi.api_version()}")

# Example: Get a list of all hosts
hosts = zapi.host.get(output="extend")
print(f"Number of hosts in Zabbix: {len(hosts)}")

#Hosts\clients list
salonList = [host['name'] for host in hosts if len(host['name']) < 8]

# list of all clients to query
# with open ('vpnlist.txt', 'r') as file:
#     for line in file.readlines():
#         salonList.append(line.strip())
        
#salonList = ['A144']

zabix_dict = {}
sba_db_dict = {}

for host_name in salonList:
    host = zapi.host.get(filter={"host": host_name})
    
    if host:
        host_id = host[0]["hostid"]
        #get host ip address
        interfaces = zapi.hostinterface.get(hostids=host_id, output=["ip"])
        ip_address = interfaces[0]["ip"]
        zabix_dict[host_name] = ip_address
        #print(host_name,ip_address)

import pyodbc
load_dotenv()
sba_db_password = os.getenv('sba_db_password')
sba_db_user = os.getenv('sba_db_user')
db_server = os.getenv('db_server')
db_driver = os.getenv('db_driver')
sba_db_db = os.getenv('sba_db_db')
vpn_comparsion_adresses = os.getenv('vpn_comparsion_adresses')


cnxn = pyodbc.connect(f'Driver={db_driver};;Server={db_server};Database={sba_db_db};User ID={sba_db_user};Password={sba_db_password}')
cursor = cnxn.cursor()

cursor.execute("SELECT ST_NAZWA, AKTUALNE_IP from dbo.STANOWISKA where len(ST_NAZWA) < 8 and CFG_DATA >= DATEADD(DAY, -30, GETDATE()) and AKTYWNE = 'T'")
db_hosts = cursor.fetchall()

for host in db_hosts:
    sba_db_dict[host[0]] = host[1]
print(len(sba_db_dict))
print(len(zabix_dict))
# pierwsza jest w bazie (aktualna w teorii, druga zabix nieakutalna w teorii)
different_values = {k: (sba_db_dict[k], zabix_dict[k]) for k in sba_db_dict if k in zabix_dict and sba_db_dict[k] != zabix_dict[k]}
to_address = json.loads(vpn_comparsion_adresses)
print(different_values)

try:
    msg = MIMEMultipart()
    msg['From'] = from_address
    msg["To"] = ", ".join(to_address)
    msg['Subject'] = f"Sprawdzenie vpn ip SBA-IT <> ZABIX {formatDateTime}"
    
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""Porownanie IP ZABIX <> SBA IT: Problem z wysłaniem email - {str(e)}\n""")

if different_values:
    body = f"""
<table border="1" style="width:100%; border-collapse: collapse; text-align:center;">
    <tr>
        <th>Salon</th>
        <th>IP Poprawne SBA-IT (w teorii)</th>
        <th>IP Błędne ZABIX (w teorii)</th>
    </tr>
"""
    for k, v in different_values.items():
        body += f"""
    <tr>
        <td>{k}</td>
        <td style="color:green;">{v[0]}</td>
        <td style="color:red;">{v[1]}</td>
    </tr>
    """
    body += """
</table>
"""
else:
    body = '<p>Brak różnic w adresach IP.</p>'

#Attach the HTML body to the email
msg.attach(MIMEText(body, 'html'))

try:
    server = smtplib.SMTP('smtp-mail.outlook.com', 587)
    server.starttls()
    server.login(from_address, password)
    text = msg.as_string()
    server.sendmail(from_address, to_address, text)
    server.quit()    
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""{formatDateTime} Problem z wysłaniem maila - {str(e)}\n""")

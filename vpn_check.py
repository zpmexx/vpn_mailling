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
import pyodbc

load_dotenv()

# Replace these with your actual Zabbix server details
zabbix_server = os.getenv('zabbix_server')
zabbix_username = os.getenv('zabbix_username')
zabbix_password = os.getenv('zabbix_password')
email_suffix = os.getenv('email_suffix')
from_address = os.getenv('from_address')
to_address = os.getenv('to_address')
password = os.getenv('password')
db_server = os.getenv('db_server')
db_driver = os.getenv('db_driver')
db_sba = os.getenv('db_sba')



now = formatDateTime = formatted_date = None
try:
    now = datetime.now()
    formatDateTime = now.strftime("%d/%m/%Y %H:%M")
    formatted_date = now.strftime("%Y-%m-%d")
except Exception as e:
    pass

#Connect to Zabbix API, data in .env file
try:
    zapi = ZabbixAPI(zabbix_server)
    zapi.login(zabbix_username, zabbix_password)
    print(f"Connected to Zabbix API Version {zapi.api_version()}")

    # Example: Get a list of all hosts
    hosts = zapi.host.get(output="extend")
    print(f"Number of hosts in Zabbix: {len(hosts)}")
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""{formatDateTime} Problem z połączeniem z zabixem - {str(e)}\n""")

# Example: Check if a specific host has any items

#Hosts\clients list
salonList = []
try:
    conn = pyodbc.connect(f'DRIVER={db_driver};'
                        f'SERVER={db_server};'
                        f'DATABASE={db_sba};'
                        'Trusted_Connection=yes')

    # Create a cursor object
    cursor = conn.cursor()

    # Define the query
    query = """
        SELECT ST_NAZWA
        FROM dbo.STANOWISKA
        WHERE AKTUALNE_IP LIKE '172.38%'
        AND AKTYWNE LIKE 'T'
        AND LEN(ST_NAZWA) < 5
        OR ST_NAZWA = 'A010-1'
    """

    # Execute the query
    cursor.execute(query)

    # Fetch the results and append only the ST_NAZWA to the salonList
    for row in cursor.fetchall():
        salonList.append(row.ST_NAZWA)

    # Close the cursor and connection
    cursor.close()
    conn.close()
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""{formatDateTime} Problem z połaczeniem z baza danych - {str(e)}\n""")
        
# list of all clients to query OLD
# with open ('vpnlist.txt', 'r') as file:
#     for line in file.readlines():
#         salonList.append(line.strip())



#hosts dict to keep connection status value 0 - not connected, 1 - connected, 11 - no host found, 12 - no hisotrical data, 13 - no item zabbix[host,agent,available]
hostsDict = {}


# salonList = ['A144']
try:
    for host_name in salonList:
        host = zapi.host.get(filter={"host": host_name})

        if host:
            host_id = host[0]["hostid"]
            items = zapi.item.get(hostids=host_id, output="extend")
            # interfaces = zapi.hostinterface.get(hostids=host_id, output=["ip"])
            # ip_address = interfaces[0]["ip"]
            #print(f"Number of items for host '{host_name}': {len(items)}")
        else:
            #11
            hostsDict[host_name] = 11
            #print(f"No host found with name '{host_name}'")

        # Example: Get latest data for a specific item
        if items:
            item_key = "zabbix[host,agent,available]"  # Replace with your specific item key
            item = zapi.item.get(hostids=host_id, filter={"key_": item_key}, output="extend")
            
            if item:
                item_id = item[0]["itemid"]
                history = zapi.history.get(itemids=item_id, limit=10, output="extend", sortfield="clock", sortorder="DESC")
                #0/1
                if history:
                    #print(f"{host_name} - {history[0]['value']}")
                    hostsDict[host_name] = history[0]['value']
                else:
                    #12
                    print(f"No historical data found for item '{host_name}'")
                    hostsDict[host_name] = 12
                    
            else:
                #13
                print(f"No item found with key '{item_key}' for host '{host_name}'")
                hostsDict[host_name] = 13

    # Logout from the API
    zapi.user.logout()
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""{formatDateTime} Problem z odczytwaniem danych z zabixa - {str(e)}\n""")


# #count values in dict
count_dict = Counter(hostsDict.values())

#connected/disconected summary
summary_count_txt = f"{formatDateTime}\nLiczba połaczonych klientów: {count_dict['1']}, liczba rozłączonych: {count_dict['0']}\n"

connected_hosts = []
disconnected_hosts = []
error_dict = {}

#hosts status to lists/dict
for k,v in hostsDict.items():
    if v == '0':
        disconnected_hosts.append(k)
    elif v == '1':
        connected_hosts.append(k)
    else:
        error_dict[k] = v
        

mail_hosts_list = json.loads(to_address)

try:
    msg = MIMEMultipart()
    msg['From'] = from_address
    msg["To"] = ", ".join(mail_hosts_list)
    msg['Subject'] = f"Status VPN {formatDateTime}"
    
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f""" Problem z wysłaniem email - {str(e)}\n""")
        
disconnected_hosts.sort()

html_body = f"<p>{summary_count_txt}</p><p>{'<br>'.join(disconnected_hosts)}</p>"

# Attach the HTML body to the email
msg.attach(MIMEText(html_body, 'html'))

try:
    server = smtplib.SMTP('smtp-mail.outlook.com', 587)
    server.starttls()
    server.login(from_address, password)
    text = msg.as_string()
    server.sendmail(from_address, mail_hosts_list, text)
    server.quit()    
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""{formatDateTime} Problem z wysłaniem maila - {str(e)}\n""")




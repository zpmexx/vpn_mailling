from pyzabbix import ZabbixAPI
from dotenv import load_dotenv
import json
import os
import csv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
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

# Connect to Zabbix API, data in .env file
zapi = ZabbixAPI(zabbix_server)
zapi.login(zabbix_username, zabbix_password)
print(f"Connected to Zabbix API Version {zapi.api_version()}")

# Example: Get a list of all hosts
hosts = zapi.host.get(output="extend")
print(f"Number of hosts in Zabbix: {len(hosts)}")

# Example: Check if a specific host has any items

#Hosts\clients list
salonList = []

# list of all clients to query
with open ('vpnlist.txt', 'r') as file:
    for line in file.readlines():
        salonList.append(line.strip())

#hosts dict to keep connection status value 0 - not connected, 1 - connected, 11 - no host found, 12 - no hisotrical data, 13 - no item zabbix[host,agent,available]
hostsDict = {}

for host_name in salonList:
    host = zapi.host.get(filter={"host": host_name})

    if host:
        host_id = host[0]["hostid"]
        items = zapi.item.get(hostids=host_id, output="extend")
        print(f"Number of items for host '{host_name}': {len(items)}")
    else:
        #11
        hostsDict[host_name] = 11
        print(f"No host found with name '{host_name}'")

    # Example: Get latest data for a specific item
    if items:
        item_key = "zabbix[host,agent,available]"  # Replace with your specific item key
        item = zapi.item.get(hostids=host_id, filter={"key_": item_key}, output="extend")
        
        if item:
            item_id = item[0]["itemid"]
            history = zapi.history.get(itemids=item_id, limit=1, output="extend", sortfield="clock", sortorder="DESC")
            #0/1
            if history:
                print(f"{host_name} - {history[0]['value']}")
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

#count values in dict
count_dict = Counter(hostsDict.values())

#connected/disconected summary
summary_count_txt = f"{formatDateTime}\nLiczba połaczonych klientów: {count_dict['1']}, liczba rozłączonych: {count_dict['0']}\n"

connected_hosts = disconnected_hosts = []
error_dict = {}

#hosts status to lists/dict
for k,v in hostsDict.items():
    if v == '0':
        disconnected_hosts.append(k)
    elif v == '1':
        connected_hosts.append(k)
    else:
        error_dict[k] = v
        

with open ('connection_summary.txt', 'a') as file:
    file.write(summary_count_txt)

with open('list_connection_summary.txt', 'a') as file:
    file.write(summary_count_txt)
    file.write("Połączone salony:\n")
    file.write('\n'.join(connected_hosts) + '\n')
    file.write("Rozłączone salony:\n")
    file.write('\n'.join(disconnected_hosts) + '\n')

if error_dict:
    with open ('error.txt', 'a') as file:
        file.write(f"{formatDateTime}\n11 - no host found, 12 - no hisotrical data, 13 - no item zabbix[host,agent,available]\n")
        for k,v in error_dict.items():
            file.write(f"{k} - {v}\n")

#mail preparation and send
#email list of hosts

#tutaj lista salonow jest gotowa, wystarczy przygotowac maila i testować
#mail_hosts_list = [host.lower() + email_suffix for host in disconnected_hosts]

mail_hosts_list = ['ziemowitpalka@gmail.com','karol.piechura@cdrl.pl','kornelia.pawlicka@cdrl.pl','tomasz.walenciak@cdrl.pl','it@cdrl.pl']

try:
    msg = MIMEMultipart()
    msg['From'] = from_address
    msg["To"] = ", ".join(mail_hosts_list)
    msg['Subject'] = f"Test mail salony {formatDateTime}."
    
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f""" Problem z wysłaniem email - {str(e)}\n""")
body = "Test"
msg.attach(MIMEText(body, 'html'))
try:
    server = smtplib.SMTP('smtp-mail.outlook.com', 587)
    server.starttls()
    print(from_address,password)
    server.login(from_address, password)
    text = msg.as_string()
    server.sendmail(from_address, mail_hosts_list, text)
    server.quit()    
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""{formatDateTime} Problem z wysłaniem maila - {str(e)}\n""")







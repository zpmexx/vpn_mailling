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


# salonList = ['A144']

for host_name in salonList:
    host = zapi.host.get(filter={"host": host_name}, selectInterfaces=["interfaceid", "ip"])

    if host:
        ip_address = host[0]["interfaces"][0]["ip"]
        hostsDict[host_name] = ip_address
    else:
        #11
        hostsDict[host_name] = 11
        print(f"No host found with name '{host_name}'")

    # Example: Get latest data for a specific item

# Logout from the API
zapi.user.logout()


with open ('ip_list.txt', 'a') as file:
    for k,v in hostsDict.items():
        file.write(f"{k},{v}\n")


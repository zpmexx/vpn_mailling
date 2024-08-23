from pyzabbix import ZabbixAPI
from dotenv import load_dotenv
import json
import os
import csv

from datetime import datetime

load_dotenv()

# Replace these with your actual Zabbix server details
zabbix_server = os.getenv('zabbix_server')
zabbix_username = os.getenv('zabbix_username')
zabbix_password = os.getenv('zabbix_password')


# Connect to Zabbix API
zapi = ZabbixAPI(zabbix_server)
zapi.login(zabbix_username, zabbix_password)
print(f"Connected to Zabbix API Version {zapi.api_version()}")

# Example: Get a list of all hosts
hosts = zapi.host.get(output="extend")
print(f"Number of hosts in Zabbix: {len(hosts)}")

# Example: Check if a specific host has any items
host_name = "A154"  # Replace with the name of your host
host = zapi.host.get(filter={"host": host_name})

if host:
    host_id = host[0]["hostid"]
    items = zapi.item.get(hostids=host_id, output="extend")
    print(f"Number of items for host '{host_name}': {len(items)}")
else:
    print(f"No host found with name '{host_name}'")

# Example: Get latest data for a specific item
if items:
    item_key = "zabbix[host,agent,available]"  # Replace with your specific item key
    item = zapi.item.get(hostids=host_id, filter={"key_": item_key}, output="extend")
    
    if item:
        item_id = item[0]["itemid"]
        history = zapi.history.get(itemids=item_id, limit=1, output="extend", sortfield="clock", sortorder="DESC")
        if history:
            print(f"Latest data for '{item_key}': {history}")
        else:
            print(f"No historical data found for item '{item_key}'")
    else:
        print(f"No item found with key '{item_key}' for host '{host_name}'")

# Logout from the API
zapi.user.logout()
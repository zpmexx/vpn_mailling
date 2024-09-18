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

# db details


now = formatDateTime = formatted_date = formatDbDateTime = None
try:
    now = datetime.now()
    formatDateTime = now.strftime("%d/%m/%Y %H:%M")
    formatDbDateTime = now.strftime("%Y/%m/%d %H:%M")
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
    host = zapi.host.get(filter={"host": host_name})

    if host:
        host_id = host[0]["hostid"]
        items = zapi.item.get(hostids=host_id, output="extend")
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
                #print(history)
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

#count values in dict
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
        

with open ('connection_summary.txt', 'a') as file:
    file.write(summary_count_txt)

with open('connected_list.txt', 'a') as file:
    file.write(summary_count_txt)
    file.write('\n'.join(connected_hosts) + '\n')
    
with open('disconnected_list.txt', 'a') as file:
    file.write(summary_count_txt)
    file.write('\n'.join(disconnected_hosts) + '\n')

if error_dict:
    with open ('error.txt', 'a') as file:
        file.write(f"{formatDateTime}\n11 - no host found, 12 - no hisotrical data, 13 - no item zabbix[host,agent,available]\n")
        for k,v in error_dict.items():
            file.write(f"{k} - {v}\n")

#mail preparation and send
#email list of hosts

#tutaj lista salonow jest gotowa, wystarczy przygotowac maila i testować
mail_hosts_list = [host.lower() + email_suffix for host in disconnected_hosts]

#print(mail_hosts_list)

#mail_hosts_list = ['ziemowit.palka@cdrl.pl','karol.piechura@cdrl.pl','kornelia.pawlicka@cdrl.pl','tomasz.walenciak@cdrl.pl','it@cdrl.pl']
#mail_hosts_list = ['ziemowit.palka@cdrl.pl']

#mail_hosts_list = []


try:
    msg = MIMEMultipart()
    msg['From'] = from_address
    msg["To"] = ", ".join(mail_hosts_list)
    msg['Subject'] = f"Przypomnienie FortiClient"
    
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f""" Problem z wysłaniem email - {str(e)}\n""")
body = "Test"


html_body = """
<html>
    <body>
        <p>Dzień dobry, przypominamy o konieczności połączenia programu FortiClient podczas godzin pracy salonu. <b>Program ten jest niezbędny do poprawnego funkcjonowania systemu 
        (m.in. działania programu lojalnościowego, obsługi zwrotów, posiadania najnowszych przecen oraz promocji, łączności z centralą).</b>
        Aby włączyć program należy nacisnąć przycisk connect.</p>
        <p>
        <img src="cid:image1">
        <img src="cid:image2"></p>
        <p>Prawidłowo połączony program FortiClient posiada żółtą kłódkę na ikonie aplikacji na pasku zadań.</p>
        <p>
        <img src="cid:image3">
        <img src="cid:image4"></p>
        <p>Rozłączony program takowej kłódki nie posiada.</p>
        <p>
        <img src="cid:image5"></p>
        <p>Finalny status programu FortiClient, który działa poprawnie posiada wszystkie informacje jak na zdjęciu poniżej.</p>
        <p>
        <img src="cid:image6"></p>
         <p>Czasem zdarzy się jednak, że pomimo posiadania kłódki aplikacja nie działa poprawnie (jeśli występuje jeden z problemów opisanych wyżej), w takiej
    sytuacji w aplikacji może brakować "IP Address" lub nie są otrzymywane pakiety (Bytes Received oraz Bytes Sent).
    Aplikacje należy wtedy uruchomić ponownie "Disconnect", a potem "Connect". </p>
    <p>Wiadomość została wysłana automatycznie oraz powinna trafić tylko do salonów, które mają rozłączony program FortiClient.
    Prosimy nie odpowiadać na tego maila. Jeśli uważają Państwo, że nie powinni byli dostać tego maila, proszę skontaktować się z telefonicznie z działem IT pod numer 602 710 974
lub napisać zgłoszenie na SalonDesk.
    Wszelkie potrzebne informacje znajdą Państwo na stronie <a href="https://cdrl.sharepoint.com/sites/salondesk">SalonDesk</a></p>
    </body>
</html>
"""

# Attach the HTML body to the email
msg.attach(MIMEText(html_body, 'html'))



# List of images to embed
images = ['vpn_connect.png','vpn_connect2.png','vpn_correct.png', 'vpn_hiddencorrect.png', 'vpn_incorrect.png', 'vpn_status.png']
image_folder = 'images'
# Attach each image and give it a Content-ID
for i, image in enumerate(images):
    image_path = os.path.join(image_folder, image)
    try:
        with open(image_path, 'rb') as img_file:
            mime_image = MIMEImage(img_file.read())
            mime_image.add_header('Content-ID', f'<image{i+1}>')
            mime_image.add_header('Content-Disposition', 'inline', filename=image)
            msg.attach(mime_image)
    except Exception as e:
        with open('logfile.log', 'a') as file:
            file.write(f"{formatDateTime} Problem with embedding {image} - {str(e)}\n")

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


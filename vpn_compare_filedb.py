import pyodbc
from dotenv import load_dotenv
import json
import os
import smtplib
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage

load_dotenv()
sba_db_password = os.getenv('sba_db_password')
sba_db_user = os.getenv('sba_db_user')
db_server = os.getenv('db_server')
db_driver = os.getenv('db_driver')
sba_db_db = os.getenv('sba_db_db')
my_address = os.getenv('my_address')
from_address = os.getenv('from_address')

password = os.getenv('password')
now = formatDateTime = formatted_date = None
try:
    now = datetime.now()
    formatDateTime = now.strftime("%d/%m/%Y %H:%M")
    formatted_date = now.strftime("%Y-%m-%d")
except Exception as e:
    pass

cnxn = pyodbc.connect(f'Driver={db_driver};;Server={db_server};Database={sba_db_db};User ID={sba_db_user};Password={sba_db_password}')
cursor = cnxn.cursor()

cursor.execute("SELECT ST_NAZWA, AKTUALNE_IP, AKTYWNE from dbo.STANOWISKA ")
db_hosts = cursor.fetchall()
salonListFromDb = []
for host in db_hosts:
    if(len(host[0]) < 7) and host[1].startswith("172.38") and host[2] != "N":
        salonListFromDb.append(host[0].strip())
        print(host)

print(len(salonListFromDb))

salonListFromFile = []
with open ('vpnlist.txt', 'r') as file:
    for line in file.readlines():
        salonListFromFile.append(line.strip())
print(len(salonListFromFile))

missing_in_file = list(set(salonListFromDb) - set(salonListFromFile))

# Find items in salonListFromFile that are missing in salonListFromDb

missing_in_db = list(set(salonListFromFile) - set(salonListFromDb))

to_address = json.loads(my_address)
try:
    msg = MIMEMultipart()
    msg['From'] = from_address
    msg["To"] = ", ".join(to_address)
    msg['Subject'] = f"Sprawdzenie brakujacych VPN bidata vpnlist.txt {formatDateTime}"
    
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""Porownanie IP ZABIX <> SBA IT: Problem z wysłaniem email - {str(e)}\n""")

body = ""

if missing_in_file:
    body += "Braki w pliku vpnlist.txt na bidacie:\n"
    for host in missing_in_file:
        body+= f"{host}\n"
        
if missing_in_db:
    body += "Braki w bazie SBA-IT it mann:\n"
    for host in missing_in_db:
        body+= f"{host}\n"

if not body:
    body = "Brak braków. Wszystko ok."

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



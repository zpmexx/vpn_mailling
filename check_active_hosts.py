import pyodbc
from dotenv import load_dotenv
import json
import os
import smtplib
from datetime import datetime, timedelta
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
my_address = os.getenv('vpn_comparsion_adresses')
from_address = os.getenv('from_address')

password = os.getenv('password')
now = subtracted_formatted_date = formatDateTime = subtracted_date = formatted_date = None
try:
    now = datetime.now()
    formatted_date = now.strftime("%Y-%m-%d")
    formatDateTime = now.strftime("%d/%m/%Y %H:%M")
    subtracted_date = now - timedelta(days=7)
    subtracted_formatted_date = subtracted_date.strftime("%Y-%m-%d")
except Exception as e:
    pass


cnxn = pyodbc.connect(f'Driver={db_driver};;Server={db_server};Database={sba_db_db};User ID={sba_db_user};Password={sba_db_password}')
cursor = cnxn.cursor()

cursor.execute("SELECT ST_NAZWA, AKTYWNE, CFG_DATA from dbo.STANOWISKA WHERE len(ST_NAZWA) = 4 ORDER BY 3 DESC ")
hosts = cursor.fetchall()
activeList = []
inactiveList = []
inactiveWithT = [] #salony nieaktywne z flaga T (aktywne) w db
activeWithN = [] #salony aktywne z flaga N (niekatywne) w db
for host in hosts:
    if host[2] >= subtracted_formatted_date:
        activeList.append(host[0])
        if host[1] == 'N':
            activeWithN.append(host[0])
    else:
        inactiveList.append(host[0])
        if host[1] == 'T':
            inactiveWithT.append(host[0])

activeList.sort()
inactiveList.sort()
inactiveWithT.sort()
activeWithN.sort()

to_address = json.loads(my_address)
try:
    msg = MIMEMultipart()
    msg['From'] = from_address
    msg["To"] = ", ".join(to_address)
    msg['Subject'] = f"Aktywne salony lista {formatDateTime}"
    
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""Aktwyne salony check problem z wyslaniem email - {str(e)}\n""")

body = ''
for host in activeList:
    body += f'<p>{host}</p>'
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

#######################################################################################Tutaj podsumowanie błedów

print(f'Salony aktywne z N: {activeWithN}\nSalony nieaktywne z T: {inactiveWithT}\nSalony nieaktywne: {inactiveList}')

try:
    msg = MIMEMultipart()
    msg['From'] = from_address
    msg["To"] = ", ".join(to_address)
    msg['Subject'] = f"Podsumowanie nieaktywnych salonów IT Mann {formatDateTime}"
    
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""Aktwyne salony check problem z wyslaniem email - {str(e)}\n""")

body = ''
if activeWithN:
    body+='<h3>Salony akytwne, które są w archiwum IT mann:</h3>'
    for host in activeWithN:
        body += f'<p>{host}</p>'
        
if inactiveWithT:
    body+='<h3>Salony nieaktywne, które są aktywne w IT mann:</h3>'
    for host in inactiveWithT:
        body += f'<p>{host}</p>'
        
##niedzialajace salony, ale bierze takze z archiwum
# if inactiveList:
#     body+='<h3>Salony nieaktywne od ponad tygodnia:</h3>'
#     for host in inactiveList:
#         body += f'<p>{host}</p>'
#Attach the HTML body to the email

if not body:
    body = "<p>Brak błędów w IT Mann.</p>"

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
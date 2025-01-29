"""
Automatic script for fiscal reminder
"""
import os
import smtplib
import pyodbc
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders
import re
from dotenv import load_dotenv

try:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dotenv_path = os.path.join(base_dir, '.env')
    
    load_dotenv(dotenv_path)
    
    sba_db_db = os.environ['sba_db_db']
    db_server = os.environ['db_server']
    db_driver = os.environ['db_driver_windows_auth']
    email_suffix = os.environ['email_suffix']
    from_address = os.environ['from_address']
    to_address = os.environ['to_address']
    password = os.environ['password']
    
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""Problem z wczytywaniem zmiennych środowiskowych - {str(e)}\n""")

now = subtracted_formatted_date = formatDateTime = subtracted_date = formatted_date = None
try:
    now = datetime.now()
    formatted_date = now.strftime("%Y-%m-%d")
    formatDateTime = now.strftime("%d/%m/%Y %H:%M")
    subtracted_date = now - timedelta(days=7)
    subtracted_formatted_date = subtracted_date.strftime("%Y-%m-%d")
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""Problem z wczytyaniem daty - {str(e)}\n""")

try:
    cnxn = pyodbc.connect(f"Driver={{ODBC Driver 17 for SQL Server}};Server={db_server};Database={sba_db_db};Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;")
    cursor = cnxn.cursor()

    cursor.execute("SELECT ST_NAZWA, AKTYWNE, CFG_DATA from dbo.STANOWISKA WHERE len(ST_NAZWA) = 4 ORDER BY 3 DESC ")
    hosts = cursor.fetchall()
    
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""Problem z wczytaniem danych z bazy danych - {str(e)}\n""")
    
try:  
    activeList = []
    inactiveList = []
    inactiveWithT = [] #salony nieaktywne z flaga T (aktywne) w db
    activeWithN = [] #salony aktywne z flaga N (niekatywne) w db
    for host in hosts:
        # Ignore ignored hosts from .env 
        if re.match(r"A5[.]*", host[0]):
            continue 
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
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""Problem z filtrowaniem hostów - {str(e)}\n""")

mail_hosts_list = [host.lower() + email_suffix for host in activeList]

try:
    msg = MIMEMultipart()
    msg['From'] = from_address
    msg["To"] = ", ".join(mail_hosts_list)
    msg['Subject'] = f"Przypomnienie o konieczności sprawdzenia stanu połączenia drukarki fiskalnej z urzędem skarbowym"
    
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f""" Problem z wysłaniem email - {str(e)}\n""")


fiscal_image = 'images/fiscal_status.png'

with open('fiscal_email_body.txt', 'r', encoding='utf-8') as file:
    html_body = file.read()

# Attach the HTML body to the email
msg.attach(MIMEText(html_body, 'html'))

with open(fiscal_image, 'rb') as img_file:
    img = MIMEImage(img_file.read())
    img.add_header('Content-ID', '<fiscal_status>')
    msg.attach(img)

try:
    server = smtplib.SMTP('smtp-mail.outlook.com', 587)
    server.starttls()
    server.login(from_address, password)
    text = msg.as_string()
    server.sendmail(from_address, mail_hosts_list, text)
    server.quit()    
    with open ('fiscal_succes.log', 'a') as file:
        file.write(f"""{formatDateTime} Wysłano maila do {len(mail_hosts_list)} salonów: {mail_hosts_list}\n\n""")
except Exception as e:
    with open ('logfile.log', 'a') as file:
        file.write(f"""{formatDateTime} Problem z wysłaniem maila - {str(e)}\n""")
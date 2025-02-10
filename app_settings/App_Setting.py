# Fetch User Login ID and Passcode from mongo database
from pymongo import MongoClient
#from db_setup import create_indexes
from flask import Flask

# Mongo Database (General)
client = MongoClient('mongodb://192.168.0.18:27017/')
db_FusionBizCentral = client['FusionBizCentral']
collection = db_FusionBizCentral['Selection_Process']
Interviewers_List = db_FusionBizCentral['Interviewers_List']
Log_table = db_FusionBizCentral['Logs_Records']
PC_profile = db_FusionBizCentral['PC Profile']
CollectionOfPersonalInfo=db_FusionBizCentral['User Profile - Personal Info']
CollectionOfOfficialInfo=db_FusionBizCentral['User Profile - Official Info']
CollectionOfBankDetails=db_FusionBizCentral['User Profile - Bank Details']
PreHRApproved=db_FusionBizCentral['Pre_HR_Approved']
ActiveEmployees=db_FusionBizCentral['Active_Employees']
PortalPermission=db_FusionBizCentral['PortalPermission']
MenuBarList=db_FusionBizCentral['MenuBarList']
PortalTitlesList=db_FusionBizCentral['PortalTitlesList']
BlockPCProfile=db_FusionBizCentral['Block_PC_Profile']
HtmlFilesList=db_FusionBizCentral['htmlFilesList']
PCProfileTable=db_FusionBizCentral['PC_Profile_Table']
FieldCollection= db_FusionBizCentral['Field Profile']
ClientGroupProfile = db_FusionBizCentral['Client Group Profile']
clientcollection = db_FusionBizCentral['Client Profile - Main']
clientdisplaycollection = db_FusionBizCentral['Client Display Profile']
departmentcollection = db_FusionBizCentral['Client Department Profile']
cameracollection = db_FusionBizCentral['Client Camera Profile']
clientDeptLink=db_FusionBizCentral['Client_Department_Link']
organizationProfile=db_FusionBizCentral['Organization_Profile']
orgnLocDept=db_FusionBizCentral['Organization_Location_Department']
reasonofcancellationcollection= db_FusionBizCentral['Reason For Cancellation']
incidentsentencescollection = db_FusionBizCentral['Incident Sentences Profile']
entitysentencescollection = db_FusionBizCentral['Entity Profile']
playbackcollection = db_FusionBizCentral['Playback Profile']
CRAuditorCollection = db_FusionBizCentral['Camera_Issue_Auditor']
CamIssueCollection = db_FusionBizCentral['camera_issue_details']
CIAuditorReporter = db_FusionBizCentral['Camera_Issue_Reporter']
db_Test = client['For_Test']
autosentencescollection = db_Test['AutoTextPopulations']
QuickReportViewCollection = db_FusionBizCentral['Report App']
Logs_popup = db_FusionBizCentral['report_app_logs']
collectionofdesignations = db_FusionBizCentral['designations_list'] 


#documents = collection.find({})
#users = {doc.get('dob_1') for doc in documents}

# Define the directory to fetch HTML files from and the JSON output path
#folder_path = "D:/Web Applications/iSurveillanz Web Application/templates"  # Folder containing the HTML files
#json_file_path = "D:/Web Applications/iSurveillanz Web Application/JSON files/Permission_table4.JSON"  # JSON file to save the data

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'amaratitkar@gmail.com'  
app.config['MAIL_PASSWORD'] = 'lwab mbsg oxjw oyyq'  
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

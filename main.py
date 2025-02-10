import sys
import os
from flask import Flask, request, redirect, url_for, render_template, flash, jsonify
from datetime import datetime
from jinja2 import FileSystemLoader
from jinja2 import Environment
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.', 'app_settings')))
from App_Setting import PCProfileTable,CamIssueCollection,CRAuditorCollection, CIAuditorReporter, clientDeptLink,playbackcollection 
from App_Setting import incidentsentencescollection, entitysentencescollection, clientcollection, reasonofcancellationcollection
from App_Setting import collection, app, organizationProfile, MongoClient, PC_profile,FieldCollection, ClientGroupProfile, clientcollection
from App_Setting import clientdisplaycollection, departmentcollection, cameracollection, CollectionOfOfficialInfo, MenuBarList, PortalPermission
from App_Setting import Log_table, CollectionOfPersonalInfo, CollectionOfBankDetails, BlockPCProfile, Logs_popup, collectionofdesignations
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.', 'User_Profile')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.', 'Block_PC_Profile')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.', 'Client_Profile')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.', 'Settings_Page')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.', 'Organization_Profile')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Initiated_Reports_View_Auditor_View')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Initiated_Reports_View_Reporter_View')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.', 'Report_Form')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.', 'Quick_Report_View')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Cancellation_Reason_Profile')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Incident_Sentences_Profile')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Playback')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Camera_Issue_Auditor_View')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Cancelled_Reports')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Rechecked_Reports')))
import methods.employee_profile.get_para_from_officialid as m
import methods.common_functions.common_function as hn
import methods.common_functions.loginid_menulist as lm
from User_Profile.register import app as register_bp
from User_Profile.portal import app as portal_bp
from Block_PC_Profile.pcprofile import app as BlockPC_bp
from Client_Profile.FieldProfile import app as Client_bp
from Organization_Profile.organizationProf import app as Organization_bp
from Report_Form.report_form import app as report_bp
import pandas as pd

# Initialize the Flask app
app = Flask(__name__)
app.register_blueprint(register_bp)
app.register_blueprint(portal_bp)
app.register_blueprint(BlockPC_bp)
app.register_blueprint(Client_bp)
app.register_blueprint(Organization_bp)
app.register_blueprint(report_bp)

app.secret_key = 'your_secret_key'
template_folders = [os.path.abspath("Report_Form/Initiated_Reports_View_Auditor_View"),
                    os.path.abspath("Report_Form/Initiated_Reports_View_Auditor_View/templates"),
                    os.path.abspath("Report_Form/Initiated_Reports_View_Reporter_View"),
                    os.path.abspath("Report_Form/Initiated_Reports_View_Reporter_View/templates"),
                    os.path.abspath("Report_Form/Cancelled_Reports"),
                    os.path.abspath("Report_Form/Cancelled_Reports/templates"),
                    os.path.abspath("Report_Form/Rechecked_Reports"),
                    os.path.abspath("Report_Form/Rechecked_Reports/templates"),
                    os.path.abspath("Quick_Report_View"),
                    os.path.abspath("Quick_Report_View/templates"),
                    os.path.abspath("Report_Form/Camera_Issue_Auditor_View"),
                    os.path.abspath("Report_Form/Camera_Issue_Auditor_View/templates"),
                    os.path.abspath("Report_Form/Playback"),
                    os.path.abspath("Report_Form/Playback/templates"),
                    os.path.abspath("Report_Form/Incident_Sentences_Profile"),
                    os.path.abspath("Report_Form/Incident_Sentences_Profile/templates"),
                    os.path.abspath("Report_Form/common templates"),
                    os.path.abspath("Report_Form/Cancellation_Reason_Profile/templates"),
                    os.path.abspath("Report_Form"),
                    os.path.abspath("Report_Form/Cancellation_Reason_Profile"),
                    os.path.abspath("Cancellation_Reason_Profile/templates"),
                    os.path.abspath("Settings_Page"),
                    os.path.abspath("Organization_Profile"),
                    os.path.abspath("Organization_Profile/templates"),
                    os.path.abspath("User_Profile"),
                    os.path.abspath("Client_Profile/templates"),
                    os.path.abspath("User_Profile/templates"), 
                    os.path.abspath("ctemplates"),
                    os.path.abspath("Block_PC_Profile/templates"), 
                    os.path.abspath("Block_PC_Profile"), 
                    os.path.abspath("Report_Form/Client_Rules_Linking"),
                    os.path.abspath("Report_Form/Client_Rules_Linking/templates"),
                    os.path.abspath("Client_Profile"),'format_datetime']
app.jinja_loader = FileSystemLoader(template_folders)
app.static_folder = os.path.abspath("static")

# Route for displaying the login page
'''@app.route('/')
def index():
    #username = session.get('username')
    # Get User Info
    loginid,portal_user_title = lm.get_user_info()
    check_login=hn.get_username()
    print(loginid)
    print(check_login)
    if check_login != loginid:
        loginid=""

    if not loginid or not portal_user_title:
        return redirect(url_for('log_in'))  # Redirect to login page if not logged in

    menu_items = lm.get_loginid_menulist()
   
    # Render the template with the visible menu items
    return render_template('menu_bar.html', username=loginid,menu_list=menu_items )

# Route for rendering login page
@app.route('/log_in.html')
def log_in():
    loginid,portal_user_title = lm.get_user_info()
    check_login=hn.get_username()
    print(loginid)
    print(check_login)
    if check_login != loginid:
        loginid=""
    return render_template('log_in.html',username=loginid)'''

# Route for handling login form submission
@app.route('/', methods=['GET','POST'])
def login():
    if request.method=='POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Find the user in MongoDB and check the password directly
        user = CollectionOfOfficialInfo.find_one({'User Login ID': username, 'Passcode': password})

        # Fetch PC Name and PC Title
        pc_profile = PC_profile.find_one({"Assigned User ID": username})
        pc_name = pc_profile['PC Name'] if pc_profile else 'Unknown'
        pc_profile_table = PCProfileTable.find_one({"pc_name": pc_name})
        pc_title = pc_profile_table['pc_title'] if pc_profile_table else 'No Title'

        if user:
            hn.update_host_name(username)
            menu_items = lm.get_loginid_menulist()
    
        # Render the template with the visible menu items
            return render_template('menu_bar.html', username=username,menu_list=menu_items )
            #return redirect(url_for('index'))  # Redirect to the dashboard (menu_bar.html) after successful login
        else:
            flash('Invalid username or password', 'error')
            #return redirect(url_for('log_in'))  # If login fails, redirect back to login page
    return render_template('log_in.html')
    
@app.route('/get_pc_data')
def get_pc_data():
    username = request.args.get('username')
    pc_profile = PC_profile.find_one({"username": username})
    pc_name = pc_profile['PC Name'] if pc_profile else 'Unknown'
    pc_profile_table = PCProfileTable.find_one({"pc_name": pc_name})
    pc_title = pc_profile_table['pc_title'] if pc_profile_table else 'No Title'

    return jsonify({"pcTitle": pc_title})

# Route for logging out the user
@app.route('/logout')
def logout():
    hn.update_host_name('')
    return render_template('log_in.html')

@app.route('/settings_page')
def settings():
    loginid,portal_user_title = lm.get_user_info()
    check_login=hn.get_username()
    if check_login != loginid:
        loginid=""

    menu_items = lm.get_loginid_menulist()
    return render_template('settings_page.html', username=loginid,menu_list=menu_items)  # Render your settings page

@app.route('/settings_permission')
def settings_permission():
    loginid,portal_user_title = lm.get_user_info()
    check_login=hn.get_username()
    if check_login != loginid:
        loginid=""

    menu_items = lm.get_loginid_menulist()
    return render_template('permission_page.html', username=loginid,menu_list=menu_items)  # Render your settings page

# Route for settings selection process (using menu visibility logic)
@app.route('/settings_SelectionProcess')
def settings_SelectionProcess():
    loginid,portal_user_title = lm.get_user_info()
    check_login=hn.get_username()
    if check_login != loginid:
        loginid=""

    if not loginid or not portal_user_title:
        return redirect(url_for('log_in'))  # Redirect to login page if not logged in

    menu_items = lm.get_loginid_menulist()

    # Render the settings page with the visible menu items
    return render_template('settings_SelectionProcess.html', username=loginid,menu_list=menu_items)

@app.route('/settings_BlockPCProfile')
def settings_BlockPCProfile():
    loginid,portal_user_title = lm.get_user_info()
    check_login=hn.get_username()
    if check_login != loginid:
        loginid=""

    if not loginid or not portal_user_title:
        return redirect(url_for('log_in'))  # Redirect to login page if not logged in

    menu_items = lm.get_loginid_menulist()

    # Render the settings page with the visible menu items
    return render_template('settings_BlockPCProfile.html', username=loginid,menu_list=menu_items)

@app.route('/html_file_entry_form')
def html_file_entry_form():
    loginid,portal_user_title = lm.get_user_info()
    check_login=hn.get_username()
    if check_login != loginid:
        loginid=""

    if not loginid or not portal_user_title:
        return redirect(url_for('log_in'))  # Redirect to login page if not logged in

    menu_items = lm.get_loginid_menulist()

    # Render the settings page with the visible menu items
    return render_template('html_file_entry_form.html', username=loginid,menu_list=menu_items)

@app.route('/settings_ClientProfile')
def settings_ClientProfile():
    loginid,portal_user_title = lm.get_user_info()
    check_login=hn.get_username()
    if check_login != loginid:
        loginid=""

    if not loginid or not portal_user_title:
        return redirect(url_for('log_in'))  # Redirect to login page if not logged in

    menu_items = lm.get_loginid_menulist()

    # Render the settings page with the visible menu items
    return render_template('settings_ClientProfile.html', username=loginid,menu_list=menu_items)

@app.route('/settings_OrganizationProfile')
def settings_OrganizationProfile():
    loginid,portal_user_title = lm.get_user_info()
    check_login=hn.get_username()
    if check_login != loginid:
        loginid=""

    if not loginid or not portal_user_title:
        return redirect(url_for('log_in'))  # Redirect to login page if not logged in

    menu_items = lm.get_loginid_menulist()

    # Render the settings page with the visible menu items
    return render_template('settings_OrganizationProfile.html', username=loginid,menu_list=menu_items)

@app.route('/show_logs', methods=['GET', 'POST'])
def show_logs():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()

    # Ensure the login id is valid
    if check_login != loginid:
        loginid = ""
    
    # Fetch all records from the MongoDB collection
    logs_cursor = Log_table.find()

    # Convert the MongoDB data into a list of dictionaries (documents)
    logs_records_list = list(logs_cursor)

    # Create a DataFrame from the MongoDB data
    logs_records_df = pd.DataFrame(logs_records_list)

    # Print the actual column names to debug
    print(logs_records_df.columns)

    # Check if 'user_name' or 'User Name' is the correct column
    # Rename the columns to match the table headers, adjusting the column names based on inspection
    logs_records_df = logs_records_df[['category', 'action', 'action_title', 'user_name', 'date_time', 'collection_name', 'html_file_source']]
    logs_records_df.columns = ['Category', 'Action', 'Action Title', 'User Name', 'Date - time', 'Collection Name', 'HTML File Source']

    # Get filter values from the form, default to None if not set
    category_filter = request.args.get('category')
    collection_filter = request.args.get('collection')  
    user_filter = request.args.get('username')

    # Filter the DataFrame based on selected filters
    if category_filter:
        logs_records_df = logs_records_df[logs_records_df['Category'] == category_filter]
    
    if collection_filter:
        logs_records_df = logs_records_df[logs_records_df['Collection Name'] == collection_filter]
    
    if user_filter:
        logs_records_df = logs_records_df[logs_records_df['User Name'] == user_filter]

    # Convert the DataFrame to HTML format for rendering in the template
    logs_html = logs_records_df.to_html(classes='table table-bordered', index=False)

    # Get unique values for filters from the MongoDB data (categories, actions, users)
    categories = logs_records_df['Category'].unique()

    # Dynamically filter actions and users based on selected category
        
    collections = list()  # Set to ensure unique collection names
    print(logs_records_df['Collection Name'])
    for collection_name in logs_records_df['Collection Name']:
        # Extract collection name after the dot (e.g., FusionBizCentral.PortalTitlesList -> PortalTitlesList)
        collection_base = collection_name.split('.')[1] if '.' in collection_name else collection_name
        collections.insert(0,collection_base)
    
    collections = sorted(collections)

    if category_filter:
        collections = logs_records_df[logs_records_df['Collection Name'] == category_filter]['Collection Name'].unique()
        users = logs_records_df[logs_records_df['Category'] == category_filter]['User Name'].unique()
    else:
        collections = logs_records_df['Collection Name'].unique()
        users = logs_records_df['User Name'].unique()

    menu_items = lm.get_loginid_menulist()

    # Pass the HTML table and filter options to the template
    return render_template(
        'logs_records.html', 
        table=logs_html, 
        categories=categories, 
        collections=collections,
        users=users, 
        username=loginid,
        menu_list=menu_items
    )

@app.route('/settings_reportform')
def settings_reportform():
    loginid,portal_user_title = lm.get_user_info()
    check_login=hn.get_username()
    if check_login != loginid:
        loginid=""

    menu_items = lm.get_loginid_menulist()
    return render_template('settings_reportform.html', username=loginid,menu_list=menu_items)  # Render your settings page

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
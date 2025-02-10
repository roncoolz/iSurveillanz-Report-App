import sys
import os
from flask import Flask, request, redirect, url_for, render_template, flash, jsonify, session, Blueprint
from flask_mail import Mail, Message
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app_settings')))
from App_Setting import collection, app, MongoClient, CollectionOfOfficialInfo,Log_table, PC_profile, BlockPCProfile, db_FusionBizCentral, PCProfileTable, clientcollection, departmentcollection, clientDeptLink
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Block_PC_Profile')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.', 'User_Profile')))
import methods.employee_profile.get_para_from_officialid as m
import methods.common_functions.loginid_menulist as lm
import socket
import methods.common_functions.common_function as hn
import random
import string
from jinja2 import FileSystemLoader
from jinja2 import Environment
from flask_pymongo import PyMongo
from bson.objectid import ObjectId

# Initialize the Flask app
app = Blueprint('block_PC', __name__)

# Function to generate Block ID
def generate_block_id():
    block_id = ''.join(random.choices(string.ascii_uppercase, k=3)) + str(random.randint(0, 9))
    return block_id

# List to store block profile entries
block_profiles = []

@app.route('/block_Profile', methods=['GET', 'POST'])
def block_Profile():
    block_id = generate_block_id()  # Generate Block ID
    block_location = None
    block_name = None
    organization = None
    location = None
    department = None

    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""

    if request.method == 'POST':
        block_id = generate_block_id()  # Generate Block ID on form submission
        block_name = request.form['block_name']
        organization = request.form['organization']
        location = request.form['location']
        department = request.form['department']

        if not organization and not location and not department:
            flash('Please select Organization, Location, and Department before submitting the form.', 'error')
            return redirect(url_for('block_Profile'))

        block_location = f"{organization}/{location}/{department}"

        data = {
            "block_id": block_id,
            "block_name": request.form.get("block_name"),
            "organization": organization,
            "location": location,
            "department": department,
            "block_location": block_location
        }        
        BlockPCProfile.insert_one(data)

        # Log entry for the addition of new profile
        log_entry_new_block_profile = {
            "action_title": "Form Submission",
            "action": f"New Block Added - {block_name}",
            "user_name": m.getfullname(hn.get_username()),
            "date_time": datetime.now(),
            "collection_name": BlockPCProfile.full_name,
            "html_file_source": "block_table.html",
            "category":"Block & PC Profile"
        }

        # Insert log into MongoDB collection
        Log_table.insert_one(log_entry_new_block_profile) 

        return redirect(url_for('block_PC.view_profiles'))

    menu_items = lm.get_loginid_menulist()
    return render_template('block_Profile.html', block_id=block_id, block_location=block_location,
                           block_name=block_name, organization=organization, location=location, 
                           department=department,username=loginid, menu_list=menu_items)

@app.route('/profiles')
def view_profiles():
    block_profiles = list(BlockPCProfile.find())
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""

    menu_items = lm.get_loginid_menulist()
    return render_template('block_table.html', block_profiles=block_profiles,username=loginid, menu_list=menu_items)

@app.route('/new_pc', methods=['GET', 'POST'])
def new_pc():
    pc_name = None
    machine_id = None
    status = None
    pc_title = None
    block_name = None

    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""

    menu_items = lm.get_loginid_menulist()

    # Fetch all block names from the database
    block_profiles = BlockPCProfile.find({}, {'block_name': 1, '_id': 0})
    block_names = [profile['block_name'] for profile in block_profiles]

    if request.method == 'POST':
        pc_name = request.form['pc_name']
        machine_id = request.form['machine_id']
        status = request.form['status']
        pc_title = request.form['pc_title']
        block_name = request.form['block_name']

        # Validate that all fields are filled
        if not pc_name or not machine_id or not status or not pc_title or not block_name:
            flash('All fields are required.', 'error')
            return redirect(url_for('block_PC.new_pc'))

        data_newPC = {
            "pc_name": pc_name,
            "machine_id": machine_id,
            "status": status,
            "pc_title": pc_title,
            "block_name": block_name,
            "created_at": datetime.now()  # Track the creation time of the record
        }

        # Insert data into MongoDB collection (e.g., 'pc_profiles')
        PCProfileTable.insert_one(data_newPC)  # Adjust to correct collection

        entry_pc_profile = {
            "PC Name": pc_name,
            "Assigned User ID": "None"
        }

        PC_profile.insert_one(entry_pc_profile)

        # Log entry for the addition of new profile
        log_entry_new_pc_profile = {
            "action_title": "Form Submission",
            "action": f"New PC Added - {pc_title}",
            "user_name": m.getfullname(hn.get_username()),
            "date_time": datetime.now(),
            "collection_name": PCProfileTable.full_name,
            "html_file_source": "pc_profile.html",
            "category":"Block & PC Profile"
        }

        # Insert log into MongoDB collection
        Log_table.insert_one(log_entry_new_pc_profile) 

        flash('PC Profile successfully added!', 'success')
        return redirect(url_for('block_PC.view_pc_profiles'))

    return render_template('new_pc_profile.html', 
                           pc_name=pc_name, machine_id=machine_id, status=status, 
                           pc_title=pc_title,block_names=block_names, username=loginid, menu_list=menu_items)

@app.route('/view_pc_profiles')
def view_pc_profiles():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""

    # Fetch all PC profiles from MongoDB collection 'PC_Profile_Table'
    pc_profiles = list(PCProfileTable.find())
    menu_items = lm.get_loginid_menulist()

    return render_template('pc_profile.html', pc_profiles=pc_profiles,username=loginid, menu_list=menu_items)

# Route to fetch distinct Client Registration Names (Client Names)
@app.route('/get_clients')
def get_clients():
    clients = clientcollection.distinct('Client Name')  # Fetch distinct client names
    return jsonify(clients)

# Route to fetch Client IDs based on Client Registration Name
@app.route('/get_client_ids/<client_name>')
def get_client_ids(client_name):
    client_ids = departmentcollection.find({'Client Name': client_name}, {'Client ID': 1, '_id': 0})
    client_ids_list = [client['Client ID'] for client in client_ids]
    return jsonify({'client_ids': client_ids_list})

# Route to fetch Departments based on Client ID
@app.route('/get_departments/<client_id>')
def get_departments(client_id):
    departments = departmentcollection.find({'Client ID': client_id}, {'Department Name/Port Number': 1, '_id': 0})
    department_names = [dept['Department Name/Port Number'] for dept in departments]
    return jsonify({'departments': department_names})

# Route to fetch Department ID based on Department Name
@app.route('/get_department_id/<department_name>')
def get_department_id(department_name):
    department = departmentcollection.find_one({'Department Name/Port Number': department_name}, {'Department ID': 1, '_id': 0})
    department_id = department['Department ID'] if department else None
    return jsonify({'department_id': department_id})

@app.route('/check_department_exists/<department_id>')
def check_department_exists(department_id):
    # Search for the department_id in the 'Client_Department_Link' collection
    existing_link = clientDeptLink.find_one({"department_id": department_id})
    
    # Return a JSON response indicating if the department_id exists or not
    return jsonify({"exists": bool(existing_link)})

@app.route('/link_to_department', methods=['POST'])
def link_to_department():
    # Capture form data from the modal
    pc_title = request.form['pc_title']
    client_registration_number = request.form['client']
    client_id = request.form['client_id']
    department = request.form['department']
    department_id = request.form['department_id']

    # Check if the department_id already exists in the MongoDB collection 'Client_Department_Link'
    existing_link = clientDeptLink.find_one({"department_id": department_id})
    
    if existing_link:
        # If department_id exists, flash a message and prevent insertion
        flash('This department is already linked with a PC Profile. No changes made.', 'error')
        return redirect(url_for('block_PC.view_pc_profiles'))

    # If department_id does not exist, proceed to insert the new data
    clientDeptLink.insert_one({
        "pc_title": pc_title,
        "client_registration_number": client_registration_number,
        "client_id": client_id,
        "department": department,
        "department_id": department_id
    })

    # Log entry for the addition of new profile
    log_entry_linking_to_department = {
        "action_title": "Form Submission",
        "action": f"New Department is Linked to {pc_title}. Department ID is: {department_id}",
        "user_name": m.getfullname(hn.get_username()),
        "date_time": datetime.now(),
        "collection_name": clientDeptLink.full_name,
        "html_file_source": "link_to_department.html",
        "category":"Block & PC Profile"
    }

    # Insert log into MongoDB collection
    Log_table.insert_one(log_entry_linking_to_department) 

    flash('PC Profile successfully linked to Department!', 'success')
    return redirect(url_for('block_PC.view_pc_profiles'))  # Redirect back to the PC Profiles page

@app.route('/view_all_links', methods=['GET', 'POST'])
def view_all_links():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""

    menu_items = lm.get_loginid_menulist()
    # Fetch all PC Titles from the database
    pc_titles = [profile['pc_title'] for profile in PCProfileTable.find()]
    
    # Get PC Title from query string or set it to None if not provided
    pc_title = request.args.get('pc_title', None)
    
    links = []
    
    if request.method == 'POST':
        # Fetch the PC Title entered in the form
        pc_title = request.form['pc_title']
        
        # Fetch the linked departments for the provided PC Title
        links = list(clientDeptLink.find({"pc_title": pc_title}))
        
    # Render the template with the pc_titles and the links (if any)
    return render_template('view_all_links.html', pc_titles=pc_titles, links=links, pc_title=pc_title,username=loginid, menu_list=menu_items)

@app.route('/remove_link', methods=['POST'])
def remove_link():
    # Retrieve the link ID from the form
    link_id = request.form['link_id']

    # Attempt to delete the link from the MongoDB collection
    result = clientDeptLink.delete_one({"_id": ObjectId(link_id)})

    # Log entry for the addition of new profile
    log_entry_remove_linked_departments = {
        "action_title": "Form Submission",
        "action": f"Department removal done for PC Link ID: {link_id} ",
        "user_name": m.getfullname(hn.get_username()),
        "date_time": datetime.now(),
        "collection_name": clientDeptLink.full_name,
        "html_file_source": "link_to_department.html",
        "category":"Block & PC Profile"
    }

    # Insert log into MongoDB collection
    Log_table.insert_one(log_entry_remove_linked_departments) 
    
    # Check if the deletion was successful
    if result.deleted_count > 0:
        flash('Link successfully removed!', 'success')
    else:
        flash('Failed to remove the link. Please try again.', 'error')
    
    # Redirect back to the view_all_links page
    return redirect(url_for('block_PC.view_all_links'))

@app.route('/pc_assigned_users_list')
def pc_assigned_users_list():
    # Get the current user's info and check login
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""

    # Get the menu items
    menu_items = lm.get_loginid_menulist()

    # Query to get all records from 'PC Profile' collection
    pc_data = PCProfileTable.find({})

    # List to hold the final combined data
    pc_assigned_users = []

    # Iterate over each PC Profile entry
    for pc in pc_data:
        pcname=pc['pc_name']
        pctitle=pc['pc_title']
        assigneduserid=PC_profile.find_one({'PC Name':pcname}).get('Assigned User ID')

        # Query the 'User Profile - Official Info' collection for the employee's name
        user_info = CollectionOfOfficialInfo.find_one(
            {'Official ID': assigneduserid},  # Matching Assigned User ID with Official ID
        )

        # If user info is found, merge the data
        if user_info and assigneduserid:
            full_name = f"{user_info['First Name']} {user_info['Middle Name']} {user_info['Last Name']}"
            pc_assigned_users.append({
                'PC Name': pcname,
                'PC Title':pctitle,
                'Assigned User ID': assigneduserid,
                'Employee Name': full_name
            })
        else:
            # If no matching user found, just show the PC Name and Assigned User ID
            pc_assigned_users.append({
                'PC Name': pcname,
                'PC Title':pctitle,
                'Assigned User ID': assigneduserid,
                'Employee Name': '-'  # Or leave it empty if preferred
            })

    # Pass the data to the template
    return render_template('pc_assigned_users_list.html', users=pc_assigned_users, username=loginid, menu_list=menu_items)

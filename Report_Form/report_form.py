from flask import Flask, render_template, request, redirect, url_for, flash, Blueprint, jsonify, session, current_app, send_from_directory
from datetime import datetime
from bson.objectid import ObjectId
import sys
import os
import json
from werkzeug.utils import secure_filename
import methods.employee_profile.get_para_from_officialid as m
import methods.common_functions.loginid_menulist as lm
import methods.common_functions.common_function as hn
from flask_cors import CORS
from transformers import pipeline
import re
from App_Setting import app,Log_table,QuickReportViewCollection,autosentencescollection,CIAuditorReporter, cameracollection, CamIssueCollection
from App_Setting import CRAuditorCollection, clientDeptLink, PCProfileTable, reasonofcancellationcollection, incidentsentencescollection, entitysentencescollection
from App_Setting import clientcollection, playbackcollection, cameracollection, PC_profile, departmentcollection, Logs_popup, incidentcategoriesdetails

# Initialize the Flask app
app = Blueprint('report', __name__)
CORS(app)

# Initialize the transformer model for grammar correction
grammar_corrector = pipeline("text2text-generation", model="t5-base", device=0)  # Use device=0 for GPU if available

# Define a shared directory for file storage, assuming this is a shared folder path accessible across desktops
UPLOAD_FOLDER = "Z:/Client_Profile_Rules"  # Example shared network folder
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'docx'}

@app.route('/add_cancellation_reason', methods=['POST'])
def add_cancellation_reason():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""
    menu_items = lm.get_loginid_menulist()
    try:
        # Retrieve form data
        reason_title = request.form.get('reason_title_text')
        reason_dropdown = request.form.get('reason_title_dropdown')
        parameter = request.form.get('parameter')

        # Combine reason_title and reason_dropdown
        combined_reason = reason_title if reason_title else reason_dropdown

        # Check if the combination of 'Cancellation Title' and 'Parameter' already exists
        if reasonofcancellationcollection.find_one({"Cancellation Title": combined_reason, "Reason Parameter": parameter}):
            flash(f"Error: The Cancellation Title '{combined_reason}' and Parameter '{parameter}' already exists!", "error")
            return redirect(url_for('report.table_cancellation_reasons'))

        # Insert the new cancellation reason into the database
        reasonofcancellationcollection.insert_one({
            "Cancellation Title": combined_reason,
            "Status": "Cancel",
            "Reason Parameter": parameter,
            "Created On": datetime.now()
        })

        # Log the action
        log_entry_new_cancellation_reason = {
            "action_title": "Form Submission",
            "category": "Report Form",
            "user_name": m.getfullname(hn.get_username()),
            "action": f"Cancellation reason ({reason_title} with parameter ({parameter}))",
            "date_time": datetime.now(),
            "collection_name": reasonofcancellationcollection.full_name,
            "html_file_source": "reason_cancellation.html"}

        Log_table.insert_one(log_entry_new_cancellation_reason)
   
        flash("Cancellation reason added successfully!", "success")
        return redirect(url_for('report.table_cancellation_reasons'))
    except Exception as e:
        flash(f"Error adding cancellation reason: {str(e)}", "error")
        return redirect(url_for('report.table_cancellation_reasons'), username=loginid, menu_list=menu_items)
    
@app.route('/table_cancellation_reasons')
def table_cancellation_reasons():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""
    menu_items = lm.get_loginid_menulist()
        
    cancellation_reasons = list(reasonofcancellationcollection.find().sort('Cancellation Title', -1))
    unique_reasons = reasonofcancellationcollection.distinct("Cancellation Title")
    return render_template('reason_cancellation.html', cancellation_reasons=cancellation_reasons, unique_reasons=unique_reasons, username=loginid, menu_list=menu_items)

@app.route('/form_incident_profile', methods=['GET', 'POST'])
def form_incident_profile():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""
    menu_items = lm.get_loginid_menulist()
    if request.method == 'POST':
        # Collect form data
        subject = request.form.get('subject')
        #client_name = request.form.get('client_name')
        #client_id = request.form.get('client_id')
        incident_sentence = request.form.get('incident_sentence')
        keywords = request.form.get('keywords')  # Optional field
        incident_category = request.form.get('incident_category')
        incident_category_other = request.form.get('incident_category_other')

        # Validation checks
        if not all([subject, incident_sentence, incident_category]):
            flash('All required fields must be filled out.', 'error')
            return redirect(url_for('form_incident_profile'))

        # Handle 'Other' category
        if incident_category == 'other' and not incident_category_other:
            flash('Please specify the "Other" incident category.', 'error')
            return redirect(url_for('form_incident_profile'))

        # Prepare data for MongoDB
        incident_data = {
            'Subject': subject,
            'Incident Sentence': incident_sentence,
            'Keywords': keywords,
            'status': 'Not Selected',
            'Incident Category': incident_category_other if incident_category == 'other' else incident_category,
        }

        # Log the action
        log_entry_new_incident_profile = {
            "action_title": "Form Submission",
            "category": "Report Form",
            "user_name": m.getfullname(hn.get_username()),
            "action": f"New incident Profile statement ({incident_sentence})",
            "date_time": datetime.now(),
            "collection_name": incidentsentencescollection.full_name,
            "html_file_source": "form_incident_sentences_profile.html"}

        Log_table.insert_one(log_entry_new_incident_profile)

        try:
            # Insert data into MongoDB
            incidentsentencescollection.insert_one(incident_data)
            flash('Incident Profile created successfully!', 'success')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')

        return redirect(url_for('report.form_report'))  # Redirect to form_report after submission

    # Fetch client names from the 'Client Profile - Main' collection
    clients = clientcollection.find()
    client_data = {client['Client Name']: client['Client ID'] for client in clients}

    # Render form for GET request and pass client names to the template
    return render_template('form_incident_sentences_profile.html', client_data=client_data, username=loginid, menu_list=menu_items)

@app.route('/table_incident_profile')
def table_incident_profile():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""
    menu_items = lm.get_loginid_menulist()

    incident_sentences = list(incidentsentencescollection.find({}, {"_id": 0, "Client Name": 1, "Client ID": 1, "Incident Category": 1, "Incident Sentence": 1}))   
    
    for index, incident in enumerate(incident_sentences, start=1):
        incident["Sr.No"] = index
    
    return render_template('table_incident_profile.html', incident_sentences=incident_sentences, username=loginid, menu_list=menu_items)


@app.route('/form_entity_profile', methods=['GET', 'POST'])
def form_entity_profile():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""
    menu_items = lm.get_loginid_menulist()
    if request.method == 'POST':
        entity_type = request.form.get('entity_type')
        entity_type_other = request.form.get('entity_type_other')
        entity_title = request.form.get('entity_title')

        if not entity_type or not entity_title:
            flash('Both Type and Title fields are required.', 'error')
            return redirect(url_for('form_entity_profile'))

        if entity_type == 'other' and not entity_type_other:
            flash('Please specify the "Other" type.', 'error')
            return redirect(url_for('form_entity_profile'))

        entity_data = {
            'Entity Type': entity_type_other if entity_type == 'other' else entity_type,
            'Entity Title': entity_title,
        }

        # Log the action
        log_entry_new_entity_profile = {
            "action_title": "Form Submission",
            "category": "Report Form",
            "user_name": m.getfullname(hn.get_username()),
            "action": f"New entity ({entity_title}) created for type ({entity_type})",
            "date_time": datetime.now(),
            "collection_name": entitysentencescollection.full_name,
            "html_file_source": "form_entity_profile.html"}

        Log_table.insert_one(log_entry_new_entity_profile)

        try:
            entitysentencescollection.insert_one(entity_data)
            flash('Entity Profile created successfully!', 'success')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')

        return redirect(url_for('table_entity_profile'))

    return render_template('form_entity_profile.html', username=loginid, menu_list=menu_items)

@app.route('/table_entity_profile')
def table_entity_profile():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""
    menu_items = lm.get_loginid_menulist()
    entity_profiles = list(entitysentencescollection.find().sort('Entity Type',-1))
    return render_template('table_entity_profile.html', entity_profiles=entity_profiles, username=loginid, menu_list=menu_items)

@app.route('/form_report', methods=['GET', 'POST'])
def form_report():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""
    menu_items = lm.get_loginid_menulist()
    #incident_message = None
    final_report_statement= None
    entity_titles = []

    if request.method == 'POST':
        # Retrieve the updated incident message
        #incident_message = request.form.get('incident_message')
        final_report_statement = request.form.get('report_statement')

        if not final_report_statement:
            flash('Final Report Statement is required.', 'error')
        else:
            # Save the updated message to the database if needed
            flash('Form Report submitted successfully!', 'success')
            return redirect(url_for('form_report')) 

    # Fetch the latest incident message from the database
    latest_incident = incidentsentencescollection.find().sort('_id', -1).limit(1)
    if latest_incident:
        final_report_statement = latest_incident[0].get('report_statement', '')

    # Fetch the list of entity titles
    entity_data = entitysentencescollection.find({'Entity Type': 'Human-Entiy-P'})  
    for entity in entity_data:
        entity_titles.append(entity['Entity Title'])

    return render_template('form_report.html', final_report_statement=final_report_statement, entity_titles=entity_titles, username=loginid, menu_list=menu_items)

@app.route('/add_playback', methods=['GET', 'POST'])
def add_playback():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""
    menu_items = lm.get_loginid_menulist()
    if request.method == 'POST':
        client_name = request.form['client_name']
        department_name = request.form['department_name']
        camera_number = request.form.getlist('camera_number')
        priority = request.form['priority']
        pc_name = request.form['pc_name']

        # Get the highest current serial number in the database
        highest_serial = playbackcollection.find_one(
            {}, sort=[("Serial Number", -1)]
        )
        # If there's no existing playback, start from 1, otherwise, increment the highest serial number
        serial_number = 1 if highest_serial is None else highest_serial["Serial Number"] + 1

        playback_data = {
            'Serial Number': serial_number,
            'Client Name': client_name,
            'Department Name': department_name,
            'Camera Number': camera_number,
            'Priority': priority,
            'PC Name': pc_name,
        }

        playbackcollection.insert_one(playback_data)
        flash('Playback added successfully!', 'success')
        return redirect(url_for('view_playback'))

    client_names = cameracollection.distinct("Client Name")
    return render_template('playback.html', client_names=client_names, username=loginid, menu_list=menu_items)

@app.route('/get_departments/<client_name>', methods=['GET'])
def get_departments(client_name):
    departments = cameracollection.distinct("Department Name", {"Client Name": client_name})
    return jsonify(departments)

@app.route('/get_cameras/<client_name>/<department_name>', methods=['GET'])
def get_cameras(client_name, department_name):
    cameras = cameracollection.find({"Client Name": client_name, "Department Name": department_name}, {"Camera Number": 1, "_id": 0})
    camera_list = [camera["Camera Number"] for camera in cameras]
    return jsonify(camera_list)

@app.route('/view_playback', methods=['GET'])
def view_playback():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""
    menu_items = lm.get_loginid_menulist()
    # Fetch playback records sorted by Serial Number
    playbacks = list(playbackcollection.find().sort("Serial Number", 1))
    pc_names = playbackcollection.distinct("PC Name")
    return render_template('table_playback.html', playbacks=playbacks, pc_names=pc_names, username=loginid, menu_list=menu_items)

'''@app.route('/debug_playback', methods=['GET'])
def debug_playback():
    data = list(playbackcollection.find().sort("Serial Number", 1))
    return jsonify(data)'''

@app.route('/update_playback_sequence', methods=['POST'])
def update_playback_sequence():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""
    menu_items = lm.get_loginid_menulist()
    updated_order = request.json.get('order')

    for new_serial, playback_id in enumerate(updated_order, start=1):
        playbackcollection.update_one(
            {"_id": ObjectId(playback_id)},  
            {"$set": {"Serial Number": new_serial}}
        )

    return jsonify({"status": "success", "message": "Sequence updated successfully"})

@app.route('/get_departments_by_client', methods=['GET'])
def get_departments_by_client():
    client_registration_number = request.args.get('client_registration_number')
    client_name = request.args.get('client_name')
    
    if client_registration_number:
        # Fetch distinct departments for the client using client_registration_number
        departments = clientDeptLink.distinct("department", {"client_registration_number": client_registration_number})

        if departments:
            return jsonify({"departments": departments})
        else:
            return jsonify({"error": "Departments not found for the client"}), 404
    
    elif client_name:
        # Fetch departments associated with the client using client_name from PCClientLinkCollection
        try:
            departments = list(clientDeptLink.find(
                {'client_registration_number': client_name},
                {'department': 1, '_id': 0}
            ))

            # Extract unique departments to avoid duplicates
            unique_departments = list(set([entry['department'] for entry in departments]))

            return jsonify({"success": True, "departments": unique_departments})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)})
    
    else:
        return jsonify({"error": "Either 'client_registration_number' or 'client_name' must be provided"}), 400

@app.route('/get_cameras_by_client_and_department', methods=['GET'])
def get_cameras_by_client_and_department():
    client_name = request.args.get('client_name')
    department_name = request.args.get('department_name')

    if not client_name or not department_name:
        return jsonify({"success": False, "message": "Client or Department not provided."})

    # Fetch Department ID based on Client Name and Department Name
    department = clientDeptLink.find_one({"client_registration_number": client_name, "department": department_name})

    if not department:
        return jsonify({"success": False, "message": "Department not found."})

    department_ID = department["department_id"]
    print(department_ID)

    # Fetch cameras for the given department
    cameras = list(cameracollection.find({'Department ID': department_ID}))
    print(cameras)

    # Convert Camera Number to integer (if float) and then to string before concatenation
    camera_numbers = [str(int(camera['Camera Number'])) + ':' + str(camera["Camera Name"]) for camera in cameras]
    print(camera_numbers)

    return jsonify({"success": True, "cameras": camera_numbers})
 
@app.route('/get_client_data', methods=['GET'])
def get_client_data():
    client_registration_number = request.args.get('client_registration_number')
    print(f"Fetching data for client: {client_registration_number}")

    # Fetch client data from Client_Department_Link collection
    client_data = clientDeptLink.find_one({"client_registration_number": client_registration_number})
    print(f"Client data is: {client_data}")

    if client_data:
        client_id = str(client_data.get("_id"))  # Convert MongoDB ObjectId to string
        departments = clientDeptLink.distinct("department", {"client_registration_number": client_registration_number})

        print(f"departments are:{departments}")

        # Fetch camera data for the client
        cameras = cameracollection.find({"Client Name": client_registration_number})
        print(f"cameras are:{cameras}")
        camera_options = []
        for camera in cameras:
            camera_number = camera.get("Camera Number")
            camera_name = camera.get("Camera Name")
            camera_options.append(f"{camera_number} : {camera_name}")

        # Return combined data in JSON format
        return jsonify({
            "client_id": client_id,
            "departments": departments,
            "cameras": camera_options  # List of cameras for multi-select in frontend
        })
    else:
        return jsonify({"error": "Client not found"}), 404
    
@app.route('/get_cameras_by_department', methods=['GET'])
def get_cameras_by_department():
    client_registration_number = request.args.get('client_registration_number')
    selected_department = request.args.get('department')

    if not client_registration_number or not selected_department:
        return jsonify({"error": "Missing client or department"}), 400

    # Fetch cameras for the given client and department
    cameras = cameracollection.find({
        "Client Name": client_registration_number,
        "Department Name/Port Number": selected_department  # Ensure filtering by department
    })

    camera_options = [
        f"{camera.get('Camera Number')} : {camera.get('Camera Name')}"
        for camera in cameras if "Camera Number" in camera and "Camera Name" in camera
    ]

    return jsonify({"cameras": camera_options})

@app.route('/get_report_statements', methods=['GET'])
def get_report_statements():
    client_name = request.args.get('client_name')

    if not client_name:
        return jsonify({"error": "Client name is required"}), 400

    try:
        # Fetch records with matching criteria
        query = {"Subject": "Camera Issue", "Client Name": client_name}
        records = incidentsentencescollection.find(query, {"_id": 0, "Incident Sentence": 1})

        # Extract Incident Sentences
        sentences = [record["Incident Sentence"] for record in records]

        return jsonify(sentences)
    except Exception as e:
        print(f"Error fetching report statements: {e}")
        return jsonify({"error": "An error occurred while fetching report statements"}), 500
    
@app.route('/get_entity_titles', methods=['GET'])
@app.route('/get_entity_titles/<entity_type>', methods=['GET'])
def get_entity_titles(entity_type=None):
    if entity_type:
        # Fetch the entity titles based on the provided entity_type
        if entity_type not in ['P', 'S']:
            return jsonify({"error": "Invalid entity type"}), 400
        
        # Fetch corresponding entity titles from MongoDB based on entity type
        entity_data = entitysentencescollection.find({'Entity Type': f'Human-Entity-{entity_type}'})
        entity_titles = [entity.get('Entity Title') for entity in entity_data]
        
        return jsonify({"entity_titles": entity_titles})
    else:
        # Get distinct 'Entity Title' where 'Entity Type' is 'Human-Entity-P'
        distinct_titles = entitysentencescollection.distinct("Entity Title", {"Entity Type": "Human-Entity-P"})
        return jsonify(distinct_titles)

@app.route('/table_camera_issue_auditor1', methods=['GET'])
def table_camera_issue_auditor1():
    # Existing user info and login check
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""
    menu_items = lm.get_loginid_menulist()

    # Existing PC Profile and Clients List logic
    clients_list = []
    pc_title = None
    if loginid:
        pc_profile = PC_profile.find_one({"Assigned User ID": loginid})
        if pc_profile and 'PC Name' in pc_profile:
            pc_name = pc_profile['PC Name']
            pc_profile_table = PCProfileTable.find_one({"pc_name": pc_name})
            if pc_profile_table and 'pc_title' in pc_profile_table:
                pc_title = pc_profile_table['pc_title']
                distinct_clients = clientDeptLink.distinct("client_registration_number", {"pc_title": pc_title})

                clients_list = [
                    {"registration_number": client, "_id": "", "name": client}
                    for client in distinct_clients if client  # Ensure no None values
                ]

    # Fetch data from MongoDB, but only include records with the matching pc_title
    data = list(QuickReportViewCollection.find({
    "PC title": pc_title,  # Filter by pc_title
    "CR Status": { "$ne": "Cleared", "$ne": "Ignored" },
    "Status": { "$ne": "Initiated" }  # CR Status should not be "Cleared"
}))
    today_date = datetime.today().date()  # Get today's date

    # Add a flag to determine if the remind button should be disabled


    # Log data to ensure it is being populated correctly (you can remove this later)
    print(data)

    # Existing categories fetch
    categories = CamIssueCollection.distinct('camera_issue_category')

    return render_template('camera_issue_auditor_view1.html',
        data=data,
        pc_title=pc_title,
        username=loginid,
        menu_list=menu_items,
        clients_list=clients_list,
        categories=categories)

# Route to display the form and handle form submission
@app.route('/camera_issue_form', methods=['GET', 'POST'])
def camera_issue_form():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""
    menu_items = lm.get_loginid_menulist()
    # Fetch existing camera issue categories from MongoDB (distinct categories)
    existing_categories = CamIssueCollection.distinct('camera_issue_category')

    if request.method == 'POST':
        # Retrieve data from the form
        camera_issue_category = request.form.get('cameraIssueCategory')
        camera_issue_statement = request.form.get('cameraIssueStatement')

        # If the user chose "Other", they must have entered a custom category
        if camera_issue_category == 'Other':
            camera_issue_category = request.form.get('customCategory')

        # Insert the data into MongoDB
        issue_data = {
            'camera_issue_category': camera_issue_category,
            'camera_issue_statement': camera_issue_statement
        }

        # Insert the document into the collection
        CamIssueCollection.insert_one(issue_data)

        # After form submission, redirect back to the same form
        return redirect(url_for('report.camera_issue_form'))

    # If the request is a GET request, return the form with existing categories
    return render_template('camera_issue_form.html', categories=existing_categories, username=loginid, menu_list=menu_items)

# Route to fetch camera issue statements based on the selected category
@app.route('/get_camera_issue_statements', methods=['GET'])
def get_camera_issue_statements():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""
    menu_items = lm.get_loginid_menulist()
    category = request.args.get('category')  # Get the category from the request
    # Fetch distinct camera issue statements based on the selected category
    if category:
        statements = CamIssueCollection.distinct('camera_issue_statement', {'camera_issue_category': category})
        return jsonify(statements)
    else:
        return jsonify([])  # Return an empty list if no category is provided
    
# Route to display the form
@app.route('/camera_issue_auditor_view1', methods=['GET'])
def camera_issue_auditor_view1():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""
    menu_items = lm.get_loginid_menulist()
    categories = CamIssueCollection.distinct('camera_issue_category')
    return render_template('camera_issue_auditor_view1.html', categories=categories, username=loginid, menu_list=menu_items)

@app.route('/submit_camera_issue', methods=['GET','POST'])
def submit_camera_issue():
    # Debug: Print all incoming form data
    print("Received Form Data:", request.form)

    # Keep existing user info
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""
    menu_items = lm.get_loginid_menulist()

    pc_title = None
    if loginid:
        pc_profile = PC_profile.find_one({"Assigned User ID": loginid})
        if pc_profile and 'PC Name' in pc_profile:
            pc_name = pc_profile['PC Name']
            pc_profile_table = PCProfileTable.find_one({"pc_name": pc_name})
            if pc_profile_table and 'pc_title' in pc_profile_table:
                pc_title = pc_profile_table['pc_title']

    # Check if this is a status update action
    if 'action' in request.form:
        try:
            action = request.form.get('action')
            client_name = request.form.get('clientName')
            final_report_statement = request.form.get('finalReportStatement')

            # Check if client_name or final_report_statement are None or empty
            if not client_name or not final_report_statement:
                print("Error: Missing required fields!")
                return jsonify({"error": "Missing required fields"}), 400

            # Strip extra spaces only if not None
            client_name = client_name.strip() if client_name else ""
            final_report_statement = final_report_statement.strip() if final_report_statement else ""

            # Debug prints to check values
            print("Client Name:", client_name)
            print("Final Report Statement:", final_report_statement)

            # Prepare update data for different actions
            update_data = {"Last Updated": datetime.now()}
            if action == "Reminded":
                current_doc = QuickReportViewCollection.find_one({"Client Name": client_name, "PC title": pc_title})
                current_count = current_doc.get("Reminder Count", 0) if current_doc else 0
                update_data.update({
                    "CR Status": "Reminded",
                    "Reminder Count": current_count + 1
                })
            elif action == "Cleared":
                update_data.update({
                    "CR Status": "Cleared",
                    "Status": "Closed"
                })
            elif action == "Direct Clear":
                update_data.update({
                    "CR Status": "Directly Cleared",
                    "Status": "Closed"
                })
            elif action == "Cancel":
                update_data.update({
                    "CR Status": "Cancelled",
                    "Status": "Closed"
                })

            # Update both collections if PC title matches
            QuickReportViewCollection.update_many(
                {"Client Name": client_name, "PC title": pc_title},
                {"$set": update_data}
            )
            QuickReportViewCollection.update_many(
                {"Client Name": client_name, "PC title": pc_title},
                {"$set": update_data}
            )

            # Log the action
            log_entry = {
                "action_title": "Camera Issue Action",
                "category": "Issue Management",   
                "sub-category": f"Camera Issue for ({client_name})",
                "count": 0,
                "user_name": m.getfullname(hn.get_username()),
                "action": f"Camera issue action '{action}' performed for client ({client_name})",
                "date_time": datetime.now(),
                "collection_name": CRAuditorCollection.full_name,
                "html_file_source": "camera_issue_reporter_view.html",
                "action_name":"report Initiated",
            }
            Log_table.insert_one(log_entry)

            flash('Action performed successfully!', 'success')
            return redirect(url_for('camera_issue_reporter_view'))

        except Exception as e:
            print("Error:", str(e))
            flash(f'Error performing action: {str(e)}', 'error')
            return redirect(url_for('camera_issue_reporter_view'))

    if request.method=='POST':
        # Existing form submission logic for inserting a new camera issue
        client_name = request.form.get('clientName')
        reference_id = request.form.get('referenceId')
        department_name = request.form.get('departmentName')
        final_report_statement = request.form.get('finalReportStatement')
       
        # Handle multiple camera selections
        camera_select = request.form.get('cameraSelect')  # This will return a list of selected values
        print("Selected Cameras:", camera_select) 
        attachment = request.files.get('attachment')
        camera_issue_category = request.form.get('cameraIssueCategory')
        camera_issue_statement = request.form.get('cameraIssueStatement')
        
        # Check if client_name or final_report_statement are None or empty
        if not client_name or not final_report_statement:
            print("Error: Missing required fields!")
            return jsonify({"error": "Missing required fields"}), 400

        # Strip extra spaces only if not None
        client_name = client_name.strip() if client_name else ""
        final_report_statement = final_report_statement.strip() if final_report_statement else ""
        
        # Convert camera_select back into a list from the JSON string
        camera_select = json.loads(camera_select)

        # Debug prints to check values
        print("Client Name:", client_name)
        print("Final Report Statement:", final_report_statement)

        file_name = None
        if attachment:
            secure_file_name = secure_filename(attachment.filename)
            file_name, _ = os.path.splitext(secure_file_name)

        # Prepare data to insert into Report Form mongo database
        data = {
            "Client Name": client_name,
            "File Name": file_name,
            "Incident Message": camera_issue_statement,
            "Sub Date": datetime.now(),
            "Status": "Initiated",
            "CR Status": "In-Progress",
            "Hold Upto": "N/A",
            "Reference ID": reference_id,
            "Department Name": department_name,
            'camera_select': camera_select,
            "Reminder Count": 0,
            "Overdue Days": 0,
            "Incident Category": camera_issue_category,
            "Final Report Message": camera_issue_statement,
            "PC title": pc_title,
            "Collection ID": reference_id,
            "Initiator ID": hn.get_username(),
            "Call back": "No"
        }

        result = QuickReportViewCollection.insert_one(data)

        # Capture the _id from QuickReportViewCollection
        quick_report_id = result.inserted_id

        # Log the new camera issue submission
        log_entry_new_camera_issue = {
            "action_title": "Form Submission",
            "category": "Report Form",
            "sub-category": f"Camera Issue",
            "user_name": m.getfullname(hn.get_username()),
            "action": f"New camera issue added for ({client_name}) for department ({department_name}) with camera Issue Category as ({camera_issue_category}). Selected Cameras are: {camera_select} Statement: {final_report_statement}.",
            "date_time": datetime.now(),
            "collection_name": CRAuditorCollection.full_name,
            "collection_id": str(quick_report_id),
            "html_file_source": "camera_issue_auditor_view1.html",
            "action_name":"report Initiated"
        }
        Log_table.insert_one(log_entry_new_camera_issue)

        # If only department is selected and no cameras are selected
        if department_name and not camera_select:
            # Find the department document in the departmentcollection
            department_doc = departmentcollection.find_one({"Client Name": client_name, "Department Name/Port Number": department_name})

            if department_doc:
                # Update department status
                update_result = departmentcollection.update_one(
                    {"_id": department_doc["_id"]},
                    {"$set": {
                        "Department Status": camera_issue_category,
                        "Department Status Date": datetime.now()
                    }}
                )
                print(f"Department status updated: {update_result.modified_count} document(s) modified.")
            else:
                print("Department document not found.")

        # Handle camera select updates for multiple selections
        if camera_select:
            for i, camera_info in enumerate(camera_select, 1):
                # Split the camera info into separate camera number and name if necessary
                camera_number, camera_name = camera_info.split(":") if ":" in camera_info else (camera_info, "")
                camera_number = camera_number.strip()
                camera_name = camera_name.strip()

                # Find the document for the given client
                camera_doc = cameracollection.find_one({"Client Name": client_name, "Department Name/Port Number": department_name, "Camera Number": camera_number})
                
                if camera_doc:
                    update_result = cameracollection.update_one(
                        {"_id": camera_doc["_id"]},
                        {"$set": {
                            "Camera Status": camera_issue_category,
                            "Camera Stauts Date": datetime.now()
                            }}
                    )

                    if update_result.modified_count > 0:
                        print(f"Camera status updated to {camera_issue_category} for camera {camera_number}.")
                    else:
                        print("No update was made to Camera Status.")

        # Check if both insertions were successful
        if result.inserted_id: 
            return jsonify({"message": "Data inserted successfully!"}), 200
        else:
            return jsonify({"error": "Failed to insert data"}), 500
  
@app.route('/camera_issue_reporter_view')
def camera_issue_reporter_view():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""
    menu_items = lm.get_loginid_menulist()

    today = datetime.today().date()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = datetime.combine(today, datetime.max.time())

    # Get reminder count for today
    reminded_count = QuickReportViewCollection.count_documents({
        "CR Status": "Requested to Remind",
        "Last Updated": {
            "$gte": start_of_day,
            "$lte": end_of_day
        }
    })

    # Fetch reports with calculated overdue status
    reports = list(QuickReportViewCollection.find({"Status": {"$in": ["Reported", "Requested to Remind"]}}))

    for report in reports:
        # Check if 'Hold Upto' exists in the report, otherwise set it to 'N/A'
        hold_upto = report.get('Hold Upto', 'N/A')  # Default to 'N/A' if not present
        
        if hold_upto != 'N/A':
            try:
                hold_date = datetime.strptime(hold_upto, '%Y-%m-%d').date()
                if today > hold_date:
                    report['Overdue'] = (today - hold_date).days
                else:
                    report['Overdue'] = 0
            except (ValueError, TypeError):
                report['Overdue'] = 0
        else:
            report['Overdue'] = 0  # Set overdue to 0 if 'Hold Upto' is 'N/A'

    return render_template('camera_issue_reporter_view.html',
                          data=reports,
                          username=loginid,
                          menu_list=menu_items,
                          reminded_count=reminded_count)

@app.route('/request_to_remind', methods=['GET','POST'])
def request_to_remind():
    report_id=request.form.get('reportID')
    print(f"test:{report_id}")

    if not report_id:
        return jsonify({"message": "Report ID is required."}), 400
    
    try:
        # Fetch the current reminder count from Camera_Issue_Auditor collection
        client_data = QuickReportViewCollection.find_one({"_id": ObjectId(report_id)})
        print(f"client data is: {client_data}")

        if client_data:
            # Get Reminder Count and ensure it's an integer
            current_reminder_count = client_data.get("Reminder Count", 0)
            print(f"Current Reminder Count: {current_reminder_count} (Type: {type(current_reminder_count)})")  # Log current_reminder_count type

            # Ensure current_reminder_count is an integer
            try:
                current_reminder_count = int(current_reminder_count)
            except ValueError:
                current_reminder_count = 0  # Default to 0 if it cannot be converted to an integer
                print("Reminder Count was not a valid integer, defaulting to 0.")

            # Increment the reminder count by 1
            new_reminder_count = current_reminder_count + 1

            # Update the Reminder Count in Camera_Issue_Auditor collection
            result_auditor = QuickReportViewCollection.update_one(
                {"_id": ObjectId(report_id)},
                {"$set": {
                    "Reminder Count": new_reminder_count,
                    "CR Status": "Requested to Remind",
                    "CR Status Updation Date": datetime.now()
                }}
            )

            # Log the new camera issue submission
            log_entry_request_to_remind = {
                "action_title": "Form Submission",
                "category": "Report Form",
                "sub-category": f"Camera Issue",
                "user_name": m.getfullname(hn.get_username()),
                "action": f"Requested to remind for camera issue for {client_data.get('Client Name')}.",
                "date_time": datetime.now(),
                "collection_name": QuickReportViewCollection.full_name,
                "html_file_source": "camera_issue_auditor_view1.html",
                "Collection ID": report_id,
                "action_name": "Requested to Remind"
            }

            Log_table.insert_one(log_entry_request_to_remind)
            
            # Check if the update was successful in either collection
            if result_auditor.modified_count > 0:
                # Ensure client_name and new_reminder_count are converted to strings before concatenation
                return jsonify({
                    "message": f"Reminder count updated to {str(new_reminder_count)} for {str(client_data.get('Client Name'))}."
                }), 200
            else:
                return jsonify({"message": "Failed to send reminder, client not found or update failed."}), 500
        else:
            return jsonify({"message": f"Client {str(client_data.get('Client Name'))} not found."}), 404

    except Exception as e:
        # Log the error message and return a more informative response
        print(f"Error occurred: {e}")
        return jsonify({"message": f"Error: {str(e)}"}), 500


@app.route('/request_to_clear', methods=['POST'])
def request_to_clear():
    report_id = request.form.get('reportID')
    clearing_reason = request.form.get('clearingReason')  # Get Clearing Reason
    client_name = request.form.get('clientName')  # Get Client Name

    print(f"Report ID: {report_id}, Client Name: {client_name}, Clearing Reason: {clearing_reason}")

    try:
        # Update the CR Status and Clearing Reason in the database
        result_auditor = QuickReportViewCollection.update_one(
            {"_id": ObjectId(report_id)},
            {"$set": {"CR Status": "Requested to Clear", "Clearing Reason": clearing_reason}}
        )

        # Log the request to clear with reason and client name
        log_entry_request_to_clear = {
            "action_title": "Form Submission",
            "category": "Report Form",
            "sub-category": "Camera Issue",
            "user_name": m.getfullname(hn.get_username()),
            "action": f"Requested to clear for camera issue. Reason: {clearing_reason}",
            "date_time": datetime.now(),
            "collection_name": QuickReportViewCollection.full_name,
            "html_file_source": "camera_issue_auditor_view1.html",
            "action_name": "Requested to Clear",
            "client_name": client_name
        }

        Log_table.insert_one(log_entry_request_to_clear)

        log_entry_request_to_clear_popup = {
            "category": "Report Form",
            "sub-category": "Camera Issue",
            "user_name": m.getfullname(hn.get_username()),
            "action Statement": f"Requested to clear for Camera Issue for ({client_name}) - Reason: {clearing_reason}",
            "date_time": datetime.now()
        }

        Logs_popup.insert_one(log_entry_request_to_clear_popup)

        if result_auditor.modified_count > 0:
            return jsonify({"message": f"Clear request sent for {client_name} with reason: {clearing_reason}."}), 200
        else:
            return jsonify({"message": "Failed to clear, client not found."}), 500
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500
    
@app.route('/client_cr_status', methods=['POST'])
def client_cr_status():
    try:
        # Retrieve the data from the form
        client_name = request.form.get('changeClientName')
        client_id = request.form.get('changeClientID')
        status = request.form.get('status')  # Get selected status
        hold_date = request.form.get('holdDate')  # Get the hold date if provided
        remark = request.form.get('remark')  # Get the remark from the form
        report_id = request.form.get('reportId')  # Get Report ID (_id from MongoDB)
        print("Report ID:", report_id)

        # Ensure the report_id is a valid ObjectId
        if not ObjectId.is_valid(report_id):
            flash('Invalid Report ID.', 'error')
            return redirect(url_for('report.camera_issue_reporter_view'))

        # Prepare the update data based on the status
        update_data = {
            "Last Updated": datetime.now(),
            "Remark": remark,
        }

        # Handle different statuses and update MongoDB accordingly
        if status == "Ignore":
            update_data["CR Status"] = "Ignored"
        elif status == "Hold":
            update_data["CR Status"] = "Hold"
            if hold_date:
                update_data["Hold Upto"] = hold_date
        else:
            update_data["CR Status"] = status

        # Update QuickReportViewCollection with the new CR Status and other fields
        result = QuickReportViewCollection.update_one(
            {"_id": ObjectId(report_id)},  # Use the Report ID (_id) to identify the document
            {"$set": update_data}
        )

        if result.matched_count == 0:
            flash('No matching report found with the given Report ID.', 'error')
            return redirect(url_for('report.camera_issue_reporter_view'))

        # Log the status change for auditing purposes
        log_entry = {
            "action_title": "CR Status Change",
            "category": "Status Management",
            "sub-category": f"CR Status for ({client_name})",
            "count": 0,
            "user_name": m.getfullname(hn.get_username()),
            "action": f"CR Status changed to '{status}' for client ({client_name})",
            "date_time": datetime.now(),
            "collection_name": CRAuditorCollection.full_name,
            "html_file_source": "camera_issue_reporter_view.html"
        }
        Log_table.insert_one(log_entry)

        # Display success message and redirect back
        flash('CR Status updated successfully!', 'success')
        return redirect(url_for('report.camera_issue_reporter_view'))

    except Exception as e:
        flash(f'Error updating CR Status: {str(e)}', 'error')
        return redirect(url_for('report.camera_issue_reporter_view'))
    
@app.route('/get_sentences', methods=['GET'])
def get_sentences():
    words = request.args.get('word', '').split()
    client_name = request.args.get('client', '')

    if not words or not client_name:
        return jsonify([])

    queries = [{"Incident Sentence": {"$regex": f".*{re.escape(word)}.*", "$options": "i"}} for word in words]
    queries.append({"Client Name": client_name})  # Filter by client name

    results = incidentsentencescollection.find({"$and": queries})

    sentences = [result['Incident Sentence'] for result in results]

    return jsonify(sentences)

@app.route('/autocorrect_sentence', methods=['POST'])
def autocorrect_sentence_route():
    data = request.get_json()
    
    if 'Incident Sentence' not in data:
        return jsonify({"error": "No sentence provided"}), 400

    sentence = data['Incident Sentence']
    
    # Apply the autocorrection using T5 model
    corrected_sentence = grammar_corrector(f"correct grammar: {sentence}")[0]['generated_text']
    
    return jsonify({"corrected_sentence": corrected_sentence})

@app.route('/add_report', methods=['POST'])
def add_report():
    data = request.json  # Get the incoming data from the client

    # Dynamically retrieve the PC Title
    loginid = lm.get_user_info()[0]  # Assuming lm.get_user_info() returns a tuple (loginid, ...)
    pc_title = "Unknown"
    if loginid:
        pc_profile = PC_profile.find_one({"Assigned User ID": loginid})
        # If the profile exists and contains the 'PC Name'
        if pc_profile and 'PC Name' in pc_profile:
            pc_name = pc_profile['PC Name']
            pc_profile_table = PCProfileTable.find_one({"pc_name": pc_name})
            # Extract the pc_title if available
            if pc_profile_table and 'pc_title' in pc_profile_table:
                pc_title = pc_profile_table['pc_title']

    # Prepare the report data to be inserted into MongoDB
    new_report = {
        "Client Name": data.get("Client Name", ""),
        "Department Name": data.get("Department Name", ""),
        "Camera Number": data.get("Camera Number", ""),
        "Short Message": data.get("Short Message", ""),
        "File Name": data.get("File Name", ""),
        "Status": "Drafted",  # Default status
        "Status Date-Time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "Status Changer Name": m.getfullname(hn.get_username()),
        "PC Name": pc_title
    }

    try:
        result = QuickReportViewCollection.insert_one(new_report)
        # Capture the _id from QuickReportViewCollection
        quick_report_id = result.inserted_id
    
        # Log the status change for auditing purposes
        log_entry = {
            "action_title": "Form Submission",
            "category": "Report Form",
            "sub-category": "Incidence Report",
            "user_name": m.getfullname(hn.get_username()),
            "action": f"New Incident report added for ({new_report['Client Name']}).",
            "date_time": datetime.now(),
            "collection_name": QuickReportViewCollection.full_name,
            "html_file_source": "camera_issue_reporter_view.html",
            "collection_id": str(quick_report_id),
            "html_file_source": "initiated_reports_view_reporter_view.html"
        }

        Log_table.insert_one(log_entry)
    
        return jsonify({
            "success": True,
            "message": "Report added successfully!",
            "report_id": str(result.inserted_id)
        })
    
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
    
'''@app.route('/sreport/<report_id>', methods=['POST'])
def update_report(report_id):
    data = request.json

    # Prepare the data to update the report
    updated_data = {
        "Client Name": data.get("clientName"),
        "Department Name": data.get("departmentName"),
        "Camera Number": data.get("cameraNumber"),
        "Short Message": data.get("shortMessage"),
        "File Name": data.get("fileName"),
        "Incident Date": data.get("incidentDate"),
        "Incident Time": data.get("incidentTime"),
        "Keywords": data.get("keywords"),
        "Report Message": data.get("reportMessage"),
        "Incident Message": data.get("incidentMessage"),
        "Incident Category": data.get("incidentCategory"),
        "Report Category": data.get("reportCategory"),
        "Month Year (String)": data.get("monthYearString"),
        "Month Year (Number)": data.get("monthYearNumber"),
        "Status": "Intiated",
        "Status Date-Time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
        "Status Changer Name": m.getfullname(hn.get_username()),
    }

    try:
        result = QuickReportViewCollection.update_one(
            {'_id': ObjectId(report_id)},
            {'$set': updated_data}
        )

        if result.modified_count > 0:
            flash("Report updated successfully.", "success")
        else:
            flash("Report not found or no changes made.", "error")

    except Exception as e:
        flash(f"Error updating report: {str(e)}", "error")

    return redirect(url_for('index'))  # Redirect to an appropriate page (e.g., list of reports)'''

@app.route('/update_report/<report_id>', methods=['POST'])
def update_report(report_id):
    data = request.json

    # Dynamically retrieve the PC Title
    loginid = lm.get_user_info()[0]  # Assuming lm.get_user_info() returns a tuple (loginid, ...)
    pc_title = None

    if loginid:
        pc_profile = PC_profile.find_one({"Assigned User ID": loginid})

        # If the profile exists and contains the 'PC Name'
        if pc_profile and 'PC Name' in pc_profile:
            pc_name = pc_profile['PC Name']
            pc_profile_table = PCProfileTable.find_one({"pc_name": pc_name})

            # Extract the pc_title if available
            if pc_profile_table and 'pc_title' in pc_profile_table:
                pc_title = pc_profile_table['pc_title']

    # Prepare the data to update the report
    updated_data = {
        "Client Name": data.get("clientName"),
        "Department Name": data.get("departmentName"),
        "Camera Number": data.get("cameraNumber"),
        "Short Message": data.get("shortMessage"),
        "File Name": data.get("fileName"),
        "Incident Date": data.get("incidentDate"),
        "Incident Time": data.get("incidentTime"),
        "Keywords": data.get("keywords"),
        "Report Message": data.get("reportMessage"),
        "Incident Message": data.get("incidentMessage"),
        "Final Report Message":data.get("incidentMessage"),
        "Incident Category": data.get("incidentCategory"),
        "Report Category": data.get("reportCategory"),
        "Month Year (String)": data.get("monthYearString"),
        "Month Year (Number)": data.get("monthYearNumber"),
        "Status": "Initiated",
        "Status Date-Time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "Status Creator": m.getfullname(hn.get_username()),
        "PC title": pc_title,
        "Call back" : "No",
        "Response":"",
        "Responder":"",
        "Remark":""
    
    }

    try:
        result = QuickReportViewCollection.update_one(
            {'_id': ObjectId(report_id)},
            {'$set': updated_data}
        )

        if result.modified_count > 0:
            flash("Report updated successfully.", "success")
        else:
            flash("Report not found or no changes made.", "error")

    except Exception as e:
        flash(f"Error updating report: {str(e)}", "error")

    return redirect(url_for('index'))  # Redirect to an appropriate page (e.g., list of reports)

@app.route('/update_report_status', methods=['POST'])
def update_report_status():
    data = request.json  # Get JSON data from the body of the request
    print(f"Test:{data}")
    try:
        # Extract reportId, status, and uniqueNumber from the request data
        reportId = data.get('report_id')
        status = data.get('status')

        # Validate the reportId to ensure it's a valid ObjectId
        #print(f"number is:{QuickReportViewCollection.find_one({'_id':ObjectId(reportId)}).get('Final Report Statement').split(':')[0]}")
        #.get('Final Report Statement').split(':')[0]
        # Update the report in the database with the new status and unique number
        result = QuickReportViewCollection.update_one(
            {'_id': ObjectId(reportId)},
            {'$set': {'Status': status, 'Unique Number': QuickReportViewCollection.find_one({'_id':ObjectId(reportId)})['Final Report Message'].split(':')[0]}}
        )

        updated_collection_id=QuickReportViewCollection.find_one({'_id':ObjectId(reportId)}).get('_id')
        print(f"collection Id: {updated_collection_id}")
        
        # Log the status change for auditing purposes
        log_entry_reporter_approval = {
            "action_title": "Form Submission",
            "category": "Report Form",
            "sub-category": "Incidence Report",
            "user_name": m.getfullname(hn.get_username()),
            "action": f"Incident report approved by reporter & Unique number is generated.",
            "date_time": datetime.now(),
            "collection_name": QuickReportViewCollection.full_name,
            "html_file_source": "camera_issue_reporter_view.html",
            "collection_id": str(updated_collection_id),
            "html_file_source": "initiated_reports_view_reporter_view.html",
            "action_name":"Reported"
        }

        Log_table.insert_one(log_entry_reporter_approval)
           
        # Check if the update was successful
        if result.modified_count > 0:
            return jsonify({"success": True, "message": "Status updated successfully."})
        else:
            return jsonify({"success": False, "message": "Report not found or status already updated."})
    
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
    
@app.route('/update_report_status_2/<report_id>', methods=['POST'])
def update_report_status_2(report_id):
    data = request.json
    try:
        result = QuickReportViewCollection.update_one(
            {'_id': ObjectId(report_id)},
            {'$set': {'Status': data['Status']}}
        )
        if result.modified_count > 0:
            return jsonify({"success": True, "message": "Status updated successfully."})
        else:
            return jsonify({"success": False, "message": "Report not found or status already updated."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
    

@app.route('/get_incident_category', methods=['GET'])
def get_incident_category():
    sentence = request.args.get('sentence', '')

    if not sentence:
        return jsonify({"error": "No sentence provided"}), 400

    # Query the `incidentSentencesCollection` to find the matching sentence
    result = incidentsentencescollection.find_one({
        "Incident Sentence": sentence
    })
    
    if result:
        # Return the corresponding Incident Category
        return jsonify({"incidentCategory": result.get("Incident Category", "Not Found")})
    else:
        return jsonify({"incidentCategory": "Not Found"})
    
@app.route('/get_entity_type')
def get_entity_type():
    entity_title = request.args.get('entityTitle', '')
    if not entity_title:
        return jsonify({'error': 'Entity Title is required'}), 400

    # Query the database to find the Entity Type for the given Entity Title
    entity = entitysentencescollection.find_one({'Entity Title': entity_title}, {'Entity Type': 1})
    
    if entity and 'Entity Type' in entity:
        return jsonify({'entityType': entity['Entity Type']})
    else:
        return jsonify({'entityType': None})
    
@app.route('/get_report_data/<report_id>', methods=['GET'])
def get_report_data(report_id):
    try:
        # Fetch report data from the database
        report = QuickReportViewCollection.find_one({'_id': ObjectId(report_id)})
        if not report:
            return jsonify({"success": False, "message": "Report not found"})

        # Prepare the response data
        report_data = {
            "clientName": report.get("Client Name", ""),
            "departmentName": report.get("Department Name", ""),
            "cameraNumber": report.get("Camera Number", ""),
            "shortMessage": report.get("Short Message", ""),
            "fileName": report.get("File Name", "")
        }

        return jsonify({"success": True, "report": report_data})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

    
@app.route('/update_report_field/<report_id>', methods=['POST'])
def update_report_field(report_id):
    data = request.json
    
    try:
        # Get current PC title
        loginid = lm.get_user_info()[0]
        pc_title = None
        
        if loginid:
            pc_profile = PC_profile.find_one({"Assigned User ID": loginid})
            if pc_profile and 'PC Name' in pc_profile:
                pc_name = pc_profile['PC Name']
                pc_profile_table = PCProfileTable.find_one({"pc_name": pc_name})
                if pc_profile_table and 'pc_title' in pc_profile_table:
                    pc_title = pc_profile_table['pc_title']

        # Add additional fields
        update_data = {
            **data,
            "Status": "Drafted",
            "Status Date-Time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "Status Changer Name": m.getfullname(hn.get_username()),
            "PC Name": pc_title
        }

        result = QuickReportViewCollection.update_one(
            {'_id': ObjectId(report_id)},
            {'$set': update_data}
        )

        if result.modified_count > 0:
            return jsonify({"success": True, "message": "Field updated successfully"})
        else:
            return jsonify({"success": False, "message": "No changes made or report not found"})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/quick_report')
def index():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""
    menu_items = lm.get_loginid_menulist()

    # Fetch PC profile based on loginid
    pc_title = None
    if loginid:
        pc_profile = PC_profile.find_one({"Assigned User ID": loginid})

        # If the profile exists and contains the 'PC Name'
        if pc_profile and 'PC Name' in pc_profile:
            pc_name = pc_profile['PC Name']
            pc_profile_table = PCProfileTable.find_one({"pc_name": pc_name})

            # Extract the pc_title if available
            if pc_profile_table and 'pc_title' in pc_profile_table:
                pc_title = pc_profile_table['pc_title']

    # Get reports for the specific PC Name
    reports = list(QuickReportViewCollection.find({
        'Status': 'Drafted',
        'PC Name': pc_title  # Only include reports matching the current PC Name
    }))

    clients_list = []
    
    # Fetch clients linked to the current pc_title from the profile
    if pc_title:
        client_data = clientDeptLink.find({"pc_title": pc_title}, {"client_registration_number": 1, "_id": 1})
        for client in client_data:
            clients_list.append({
                "registration_number": client.get("client_registration_number"),
                "_id": str(client.get("_id")),  # Convert _id to string for easy rendering
                "name": client.get("client_registration_number")  # Assuming client name is client_registration_number
            })

    # Fetch the client, department, and camera data linked to the dynamically fetched pc_title
    clients = []
    departments = []
    cameras = []
    if pc_title:
        client_data = clientDeptLink.find({"pc_title": pc_title}, {'client_registration_number': 1, 'department': 1, 'Camera Number': 1})
        # Extract unique values for dropdown options
        clients = list(set([entry['client_registration_number'] for entry in client_data]))
        departments = list(set([entry['department'] for entry in client_data]))
        cameras = list(set([entry['Camera Number'] for entry in client_data]))

    # Fetch the list of entity titles dynamically from MongoDB
    entity_titles = []
    entity_data = entitysentencescollection.find({'Entity Type': 'Human-Entity-P'})
    for entity in entity_data:
        entity_titles.append(entity.get('Entity Title', ''))

    return render_template('quick_report_view.html', reports=reports, clients=clients, clients_list=clients_list, departments=departments, cameras=cameras, entity_titles=entity_titles, username=loginid, menu_list=menu_items)

@app.route('/check_criteria', methods=['GET'])
def check_criteria():
    # Get today's date (without time)
    today = datetime.now().date()

    # Query the MongoDB collection
    result = QuickReportViewCollection.find_one({
        "CR Status": "Requested to Remind",
        "Sub Date": today
    })

    # Check if the document exists and return the appropriate status
    if result:
        return jsonify({"status": "Disabled"})
    else:
        return jsonify({"status": "Enabled"})
    
@app.route('/get_client_cr_status', methods=['GET'])
def get_client_cr_status():
    client_id1 = request.args.get('client_id')  # Get the _id instead of reference_id
    print(f"client id:{client_id1}")
    # Validate if client_id is a valid ObjectId
    try:
        client_id = ObjectId(client_id1)  # Convert string to ObjectId
    except Exception as e:
        return jsonify({"success": False, "message": "Invalid client ID"}), 400
    
    # Query the database to fetch the CR Status and CR Status Updation Date for the client and _id
    client_data = QuickReportViewCollection.find_one({"_id": client_id})
    print(client_data)
    if client_data:
        cr_status = client_data.get("CR Status", "N/A")
        reminder_count = client_data.get("reminder_count", 0)
        cr_status_updation_date = client_data.get("CR Status Updation Date", None)
        
        # Default button enable/disable states
        remind_button_disabled = False
        clear_button_disabled = False

        # Logic to handle button states based on the CR Status and CR Status Updation Date
        today_date = datetime.today().date().strftime('%d-%m-%Y')
        df_logs = Log_table.find({
            'collection_id': client_id1,
            'action_name': {'$in': ['Requested to Remind','Reported']}
        }).sort('date_time', -1).limit(1)
        
        print(f"logs:{df_logs[0]}")
        if cr_status == 'In-Progress':
            if df_logs and df_logs[0].get('date_time').date().strftime('%d-%m-%Y')==today_date:
                remind_button_disabled = True  # Disable "Request to Remind" if updated today
                clear_button_disabled = True  # Enable "Request to Clear"
            else:
                remind_button_disabled = False  # Disable "Request to Remind" if updated today
                clear_button_disabled = False  # Enable "Request to Clear"
        else:
            remind_button_disabled = True  # Disable "Request to Remind"
            clear_button_disabled = True  # Enable "Request to Clear"

        # Returning response to frontend with button states
        return jsonify({
            "success": True,
            "crStatus": cr_status,
            "clientName":client_data.get('Client Name'),
            "cameraName":client_data.get('camera_select'),
            "reminderCount": reminder_count,
            "remindButtonDisabled": remind_button_disabled,
            "clearButtonDisabled": clear_button_disabled
        })
    else:
        return jsonify({"success": False, "message": "Client or _id not found"}), 404
    
@app.route('/update_reminder', methods=['POST'])
def update_reminder():
    # Get the request data
    data = request.get_json()
    client_name = data.get('client_name')
    client_id = data.get('client_id')
    print(f"client ID for reminder is:{client_id}")
    cr_status = data.get('cr_status')  # Expected "Reminded"
    status = data.get('status')        # Expected "In-Progress"

    if not client_name or not client_id:
        return jsonify({"message": "Client name and client ID are required."}), 400

    try:
        # Update CR Status and Status in Camera_Issue_Auditor collection
        result_auditor = QuickReportViewCollection.update_one(
            {"Client Name": client_name},
            {
                "$set": {
                    "CR Status": cr_status,
                    "Status": status,
                    "CR Status Updation Date": datetime.now()
                }
            }
        )

        # Update CR Status and Status in Camera_Issue_Reporter collection
        '''result_reporter = CIAuditorReporter.update_one(
            {"Client Name": client_name},
            {
                "$set": {
                    "CR Status": cr_status,
                    "Status": status,
                    "CR Status Updation Date": datetime.now()
                }
            }
        )'''

        # Check if the update was successful in both collections
        if result_auditor.modified_count > 0:
            return jsonify({"success": True, "message": f"Reminder has been sent and status updated to 'Reminded' and 'In-Progress' for {client_name}."}), 200
        else:
            return jsonify({"success": False, "message": "Failed to update the status or client not found."}), 500

    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@app.route('/update_clear', methods=['POST'])
def update_clear():
    # Get the request data
    data = request.get_json()
    client_name = data.get('client_name')
    print(f"client name is:{client_name}")
    client_id = data.get('client_id')
    print(f"client ID is:{client_id}")
    cr_status = data.get('cr_status')  # Expected "Cleared"

    if not client_name or not client_id:
        return jsonify({"message": "Client name and client ID are required."}), 400

    try:
        # Update CR Status and Status in Camera_Issue_Auditor collection
        result_auditor = QuickReportViewCollection.update_one(
            {"_id": ObjectId(client_id)},
            {
                "$set": {
                    "CR Status": cr_status,
                    "CR Status Updation Date": datetime.now()
                }
            }
        )

        '''result_reporter = CIAuditorReporter.update_one(
            {"_id": ObjectId(client_id)},
            {
                "$set": {
                    "CR Status": cr_status,
                    "CR Status Updation Date": datetime.now()
                }
            }
        )'''

        # Check if the update was successful in both collections
        if result_auditor.modified_count > 0:
            return jsonify({"success": True, "message": f"Status has been cleared and updated to 'Cleared' for {client_name}."}), 200
        else:
            return jsonify({"success": False, "message": "Failed to update the status or client not found."}), 500

    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500
    
@app.route('/update_direct_clear', methods=['POST'])
def update_direct_clear():
    # Get the request data
    data = request.get_json()

    # Print the received data to debug
    print(f"Received data: {data}")

    client_name = data.get('client_name')
    client_id = data.get('client_id')
    cr_status = data.get('cr_status')  # Expected "Cleared"
    status = data.get('status')

    # Debugging the values
    print(f"client name is: {client_name}")
    print(f"client ID is: {client_id}")
    print(f"cr_status is: {cr_status}")
    print(f"status is: {status}")

    if not client_name or not client_id:
        return jsonify({"message": "Client name and client ID are required."}), 400

    try:
        # Update CR Status and Status in Camera_Issue_Auditor collection
        result_auditor = QuickReportViewCollection.update_one(
            {"_id": ObjectId(client_id)},
            {
                "$set": {
                    "CR Status": cr_status,
                    "Status": status,
                    "CR Status Updation Date": datetime.now()
                }
            }
        )

        '''result_reporter = CIAuditorReporter.update_one(
            {"_id": ObjectId(client_id)},
            {
                "$set": {
                    "CR Status": cr_status,
                    "Status": status,
                    "CR Status Updation Date": datetime.now()
                }
            }
        )'''

        # Check if the update was successful in both collections
        if result_auditor.modified_count > 0:
            return jsonify({"success": True, "message": f"Status has been cleared and updated to 'Cleared' for {client_name}."}), 200
        else:
            return jsonify({"success": False, "message": "Failed to update the status or client not found."}), 500

    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500
    
@app.route('/update_cancel', methods=['POST'])
def update_cancel():
    # Get the request data
    data = request.get_json()
    
    # Debugging the received data
    print(f"Received data: {data}")
    
    client_name = data.get('client_name')
    client_id = data.get('client_id')
    cr_status = data.get('cr_status')  # Expected "Cancelled"
    status = data.get('status')        # Expected "Cancelled"

    # Debugging: Log the received values
    print(f"client_name: {client_name}")
    print(f"client_id: {client_id}")
    print(f"cr_status: {cr_status}")
    print(f"status: {status}")

    # Check if all required fields are present
    if not client_name or not client_id or not cr_status or not status:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # Update CR Status and Status in Camera_Issue_Auditor collection
        result_auditor = QuickReportViewCollection.update_one(
            {"_id": ObjectId(client_id)},
            {
                "$set": {
                    "CR Status": cr_status,
                    "Status": status,
                    "CR Status Updation Date": datetime.now(),
                    "call back": "No"
                }
            }
        )

        '''result_reporter = CIAuditorReporter.update_one(
            {"_id": ObjectId(client_id)},
            {
                "$set": {
                    "CR Status": cr_status,
                    "Status": status,
                    "CR Status Updation Date": datetime.now(),
                    "call back": "No"
                }
            }
        )'''

        # Check if the update was successful in both collections
        if result_auditor.modified_count > 0:
            return jsonify({"success": True, "message": f"Status has been cancelled and updated to 'Cancelled' for {client_name}."}), 200
        else:
            return jsonify({"success": False, "message": "Failed to update the status or client not found."}), 500

    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500
    
@app.route('/cancelled_reports', methods=['GET'])
def cancelled_reports():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()

    if check_login != loginid:
        loginid = ""
        
    menu_items = lm.get_loginid_menulist()

    # Collect filters from URL parameters
    _id_filter = request.args.get('_id')
    client_name_filter = request.args.get('client_name')
    callback_filter = request.args.get('call_back', 'No')  # Default to 'No' if not specified

    # **Set Exact Status Filters** (Do NOT modify case)
    status_filter = ['Declined','cancelled']

    '''# 🔍 Debugging: Check stored statuses in MongoDB
    stored_statuses = QuickReportViewCollection.distinct("Status")
    print(f"⚡ Unique Statuses Found in DB: {stored_statuses}")

    # ✅ Ensure our exact status values exist in the DB
    if not any(status in stored_statuses for status in status_filter):
        print("⚠️ No matching statuses found in DB!")'''
    
    # 🔎 Query Construction
    query_filter = {
        "Status": {"$in": status_filter}
    }

    '''query_filter = {
        "Call back": callback_filter
    }'''
    '''if _id_filter:
        query_filter["_id"] = ObjectId(_id_filter)
    if client_name_filter:
        query_filter["Client Name"] = client_name_filter

    print(f"🔎 Query Filter Being Used: {query_filter}")'''

    # Fetch records
    cancelled_reports = list(QuickReportViewCollection.find({"Status": {"$in": status_filter}, "Call back": callback_filter}))
    print(cancelled_reports)

    #print(f"✅ Reports Found: {len(cancelled_reports)}")  # Debugging

    # Process report data
    data = []
    for report in cancelled_reports:
        camera_name = report.get("Camera Number", "N/A")
        if ":" in camera_name:
            camera_name = camera_name.split(":", 1)[1].strip()  # Extract camera name after ":"

        data.append({
            "Client Name": report.get("Client Name", "N/A"),
            "Department Name": report.get("Department Name", "N/A"),
            "Camera Name": camera_name,
            "Final Report Statement": report.get("Incident Message", "N/A"),
            "Incident Category": report.get("Incident Category", "N/A"),
            "Camera Issue Category": report.get("Camera Issue Category", "N/A"),
            "Action": "Enable" if report.get("call back") == "No" else "Disabled",
            "call_back": report.get("Callback", "N/A"),
            "_id": str(report.get("_id", "N/A"))
        })

    # If no records, show a message
    if not data:
        flash("No records found with the applied filters", "info")

    return render_template('cancelled_reports.html', data=data, username=loginid, menu_list=menu_items, client_name_filter=client_name_filter, _id_filter=_id_filter)


@app.route('/initiated_report')
def initiated_report():
    loginid, portal_user_title = lm.get_user_info()  # Get the logged-in user's ID
    check_login = hn.get_username()  # Check login status
    if check_login != loginid:
        loginid = ""
    
    menu_items = lm.get_loginid_menulist()

    # Fetch PC profile based on loginid
    pc_title = None
    if loginid:
        pc_profile = PC_profile.find_one({"Assigned User ID": loginid})

        # If the profile exists and contains the 'PC Name'
        if pc_profile and 'PC Name' in pc_profile:
            pc_name = pc_profile['PC Name']
            pc_profile_table = PCProfileTable.find_one({"pc_name": pc_name})

            # Extract the pc_title if available
            if pc_profile_table and 'pc_title' in pc_profile_table:
                pc_title = pc_profile_table['pc_title']

    # Fetch the client, department, and camera data linked to the dynamically fetched pc_title
    clients = []
    departments = []
    cameras = []
    if pc_title:
        client_data = clientDeptLink.find({"pc_title": pc_title}, {'client_registration_number': 1, 'department': 1, 'Camera Number': 1})
        # Extract unique values for dropdown options
        clients = list(set([entry['client_registration_number'] for entry in client_data]))
        departments = list(set([entry['department'] for entry in client_data]))
        cameras = list(set([entry['Camera Number'] for entry in client_data]))

    # Fetch the initiated reports
    initiated_reports = list(QuickReportViewCollection.find({'Status': 'Initiated', 'PC title': pc_title})
                         .sort('Status Date-Time', -1))

    # Add the 'show_cancel_button' flag based on whether the loginid matches the Initiator ID
    for report in initiated_reports:
        if report.get('Initiator ID') == loginid:
            report['show_cancel_button'] = True  # Show the cancel button
        else:
            report['show_cancel_button'] = False  # Hide the cancel button

    return render_template('initiated_reports_view_auditor_view.html', 
                           username=loginid, 
                           menu_list=menu_items, 
                           clients=clients, 
                           initiated_reports=initiated_reports, 
                           departments=departments, 
                           cameras=cameras)

@app.route('/add_report1', methods=['POST'])
def add_report1():
    data = request.json
    client_name=data.get("clientName")

    # Dynamically retrieve the PC Title
    loginid = lm.get_user_info()[0]  # Assuming lm.get_user_info() returns a tuple (loginid, ...)
    pc_title = None

    if loginid:
        pc_profile = PC_profile.find_one({"Assigned User ID": loginid})

        # If the profile exists and contains the 'PC Name'
        if pc_profile and 'PC Name' in pc_profile:
            pc_name = pc_profile['PC Name']
            pc_profile_table = PCProfileTable.find_one({"pc_name": pc_name})

            # Extract the pc_title if available
            if pc_profile_table and 'pc_title' in pc_profile_table:
                pc_title = pc_profile_table['pc_title']
    print(f"data is: {data}")
    # Prepare the data to insert into the collection
    new_report = {
        "Client Name": data.get("clientName"),
        "Department Name": data.get("departmentName"),
        "camera_select": data.get("cameraNumber"),
        "File Name": data.get("fileName"),
        "Incident Date": data.get("incidentDate"),
        "Incident Time": data.get("incidentTime"),
        "Keywords": data.get("keywords"),
        "Report Message": data.get("reportMessage"),
        "Incident Message": data.get("incidentMessage"),
        "Final Report Message": data.get("incidentMessage"),
        "Incident Category": data.get("incidentCategory"),
        "Report Category": data.get("reportCategory"),
        "Month Year (String)": data.get("monthYearString"),
        "Month Year (Number)": data.get("monthYearNumber"),
        "Status": "Initiated",
        "Status Date-Time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "Status Creator": m.getfullname(hn.get_username()),
        "PC title": pc_title,
        "Call back": "No",
        "Response": "",
        "Responder": "",
        "Remark": "",
        "Initiator ID": hn.get_username(),
        "CR Status":"In-Progress",
        "Hold Upto": "N/A",
        "Sub Date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    try:
        # Insert the report into the collection
        result = QuickReportViewCollection.insert_one(new_report)

        # Add another update operation to a different collection
        log_entry = {
            "action_title": "Form Submission",
            "category": "Report Form",
            "Sub-category": "Incident",
            "user_name": hn.get_username(),
            "action": f"New incident report added for {client_name}.",
            "date_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "collection_name": QuickReportViewCollection.full_name, 
            "collection_id":str(result.inserted_id),
            "action_name":"report Initiated",
            "html_file_source": "initiated_reports_view_auditor_view.html",
        }
        Log_table.insert_one(log_entry)  # LogsCollection represents the other MongoDB collection
        
        # Return the inserted report as JSON
        new_report["_id"] = str(result.inserted_id)  # Add the _id for reference
        return jsonify(new_report), 201  # Return the inserted report data as a response

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ignore_report/<report_id>', methods=['POST'])
def ignore_report(report_id):
    try:
        report_object_id = ObjectId(report_id)  # Validate the ObjectId
    except Exception as e:
        return jsonify({"error": "Invalid report ID."}), 400

    # Fetch user information
    loginid = lm.get_user_info()[0]  

    # Fetch the report details
    report = QuickReportViewCollection.find_one({"_id": report_object_id})

    # Check if the logged-in user is the initiator of the report
    initiator_id = report.get("Initiator ID", "").strip()

    if loginid.strip().lower() != initiator_id.lower():
        return jsonify({"error": "Only the initiator can ignore the report."}), 403

    # Fetch the user's PC profile and PC title
    pc_name = None
    pc_title = None
    pc_profile = PC_profile.find_one({"Assigned User ID": loginid})

    # If the profile exists and contains the 'PC Name'
    if pc_profile and 'PC Name' in pc_profile:
        pc_name = pc_profile['PC Name']
        pc_profile_table = PCProfileTable.find_one({"pc_name": pc_name})

        # Extract the pc_title if available
        if pc_profile_table and 'pc_title' in pc_profile_table:
            pc_title = pc_profile_table['pc_title']

    # Check if the report's PC Title matches the user's PC Title
    report_pc_title = report.get("PC Name")

    if report_pc_title and report_pc_title != pc_title:
        return jsonify({"error": "Only the initiator with the matching PC Title can ignore the report."}), 403

    # Check if another user has already ignored a report with the same PC Name
    conflicting_report = QuickReportViewCollection.find_one({
        "PC Title": pc_title,
        "Initiator ID": {"$ne": loginid},
        "Status": "Ignored"
    })

    if conflicting_report:
        return jsonify({"error": "This PC Title has already been ignored by another user."}), 403

    # Get today's date in YYYY-MM-DD format
    today_date = datetime.now().strftime('%Y-%m-%d')

    # Count the number of reports ignored by this user today
    ignored_reports_count = QuickReportViewCollection.count_documents({
        "Status": "Ignored",
        "Initiator ID": loginid,
        "Ignored Date": today_date
    })

    # Enforce the maximum limit of 3 ignored reports per day
    if ignored_reports_count >= 3:
        return jsonify({"error": "Maximum of 3 ignored reports allowed per day."}), 403

    # Mark the report as "Ignored" and update additional fields
    result = QuickReportViewCollection.update_one(
        {"_id": report_object_id},
        {"$set": {
            "Status": "Ignored",
            "Initiator ID": loginid,
            "Ignored Date": today_date,
            "Status Date-Time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  
            "Status Creator": m.getfullname(hn.get_username()),
            "PC Name": pc_title,
            "CR Status": "Ignored"
        }}
    )

    if result.modified_count > 0:
        print("Report successfully updated to Ignored.")
        return jsonify({"success": "Report ignored successfully."}), 200
    else:
        print("Report not found or not updated.")
        return jsonify({"error": "Report not found."}), 404
    
@app.route('/initiated_report_reporter_view')
def initiated_report_reporter_view():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""
    menu_items = lm.get_loginid_menulist()

    # Fetch the user's PC profile and PC title
    pc_name = None
    pc_title = None
    pc_profile = PC_profile.find_one({"Assigned User ID": loginid})

    # If the profile exists and contains the 'PC Name'
    if pc_profile and 'PC Name' in pc_profile:
        pc_name = pc_profile['PC Name']
        pc_profile_table = PCProfileTable.find_one({"pc_name": pc_name})

        # Extract the pc_title if available
        if pc_profile_table and 'pc_title' in pc_profile_table:
            pc_title = pc_profile_table['pc_title']

    # Fetch reports for the reporter view, excluding the ones with status "cancelled"
    initiated_reports_reporter = list(QuickReportViewCollection.find(
        {
            "Status": {
                "$in": ["Initiated", "Re-initiated", "Modified", "Rechecked"],
                "$nin": ["cancelled", "Paused"]
            },
            "PC title": pc_title
        }
    ))

    # Count the number of reports with the status "Reported"
    reported_count = QuickReportViewCollection.count_documents({"Status": "Reported"})

    # Fetch cancellation reasons from the database and format as "Cancellation Title : Reason Parameter"
    cancellation_reasons = list(reasonofcancellationcollection.find({}, {'Cancellation Title': 1, 'Reason Parameter': 1}))
    formatted_cancellation_reasons = [
        f"{reason['Cancellation Title']} : {reason.get('Reason Parameter', '')}"
        for reason in cancellation_reasons
    ]

    # Convert ObjectId to string for frontend compatibility
    for report in initiated_reports_reporter:
        report['_id'] = str(report['_id'])

    return render_template(
        'initiated_reports_view_reporter_view.html',
        username=loginid,
        menu_list=menu_items,
        initiated_reports_reporter=initiated_reports_reporter,
        reported_count=reported_count,  # Pass reported count to frontend
        cancellation_reasons=formatted_cancellation_reasons  # Pass formatted cancellation reasons to template
    )

@app.route('/get_department_names', methods=['POST'])
def get_department_names():
    client_name = request.json.get('client_name')
    
    # Fetch department names and Department IDs for the specific client from the department collection
    departments = list(departmentcollection.find(
        {
            "Client Name": client_name, 
            "Status": "Active"
        }, 
        {"Department Name/Port Number": 1, "Department ID": 1, "_id": 0}  # Include Department ID
    ))

    # Format departments list to include Department Name and ID
    result = []
    for dept in departments:
        result.append({
            "Department Name/Port Number": dept["Department Name/Port Number"],
            "Department ID": dept.get("Department ID", "")  # Ensure Department ID is included
        })
    
    return jsonify(result)


@app.route('/get_incident_categories', methods=['POST'])
def get_incident_categories():
    client_name = request.json.get('client_name')
    
    # Fetch unique incident categories for the specific client
    incident_categories = list(incidentsentencescollection.find(
        {"Client Name": client_name},
        {"Incident Category": 1, "_id": 0}
    ).distinct("Incident Category"))
    
    return jsonify(incident_categories)

@app.route("/get_incident_categories_22", methods=["POST"])
def get_incident_categories_22():
    client_name = request.json.get('client_name')
    
    # Fetch selected_incidents for the specific client
    client = clientcollection.find_one(
        {"Client Name": client_name},
        {"selected_incidents": 1}
    )
    
    unique_incidents = set()
    if client and "selected_incidents" in client:
        unique_incidents.update(client["selected_incidents"])

    # Match incidents with Incident Sentences
    matching_categories = set()
    for incident in unique_incidents:
        matched_sentences = incidentsentencescollection.find(
            {"Incident Sentence": incident},
            {"Incident Category": 1}
        )
        for match in matched_sentences:
            matching_categories.add(match["Incident Category"])

    return jsonify(list(matching_categories))

@app.route('/get_camera_numbers', methods=['POST'])
def get_camera_numbers():
    department_name = request.json.get('department_name')
    
    # Fetch all active cameras for the department
    cameras = list(cameracollection.find(
        {"Department Name/Port Number": department_name, "Status": "Active"},
        {"Camera Number": 1, "Camera Name": 1, "_id": 0}
    ))
    
    # Format the response to match the MongoDB format
    formatted_cameras = []
    for camera in cameras:
        camera_number = camera.get("Camera Number", "")
        camera_name = camera.get("Camera Name", "")
        formatted_cameras.append({
            "Camera Number": camera_number,
            "Camera Name": camera_name,
            # This will create the format like "1:CV Line"
            "display_value": f"{camera_number}:{camera_name}"
        })
    
    return jsonify(formatted_cameras)

@app.route('/update_final_report_message', methods=['POST'])
def update_final_report_message():
    data = request.json
    report_id = data.get("report_id")
    final_report_message = data.get("final_report_message")
    view_or_not = data.get("view_or_not", "")  # Default to empty string if not provided

    if not report_id or final_report_message is None:
        return jsonify({"error": "Missing report_id or final_report_message"}), 400

    try:
        # Update the document in the collection
        result = QuickReportViewCollection.update_one(
            {"_id": ObjectId(report_id)},
            {"$set": {
                "Final Report Message": final_report_message,
                "View or Not": view_or_not
            }}
        )
        
        if result.modified_count == 0:
            return jsonify({"error": "No document was updated"}), 404
        
        return jsonify({"message": "Final Report Message and View status updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
'''@app.route('/update_modify', methods=['POST'])
def update_report_message():
    # Get the incoming JSON data
    data = request.json
    report_id = data.get('report_id')  # Report ID to identify the report
    department = data.get('department')  # New department (e.g., DVR 4)
    camera = data.get('camera')          # New camera (e.g., Cam 5)
    category = data.get('category')      # Category (not used in message)
    incident_date = data.get('incident_date')  # New incident date (e.g., "11 Jan 2025")
    incident_time = data.get('incident_time')  # New incident time (e.g., "2:12 PM")

    # Fetch the report from the database using the report_id
    report = QuickReportViewCollection.find_one({'_id': ObjectId(report_id)})
    
    if not report:
        return jsonify({"error": "Report not found"}), 404

    current_message = report.get("Final Report Statement", "")
    
    if not current_message:
        return jsonify({"error": "Final Report Message is empty"}), 400

    # Updated regex pattern for matching the message format
    regex_pattern = r"(DVR \d+):Cam (\d+):([^:]+):.*\*.*\* @ (.*) on (.*)"

    # Match the current message using the regex
    match = re.match(regex_pattern, current_message)

    if match:
        # Extract values from the current message
        old_department = match.group(1)  # e.g., DVR 2
        old_camera = match.group(2)      # e.g., Cam 5
        old_location = match.group(3)    # e.g., Factory Parking
        old_time = match.group(4)        # e.g., 2:12 PM
        old_date = match.group(5)        # e.g., 8 Jan 2025

        # Prepare the updated message
        updated_message = current_message.replace(old_department, f"DVR {department}")
        updated_message = updated_message.replace(old_camera, f"Cam {camera}")
        updated_message = updated_message.replace(old_date, incident_date)
        updated_message = updated_message.replace(old_time, incident_time)

        # Prepare the updated report object
        updated_report = {
            "Department Name": f"DVR {department}",
            "Camera Number": f"Cam {camera}",
            "Incident Date": incident_date,
            "Incident Time": incident_time,
            "Final Report Statement": updated_message,
            "Incident Category": category,
            "Status":"Modified"
        }

        # Update the document in MongoDB
        result = QuickReportViewCollection.update_one({'_id': ObjectId(report_id)}, {'$set': updated_report})

        # Check if the document was updated
        if result.matched_count == 0:
            return jsonify({"error": "No report was updated. Please check the report ID."}), 400

        return jsonify({"message": "Report updated successfully"}), 200
    else:
        return jsonify({"error": "Report message format is incorrect"}), 400'''


@app.route('/update_modify', methods=['POST'])
def update_modify():
    data = request.json
    report_id = data.get("report_id")
    department = data.get("department")
    camera = data.get("camera")
    report_message = data.get("report_message")
    category = data.get("category")
    incident_date = data.get("incident_date")
    incident_time = data.get("incident_time")

    if not report_id:
        return jsonify({"success": False, "error": "Missing report_id"}), 400

    try:
        # Update the fields in MongoDB
        result = QuickReportViewCollection.update_one(
            {"_id": ObjectId(report_id)},
            {
                "$set": {
                    "Department Name": department,
                    "camera_select": camera,
                    "Final Report Message": report_message,
                    "Incident Message": report_message,
                    "Incident Category": category,
                    "Incident Date": incident_date,
                    "Incident Time": incident_time,
                    "Status": "Modified"
                }
            }
        )

        if result.modified_count > 0:
            return jsonify({"success": True, "message": "Report modified successfully"}), 200
        else:
            return jsonify({"success": False, "error": "No document was modified"}), 404

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500



'''@app.route('/get_final_report_message/<string:report_id>', methods=['GET'])
def get_final_report_message(report_id):
    try:
        report = QuickReportViewCollection.find_one({"_id": ObjectId(report_id)}, {"Final Report Message": 1})
        if report:
            return jsonify({"final_report_message": report.get("Final Report Message", "")}), 200
        else:
            return jsonify({"error": "Report not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500'''

# Route to get Camera Status based on Client, Department, and Camera
@app.route('/get_camera_status', methods=['GET'])
def get_camera_status():
    # Extract query parameters
    client_name = request.args.get('client')
    department_name = request.args.get('department')
    camera_name = request.args.get('camera')


    if not client_name or not department_name or not camera_name:
        return jsonify({'error': 'Client, department, and camera are required.'}), 400

    # Extract camera number from camera_name (e.g., "1:Main Gate" -> "1")
    camera_number = camera_name.split(":")[0] if ":" in camera_name else camera_name

    print(f"extracted data: {client_name},{department_name} & {camera_name}")

    try:
        # Query MongoDB to find the matching record based on client, department, and camera number
        report = cameracollection.find_one({
            "Client Name": client_name,
            "Department Name/Port Number": department_name,
            "Camera Number": camera_number  # Assuming camera number field in the DB is 'camera_number'
        })
        camera_status = report['Camera Status']
        # If report is found, check for Camera Issue Statement
        if camera_status=="" or not camera_status:
            camera_status = 'Active'

        # Return the camera status
        return jsonify({'cameraIssueStatement': camera_status})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500
    
@app.route('/call_back_action/<report_id>', methods=['POST'])
def call_back_action(report_id):
    # Ensure the report exists by checking its _id
    report = QuickReportViewCollection.find_one({"_id": ObjectId(report_id)})

    if report:
        # Update the 'call back' field to "Yes"
        QuickReportViewCollection.update_one(
            {"_id": ObjectId(report_id)},
            {"$set": {"call back": "Yes"}}
        )
        return jsonify({"status": "success", "message": "Report marked as 'Call Back'", "report_id": report_id})
    else:
        return jsonify({"status": "error", "message": "Report not found"})
    
@app.route('/update_call_back/<report_id>', methods=['POST'])
def update_call_back(report_id):
    # Get the data from the request
    request_data = request.get_json()
    
    # Check if the 'call_back' field is present and set to "Yes"
    if 'call_back' not in request_data or request_data['call_back'] != 'Yes':
        return jsonify({"status": "error", "message": "Invalid request data"}), 400

    # Update the 'call_back' field for the specific report
    result = QuickReportViewCollection.update_one(
        {"_id": ObjectId(report_id)},  # Match the report by its _id
        {"$set": {"call back": "Yes"}}  # Set 'call back' to "Yes"
    )
    
    if result.modified_count > 0:
        return jsonify({"status": "success", "message": "Call back status updated successfully"})
    else:
        return jsonify({"status": "error", "message": "Failed to update call back status"}), 400
    
@app.route('/update_callback', methods=['POST'])
def update_callback():
    # Get the report ID from the request
    data = request.get_json()
    report_id = data.get('_id')

    if not report_id:
        return jsonify({'success': False, 'message': 'Invalid report ID'}), 400  # Return 400 error for missing ID

    try:
        # Convert the report ID to ObjectId
        report_id_obj = ObjectId(report_id)

        # Update the report with Status = "Re-initiated" and CallBack = "Yes"
        result = QuickReportViewCollection.update_one(
            {"_id": report_id_obj},
            {"$set": {"Status": "Re-initiated", "Call back": "Yes"}}
        )

        # Check if the update was successful
        if result.modified_count > 0:
            return jsonify({'success': True, 'message': 'Report updated successfully'})
        else:
            return jsonify({'success': False, 'message': 'No record found to update'}), 404

    except Exception as e:
        print(f"Error updating report: {e}")
        return jsonify({'success': False, 'message': 'Error updating the report'}), 500
    
@app.route('/rechecked_records', methods=['GET', 'POST'])
def rechecked_records():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()

    # Ensure login validation
    if check_login != loginid:
        loginid = ""
        
    menu_items = lm.get_loginid_menulist()

    # Collect filters from URL parameters (default to None if not provided)
    _id_filter = request.args.get('_id')
    client_name_filter = request.args.get('client_name')
    status_filter = "Requested to Recheck"  # Hardcoded to filter only "Requested to Recheck" status

    # Combine all filters in one dictionary
    query_filter = {
        "Status": status_filter,  # Only show records with this specific status
        **({"_id": ObjectId(_id_filter)} if _id_filter else {}),
        **({"Client Name": client_name_filter} if client_name_filter else {})
    }

    # Fetch reports from the collection with the combined filter
    rechecked_reports = list(QuickReportViewCollection.find(query_filter))

    # Fetch distinct Cancellation Titles and Reason Parameters from Reason For Cancellation collection
    reason_options = []
    cancellation_reasons = reasonofcancellationcollection.distinct("Cancellation Title")  # Get distinct Cancellation Titles

    # Fetch the Reason Parameter for each distinct Cancellation Title
    for title in cancellation_reasons:
        reason_param = reasonofcancellationcollection.find_one({"Cancellation Title": title})
        if reason_param:
            reason_option = f"{title} : {reason_param.get('Reason Parameter', 'N/A')}"
            reason_options.append(reason_option)

    # Initialize data list
    data = []

    # Process the report data
    if rechecked_reports:
        for report in rechecked_reports:
            # Extract fields and process them as needed
            camera_name = report.get("Camera Number", "N/A").split(":", 1)[1].strip() if ":" in report.get("Camera Number", "N/A") else "N/A"
            final_report_statement = report.get("Incident Message", "N/A")
            
            # Append the data
            data.append({
                "Client Name": report.get("Client Name", "N/A"),
                "Department Name": report.get("Department Name", "N/A"),
                "Camera Name": camera_name,  # Get camera name after ":"
                "Final Report Statement": final_report_statement,  # Get incident message as final report statement
                "Incident Category": report.get("Incident Category", "N/A"),
                "_id": str(report.get("_id", "N/A")),  # Add _id as a string
                "wrong_reasons": reason_options  # Pass the fetched reason options for the dropdown
            })
    else:
        flash("No records found with the applied filters", "info")

# Handle POST request for accept action (?)
    if request.method == 'POST':
        try:
            data = request.json
            action = data.get('action')  # Get action from the request body
            _id = data.get('_id')  # Get _id from the request body
            wrong_reason = data.get('wrong_reason')

            # Ensure that _id exists and is valid
            if _id:
                # Ensure _id is in the correct format as ObjectId
                try:
                    # Convert the _id to ObjectId if it's a string
                    object_id = ObjectId(_id) if isinstance(_id, str) else None
                    if not object_id:
                        return jsonify({"error": "Invalid _id format"}), 400

                    # Fetch the report from the database
                    report = QuickReportViewCollection.find_one({"_id": object_id})
                    if not report:
                        return jsonify({"error": "No report found with the given _id"}), 404
                    else:
                        if action == 'accept':
                            # Update the status to 'Rechecked' with current timestamp and creator
                            QuickReportViewCollection.update_one(
                                {"_id": object_id},
                                {
                                    "$set": {
                                        "Status": "Rechecked",  # Update status to 'Rechecked'
                                        "Rechecking Status DT": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                        "Rechecking Status Creator": m.getfullname(hn.get_username())  # Add Rechecking Status Creator
                                    }
                                }
                            ) 
                        
                        elif action == 'reject':
                            # Update the status to 'Rechecked' with current timestamp and creator
                            QuickReportViewCollection.update_one(
                                {"_id": object_id},
                                {
                                    "$set": {
                                        "Status": "Declined",  # Update status to 'Rechecked'
                                        "Rechecking Status DT": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                        "Rechecking Status Creator": m.getfullname(hn.get_username()),
                                        "Declining Reason": wrong_reason  # Add Rechecking Status Creator
                                    }
                                }
                            ) 

                            return jsonify({"message": f"Report {str(_id)} marked as Rechecked"}), 200
                        else:
                            return jsonify({"error": "Invalid action"}), 400
                except Exception as e:
                    return jsonify({"error": f"An error occurred while processing the request: {e}"}), 500
            else:
                return jsonify({"error": "Missing _id"}), 400
        except Exception as e:
            return jsonify({"error": f"An error occurred: {e}"}), 500

    # Render the template with the data
    return render_template(
        'rechecked_records_leader_view.html',
        data=data,
        username=loginid,
        menu_list=menu_items,
        client_name_filter=client_name_filter,
        _id_filter=_id_filter
    )

@app.route('/update_view_or_not', methods=['POST'])
def update_view_or_not():
    data = request.json
    report_id = data.get("report_id")
    view_or_not = data.get("view_or_not")
    final_report_message = data.get("final_report_message")

    if not report_id or view_or_not is None or final_report_message is None:
        return jsonify({"error": "Missing report_id, view_or_not, or final_report_message"}), 400

    try:
        # Update the document in the MongoDB collection
        QuickReportViewCollection.update_one(
            {"_id": ObjectId(report_id)},
            {"$set": {
                "View or Not": view_or_not,
                "Final Report Message": final_report_message
            }}
        )
        return jsonify({"message": "View or Not and Final Report Message updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/cancel_report', methods=['POST'])
def cancel_report():
    try:
        # Get data from the submitted form
        report_id = request.form.get('report_id')  # ID of the report to cancel
        cancel_reason = request.form.get('cancel_reason')  # Reason for cancellation
        explain_sa = request.form.get('explain_sa')  # Explanation flag (optional)

        # Convert 'explain_sa' to a boolean
        explain_sa_flag = True if explain_sa == 'on' else False

        # Validate report ID
        if not report_id:
            return jsonify({"success": False, "message": "Report ID is required."}), 400

        # Update the document in MongoDB
        result = QuickReportViewCollection.update_one(
            {"_id": ObjectId(report_id)},
            {
                "$set": {
                    "Status": "cancelled",
                    "Cancellation Reason": cancel_reason,
                    "Explain SA": explain_sa_flag,
                    "Call back": "No",
                    "Status Date-Time":datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "Status Changer Name": m.getfullname(hn.get_username())
                }
            }
        )

        if result.matched_count == 0:
            return jsonify({"success": False, "message": "Report not found."}), 404

        return jsonify({"success": True, "message": "Report status updated to 'cancelled'."})

    except Exception as e:
        return jsonify({"success": False, "message": f"An error occurred: {str(e)}"}), 500
    
@app.route('/recheck_report', methods=['POST'])
def recheck_report():
    try:
        # Get data from the submitted form
        report_id = request.form.get('report_id')  # ID of the report to cancel
        recheck_reason = request.form.get('recheck_reason')  # Reason for cancellation
        comments = request.form.get('comments')  # Explanation flag (optional)
        print(f'id is:{report_id}')
        # Validate report ID
        if not report_id:
            return jsonify({"success": False, "message": "Report ID is required."}), 400

        # Update the document in MongoDB
        result = QuickReportViewCollection.update_one(
            {"_id": ObjectId(report_id)},
            {
                "$set": {
                    "Status": "Requested to Recheck",
                    "Rechecking Reason": recheck_reason,
                    "Rechecking Comment": comments,
                    "Status Date-Time":datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "Status Changer Name": m.getfullname(hn.get_username())
                }
            }
        )

        if result.matched_count == 0:
            return jsonify({"success": False, "message": "Report not found."}), 404

        return jsonify({"success": True, "message": "Report status updated to 'cancelled'."})

    except Exception as e:
        return jsonify({"success": False, "message": f"An error occurred: {str(e)}"}), 500
    
# Route to fetch statements based on keyword search
@app.route('/get_sentences_for_camera_issue', methods=['GET'])
def get_sentences_for_camera_issue():
    search_query = request.args.get('word', '').strip()
    
    if not search_query:
        return jsonify([])

    # Use regex for case-insensitive search
    regex = re.compile(f".*{re.escape(search_query)}.*", re.IGNORECASE)
    results = CamIssueCollection.find({"camera_issue_statement": regex})  # Limit to 10 results
    
    sentences = [result['camera_issue_statement'] for result in results]

    return jsonify(sentences)

# Route to autocorrect the selected statement
@app.route('/autocorrect_sentence_for_camera_issue', methods=['POST'])
def autocorrect_sentence_for_camera_issue():
    data = request.get_json()
    
    if 'sentence' not in data:
        return jsonify({"error": "No sentence provided"}), 400

    sentence = data['sentence']  # Corrected the key

    # Apply grammar correction using AI model
    #corrected_sentence = grammar_corrector(f"correct grammar: {sentence}")[0]['generated_text']
    
    return jsonify({"corrected_sentence": sentence})

@app.route('/incident_to_client_linking', methods=['GET', 'POST'])
def incident_to_client_linking():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()

    # Ensure login validation
    if check_login != loginid:
        loginid = ""
    
    menu_items = lm.get_loginid_menulist()

    # Get distinct client names from the collection
    clients = clientcollection.distinct('Client Name')

    # Get all incident sentences (distinct)
    incidents = list(incidentsentencescollection.distinct('Incident Sentence'))  # Fetch incidents from the Incident Sentences Profile collection
    
    # If a client is selected via POST request, get the corresponding client ID
    client_id = None
    selected_incidents = []
    if request.method == 'POST':
        selected_client = request.form.get('client')
        if selected_client:
            # Fetch the Client ID from the collection
            client_data = clientcollection.find_one({'Client Name': selected_client})
            if client_data:
                client_id = client_data.get('Client ID')
                selected_incidents = client_data.get('selected_incidents', [])

    return render_template('incident_messages_transfer_tables.html', 
                           clients=clients, 
                           incidents=incidents, 
                           client_id=client_id, 
                           selected_incidents=selected_incidents,  # Pass selected incidents for filtering
                           username=loginid, 
                           menu_list=menu_items)



# Fetch Client ID
@app.route('/get_client_id', methods=['GET'])
def get_client_id():
    client_name = request.args.get('client_name')
    if client_name:
        client_data = clientcollection.find_one({'Client Name': client_name})
        if client_data:
            return jsonify({'client_id': client_data.get('Client ID')})
    
    return jsonify({'error': 'Client not found'}), 404

# Fetch Not Selected Incidents
@app.route('/get_not_selected_incidents', methods=['GET'])
def get_not_selected_incidents():
    client_name = request.args.get('client_name')
    
    if not client_name:
        return jsonify({"error": "Client name is required"}), 400
    
    incidents = list(incidentsentencescollection.distinct('Incident Sentence'))
    
    client_data = clientcollection.find_one({"Client Name": client_name})
    if not client_data:
        return jsonify({"error": "Client not found"}), 404
    
    selected_incidents = client_data.get('selected_incidents', [])

    if not selected_incidents:
        return jsonify(incidents)

    not_selected_incidents = [incident for incident in incidents if incident not in selected_incidents]

    return jsonify(not_selected_incidents)

# Update Selected Incidents (Add or Remove)
@app.route('/update_selected_incidents', methods=['POST'])
def update_selected_incidents():
    data = request.get_json()
    client_name = data.get('client_name')
    selected_incidents = data.get('selected_incidents', [])
    action = data.get('action')  # "add" or "remove"

    if not client_name or not selected_incidents:
        return jsonify({"error": "Client name and incidents are required"}), 400

    client_data = clientcollection.find_one({"Client Name": client_name})
    if not client_data:
        return jsonify({"error": "Client not found"}), 404

    updated_selected_incidents = client_data.get('selected_incidents', [])

    if action == "add":
        updated_selected_incidents.extend([inc for inc in selected_incidents if inc not in updated_selected_incidents])
    elif action == "remove":
        updated_selected_incidents = [inc for inc in updated_selected_incidents if inc not in selected_incidents]

    clientcollection.update_one(
        {"Client Name": client_name},
        {"$set": {"selected_incidents": updated_selected_incidents}}
    )

    return jsonify({"success": True, "updated_selected_incidents": updated_selected_incidents})
    
# Fetch Client Data for Incidents
@app.route('/get_client_data_for_incidents', methods=['GET'])
def get_client_data_for_incidents():
    client_name = request.args.get('client_name')

    if not client_name:
        return jsonify({"error": "Client name required"}), 400

    client_data = clientcollection.find_one({"Client Name": client_name})

    if not client_data:
        return jsonify({"error": "Client not found"}), 404

    return jsonify({"client_id": client_data.get("Client ID")})

# Fetch Incidents for a Selected Client
@app.route('/get_incident_data', methods=['GET'])
def get_incident_data():
    client_name = request.args.get('client_name')
    client_id = request.args.get('client_id')

    if not client_name or not client_id:
        return jsonify({"error": "Client name and ID are required"}), 400

    client_data = clientcollection.find_one({"Client Name": client_name, "Client ID": client_id})
    if not client_data:
        return jsonify({"error": "Client not found"}), 404

    selected_incidents = client_data.get('selected_incidents', [])

    all_incidents = list(incidentsentencescollection.distinct('Incident Sentence'))
    valid_selected_incidents = [inc for inc in selected_incidents if inc in all_incidents]
    not_selected_incidents = [inc for inc in all_incidents if inc not in valid_selected_incidents]

    return jsonify({
        "selected_incidents": valid_selected_incidents,
        "not_selected_incidents": not_selected_incidents
    })

''' # Route to fetch Not Selected Incidents based on keyword search
@app.route('/search_not_selected_incidents', methods=['GET'])
def search_not_selected_incidents():
    client_name = request.args.get('client_name', '').strip()
    search_query = request.args.get('word', '').strip()

    if not client_name or not search_query:
        return jsonify([])

    # Use regex for case-insensitive search
    regex = re.compile(f".*{re.escape(search_query)}.*", re.IGNORECASE)

    # Fetch the client's selected incidents
    client_data = clientcollection.find_one({"Client Name": client_name})
    selected_incidents = client_data.get('selected_incidents', []) if client_data else []

    # Fetch all incidents from the collection
    all_incidents = list(incidentsentencescollection.distinct('Incident Sentence'))

    # Filter out selected incidents & apply search filter
    filtered_incidents = [incident for incident in all_incidents if incident not in selected_incidents and regex.match(incident)]

    return jsonify(filtered_incidents)


# Route to fetch Selected Incidents based on keyword search
@app.route('/search_selected_incidents', methods=['GET'])
def search_selected_incidents():
    client_name = request.args.get('client_name', '').strip()
    search_query = request.args.get('word', '').strip()

    if not client_name or not search_query:
        return jsonify([])

    # Use regex for case-insensitive search
    regex = re.compile(f".*{re.escape(search_query)}.*", re.IGNORECASE)

    # Fetch the client's selected incidents
    client_data = clientcollection.find_one({"Client Name": client_name})
    selected_incidents = client_data.get('selected_incidents', []) if client_data else []

    # Apply search filter to selected incidents
    filtered_incidents = [incident for incident in selected_incidents if regex.match(incident)]

    return jsonify(filtered_incidents) '''

@app.route('/incident_category', methods=['GET', 'POST'])
def form_incident_category():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()

    # Ensure login validation
    if check_login != loginid:
        loginid = ""

    menu_items = lm.get_loginid_menulist()

    if request.method == 'POST':
        category_name = request.form.get('category_name')
        short_form = request.form.get('short_form')

        # If "Other" is selected, get the user input for a new category
        if category_name == "Other":
            category_name = request.form.get('new_category_name')

        # Validation
        if not category_name or not short_form:
            flash("All fields are required!", "error")
            return redirect(url_for('form_incident_category'))

        # Save to MongoDB if it does not already exist
        if not incidentcategoriesdetails.find_one({"Category Name": category_name}):
            incidentcategoriesdetails.insert_one({
                "Category Name": category_name,
                "Short Form": short_form
            })

        flash("Incident Category successfully created!", "success")
        return redirect(url_for('report.form_incident_category'))

    # Fetch distinct category names from MongoDB
    category_names = incidentcategoriesdetails.distinct("Category Name")

    return render_template(
        'incident_category_details.html',
        username=loginid,
        menu_list=menu_items,
        category_names=category_names
    )

@app.route('/incident_category_parameters', methods=['GET', 'POST'])
def form_incident_category_parameters():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()

    # Ensure login validation
    if check_login != loginid:
        loginid = ""

    menu_items = lm.get_loginid_menulist()

    if request.method == 'POST':
        category_short_form = request.form.get('category_short_form')
        parameter = request.form.get('parameter')

        # Validation
        if not category_short_form or not parameter:
            flash("All fields are required!", "error")
            return redirect(url_for('form_incident_category_parameters'))

        # Check if category exists in the database
        existing_category = incidentcategoriesdetails.find_one({"Short Form": category_short_form})

        if existing_category:
            # Prevent duplicate parameter addition by checking if the parameter exists
            if parameter in existing_category.get("Parameters", []):
                flash("Parameter already exists for this category!", "warning")
            else:
                # Append new parameter to the existing array using $push
                incidentcategoriesdetails.update_one(
                    {"Short Form": category_short_form},
                    {"$push": {"Parameters": parameter}}
                )
                flash("Parameter added successfully!", "success")
        else:
            # If category does not exist, create a new document with the Category and Parameters array
            incidentcategoriesdetails.insert_one({
                "Short Form": category_short_form,
                "Parameters": [parameter]
            })
            flash("New category created with parameter!", "success")

        return redirect(url_for('report.form_incident_category_parameters'))

    # Fetch distinct short forms from MongoDB
    category_short_forms = incidentcategoriesdetails.distinct("Short Form")

    return render_template(
        'incident_category_parameters.html',
        username=loginid,
        menu_list=menu_items,
        category_short_forms=category_short_forms
    )

@app.route('/get_sentences_for_report_form', methods=['GET'])
def get_sentences_for_report_form():
    words = request.args.get('word', '').split()  # Splitting the search terms
    client_name = request.args.get('client', '')  # Getting client name from query parameters

    if not words or not client_name:
        return jsonify([])

    # Build a list of regex queries for each word in 'words'
    regex_queries = [{"selected_incidents": {"$regex": f".*{re.escape(word)}.*", "$options": "i"}} for word in words]

    # Add the client name filter
    regex_queries.append({"Client Name": client_name})

    # Find documents based on the built query
    results = clientcollection.find({"$and": regex_queries})

    # Collect matched sentences
    matched_sentences = []

    for result in results:
        # Filter the sentences from 'selected_incidents' array that match the regex queries
        matched = [
            sentence for sentence in result['selected_incidents']
            if any(re.search(f".*{re.escape(word)}.*", sentence, re.IGNORECASE) for word in words)
        ]
        if matched:
            matched_sentences.extend(matched)

    return jsonify(matched_sentences)

@app.route('/get_incident_categories_for_report_form', methods=['GET'])
def get_incident_categories_for_report_form():
    sentence = request.args.get('sentence')
    print(f"sentence is: {sentence}")

    if not sentence:
        return jsonify({"error": "No sentence provided"}), 400

    # Fetch the document
    result = incidentsentencescollection.find_one(
        {"Incident Sentence": sentence
    })
    print(f"Query result: {result}")  # Debugging print
    print(result.get("Incident Category"))
    if result:
        # Return the corresponding Incident Category
        return jsonify({"incidentCategory": result.get("Incident Category")})
    else:
        return jsonify({"incidentCategory": "Not Found"})
    
'''@app.route('/get_incident_category', methods=['GET'])
def get_incident_category():
    sentence = request.args.get('sentence', '')
    print(f"Sentences is : {sentence}")

    if not sentence:
        return jsonify({"error": "No sentence provided"}), 400

    # Query the `incidentSentencesCollection` to find the matching sentence
    result = incidentsentencescollection.find_one({
        "Incident Sentence": sentence
    })
    print(f"Result is : {result}")
    if result:
        # Return the corresponding Incident Category
        return jsonify({"incidentCategory": result.get("Incident Category", "Not Found")})
    else:
        return jsonify({"incidentCategory": "Not Found"})'''

'''@app.route('/get_incident_category', methods=['GET'])
def get_incident_category():
    sentence = request.args.get('sentence', '')

    if not sentence:
        return jsonify({"error": "No sentence provided"}), 400

    # Query the `incidentSentencesCollection` to find the matching sentence
    result = incidentsentencescollection.find_one({
        "Incident Sentence": sentence
    })
    
    if result:
        # Return the corresponding Incident Category
        return jsonify({"incidentCategory": result.get("Incident Category", "Not Found")})
    else:
        return jsonify({"incidentCategory": "Not Found"})'''

@app.route('/get_incident_categories_2', methods=['GET'])
def get_incident_categories_2():
    categories = incidentsentencescollection.distinct("Incident Category")  # Fetch distinct categories
    return jsonify(categories)  # Return as JSON response

# Function to check file extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Form to upload the report
@app.route('/upload_report', methods=['GET', 'POST'])
def upload_report():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""

    menu_items = lm.get_loginid_menulist()

    # Fetch PC profile based on loginid
    pc_title = None
    if loginid:
        pc_profile = PC_profile.find_one({"Assigned User ID": loginid})

        # If the profile exists and contains the 'PC Name'
        if pc_profile and 'PC Name' in pc_profile:
            pc_name = pc_profile['PC Name']
            pc_profile_table = PCProfileTable.find_one({"pc_name": pc_name})

            # Extract the pc_title if available
            if pc_profile_table and 'pc_title' in pc_profile_table:
                pc_title = pc_profile_table['pc_title']
    
    if pc_title:
        # Assuming the `Client_Department_Link` collection has a field `pc_title` to match against
        clients = clientDeptLink.find({"pc_title": pc_title}).distinct('client_registration_number')

    if request.method == 'POST':
        client_name = request.form['client_name']
        file = request.files['file']
        
        # Ensure the file is valid
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            client_folder = os.path.join(UPLOAD_FOLDER, client_name)

            # Create the client folder if it doesn't exist
            if not os.path.exists(client_folder):
                os.makedirs(client_folder)

            # Save the file to the client's folder
            file.save(os.path.join(client_folder, filename))
            return redirect(url_for('report.view_reports', client_name=client_name))

    # Handle GET request to return client_folder as JSON for checking
    if request.method == 'GET':
        client_name = request.args.get('client_name')
        
        if client_name:
            # Check if the folder exists for the selected client
            client_folder = os.path.join(UPLOAD_FOLDER, client_name)
            if os.path.exists(client_folder):
                return jsonify({"client_folder": client_name})
            else:
                return jsonify({"client_folder": None})

    return render_template('pdf_rules_linking.html', 
                           username=loginid, 
                           menu_list=menu_items, 
                           clients=clients)

# View reports based on selected client
@app.route('/view_reports/<client_name>', methods=['GET'])
def view_reports(client_name):
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""

    menu_items = lm.get_loginid_menulist()

    client_folder = os.path.join(UPLOAD_FOLDER, client_name)
    files = []
    folder_exists = os.path.exists(client_folder)  # Check if the folder exists for the selected client
    
    if folder_exists:
        files = os.listdir(client_folder)
    
    return render_template('view_reports.html', 
                           client_name=client_name, 
                           files=files, 
                           username=loginid, 
                           menu_list=menu_items,
                           folder_exists=folder_exists)  # Pass the folder existence status

@app.route('/download/<client_name>/<filename>')
def download_file(client_name, filename):
    file_path = os.path.join(UPLOAD_FOLDER, client_name, filename)
    return send_from_directory(directory=os.path.dirname(file_path), filename=filename)

@app.route('/get_client_id_2', methods=['GET'])
def get_client_id_2():
    client_name = request.args.get('client_name')
    print(f"Fetching client ID for: {client_name}")  # Debugging log
    client = clientDeptLink.find_one({"client_registration_number": client_name})
    
    if client:
        client_id = client.get('client_id')  # Ensure this matches your actual field name in MongoDB
        return {'client_id': client_id}
    else:
        return {'client_id': None}  # If no matching client is found
    
@app.route('/view_pdf/<client_name>')
def view_pdf(client_name):
    # Check the client folder
    client_folder = os.path.join(UPLOAD_FOLDER, client_name)

    # Get the PDF file from the folder (assuming there is only one file or you know the filename)
    pdf_file = None
    for filename in os.listdir(client_folder):
        if filename.endswith('.pdf'):
            pdf_file = filename
            break  # assuming only one PDF file per client

    # If a PDF file exists, return it to be viewed in the browser
    if pdf_file:
        return send_from_directory(client_folder, pdf_file)
    else:
        return "No PDF file found for this client", 404
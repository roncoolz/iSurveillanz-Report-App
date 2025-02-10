from flask import Flask, request, render_template, flash, redirect, url_for,make_response, jsonify, session, Blueprint
from datetime import datetime
import re
import os
from bson.objectid import ObjectId
from gridfs import GridFS
import io
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app_settings')))
from App_Setting import FieldCollection, ClientGroupProfile, clientcollection, clientdisplaycollection, departmentcollection, cameracollection, db_FusionBizCentral, Log_table
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Client_Profile')))
import methods.employee_profile.get_para_from_officialid as m
import methods.common_functions.loginid_menulist as lm
import socket
import methods.common_functions.common_function as hn
import random
import string
from bson.objectid import ObjectId

# Initialize the Flask app
app = Blueprint('client_profile', __name__)

# Define a custom Jinja2 filter
'''@app.template_filter('format_datetime')
def format_datetime(value):
    # Example: Format the datetime to a specific string format
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    return value  # Return as is if not a datetime object'''

'''@app.route('/')
def index():
    loginid,portal_user_title = lm.get_user_info()
    check_login=hn.get_username()
    print(loginid)
    print(check_login)
    if check_login != loginid:
        loginid=""

    menu_items = lm.get_loginid_menulist()
    return render_template('form_field_profile.html', username=loginid, menu_list=menu_items)'''

@app.route('/form_field_profile', methods=['GET', 'POST'])
def form_field_profile():
    loginid,portal_user_title = lm.get_user_info()
    check_login=hn.get_username()
    print(loginid)
    print(check_login)
    if check_login != loginid:
        loginid=""

    menu_items = lm.get_loginid_menulist()
    if request.method == 'POST':
        field_name = request.form.get("field_name")
        short_name = request.form.get("short_name").upper()
        
        # Validate field_name
        if not field_name:
            flash('Field Name is required.', 'error')
            return redirect(url_for('form_field_profile'))

        # Validate short_name
        if not short_name:
            flash('Short Name is required.', 'error')
            return redirect(url_for('form_field_profile'))
        
         # Ensure short_name is exactly 3 letters
        if not re.match(r'^[A-Z]{3}$', short_name):
            flash('Short Name must be exactly 3 uppercase letters.', 'error')
            return redirect(url_for('client_profile.form_field_profile'))
        
        # Check for duplicate field_name
        if FieldCollection.find_one({"Field Name": field_name}):
            flash(f"Field Name '{field_name}' already exists.", 'error')
            return redirect(url_for('client_profile.form_field_profile'))
        
        # Check for duplicate short_name
        if FieldCollection.find_one({"Short Name": short_name}):
            flash(f"Short Name '{short_name}' already exists.", 'error')
            return redirect(url_for('form_field_profile'))

        # Validate field_name (e.g., it should be alphanumeric and without spaces)
        if not re.match(r'^[a-zA-Z0-9_]+$', field_name):
            flash('Field Name should be alphanumeric and without spaces.', 'error')
            return redirect(url_for('form_field_profile'))

        # Validate short_name (e.g., only letters or numbers allowed)
        if not re.match(r'^[a-zA-Z0-9]+$', short_name):
            flash('Short Name should be alphanumeric and without special characters or spaces.', 'error')
            return redirect(url_for('form_field_profile'))
        
        field_id = short_name  # You can adjust length as needed
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M')
        
        # Construct the field profile document
        field_profile = {
            "Field ID" : field_id,
            "Field Name": field_name,
            "Short Name": short_name,
            "Status": "Active",
            "Status Date-Time": formatted_datetime,
            "Status Creator Name": m.getfullname(hn.get_username()),
        }

        # Insert the new field profile into MongoDB
        FieldCollection.insert_one(field_profile)

        # Log the action
        log_entry_new_field_profile = {
            "action_title": "Form Submission",
            "category": "Client Profile",
            "user_name": m.getfullname(hn.get_username()),
            "action": f"Field profile '{field_name}' with short name '{short_name}' created.",
            "date_time": datetime.now(),
            "collection_name": FieldCollection.full_name,
            "collection_id": field_profile["_id"],
            "html_file_source": "form_field_profile.html"
        }
        Log_table.insert_one(log_entry_new_field_profile)

        flash('Field profile created successfully!', 'success')
        return redirect(url_for('client_profile.table_field_profiles'))

    return render_template('form_field_profile.html', username=loginid, menu_list=menu_items)


'''@app.route('/log_table', methods=['GET'])
def log_table():
    # Retrieve all logs
    logs = list(logs_collection.find().sort('date_time', -1))  # Sort by date_time descending
    return render_template('log_table.html', logs=logs)'''


@app.route('/table_field_profiles', methods=['GET'])
def table_field_profiles():
    loginid,portal_user_title = lm.get_user_info()
    check_login=hn.get_username()
    if check_login != loginid:
        loginid=""
    # Retrieve all field profiles
    field_profiles = list(FieldCollection.find().sort('_id',-1))
    menu_items = lm.get_loginid_menulist()
    return render_template('table_field_profiles.html', field_profiles=field_profiles, username=loginid,menu_list=menu_items)


@app.route('/image/<image_id>')
def serve_image(image_id):
    fs = GridFS(db_FusionBizCentral)
    file = fs.get(ObjectId(image_id))
    response = make_response(file.read())
    response.mimetype = file.content_type
    return response

@app.route('/add_group_name', methods=['POST'])
def add_group_name():
    group_name = request.form.get('group_name')
    field_id = request.form.get('field_id')
    field_name = request.form.get('field_name')
    logo = request.files.get('logo')

    # Ensure the necessary fields are provided
    if not group_name:
        flash('The Group Name is required.', 'error')
        return redirect(url_for('table_field_profiles'))

    # Use GridFS for image storage
    fs = GridFS(db_FusionBizCentral)

    # Save the image in GridFS
    logo_id = fs.put(logo.stream, filename=f"{group_name}_{logo.filename}", content_type=logo.content_type)

    # Find the current field profile
    field_profile = ClientGroupProfile.find_one({"Field ID": field_id, "Group Name": group_name})

    # Check if the field profile exists and if the group_name already exists
    if field_profile:
        # Get existing group_name or initialize as an empty list
        existing_group_names = field_profile.get('Group Name', [])

        # Check if the group_name already exists in the field_profile
        if group_name in existing_group_names:
            flash(f"Group Name '{group_name}' already exists for this field.", 'error')
            return redirect(url_for('client_profile.table_field_profiles'))

    # Generate unique group_id as field_id + random suffix
    while True:
        random_suffix = f"{random.randint(1, 9)}{random.choice(string.ascii_uppercase)}"
        group_id = f"{field_id}{random_suffix}"
        # Ensure uniqueness in the ClientGroupProfile collection for this field_id
        if not ClientGroupProfile.find_one({"Field ID": field_id, "Group ID": group_id}):
            break

    # Prepare additional fields
    current_datetime = datetime.now()
    formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M')

    # Insert into ClientGroupProfile collection
    ClientGroupProfile.insert_one({
        "Field ID": field_id,
        "Field Name": field_name,
        "Group ID": group_id,
        "Group Name": group_name,
        "Logo File ID": logo_id,  # Reference to the image stored in GridFS
        "Created On": formatted_datetime,  
        "Status": "Active",  
        "Status Date-Time": formatted_datetime,  
        "Status Creator Name": m.getfullname(hn.get_username()),  
    })

    # Log the action
    log_entry_new_client_group = {
        "action_title": "Form Submission",
        "category": "Client Profile",
        "user_name": m.getfullname(hn.get_username()),
        "action": f"Group name {group_name} added for the field {field_name}",
        "date_time": datetime.now(),
        "collection_name": ClientGroupProfile.full_name,
        "html_file_source": "table_group_profile.html"
    }
    Log_table.insert_one(log_entry_new_client_group)
    
    flash('Group name and Logo added successfully!', 'success')
    return redirect(url_for('client_profile.table_group_profile'))

@app.route('/table_group_profile', methods=['GET'])
def table_group_profile():
    loginid,portal_user_title = lm.get_user_info()
    check_login=hn.get_username()
    if check_login != loginid:
        loginid=""
    group_profiles = list(ClientGroupProfile.find().sort('Group ID', -1))
    menu_items = lm.get_loginid_menulist()
    return render_template('table_group_profile.html', group_profiles=group_profiles, username=loginid,menu_list=menu_items)


@app.route('/register_client', methods=['POST'])
def register_client():
    try:
        # Retrieve form data
        group_id = request.form.get('group_id')
        field_name = request.form.get('field_name')
        group_name = request.form.get('group_name')
        client_registration_name = request.form.get('client_registration_name')
        reference = request.form.get('reference')
        gst_number = request.form.get('gst_number')
        client_requirements = request.form.get('client_requirements')
        client_name = request.form.get('client_name')
        connecting_date = request.form.get('connecting_date')
        contact_name = request.form.get('contact_name')
        contact_mobile = request.form.get('contact_mobile')
        contact_email = request.form.get('contact_email')

        if clientcollection.find_one({"Client Registration Name": client_registration_name}):
            flash("Client Registration Name already exists.", "error")
            return redirect(url_for('client_profile.table_client_profile'))
        
        if clientcollection.find_one({"Client Name": client_name}):
            flash("Client Name already exists.", "error")
            return redirect(url_for('client_profile.table_client_profile'))


        # Find the existing clients for this group_id
        existing_clients = list(clientcollection.find({
            "Group ID": group_id,
            "Group Name": group_name,
        }).sort("Client ID", 1))

        if existing_clients:
            # Get the last client ID and determine the next letter
            last_client_id = existing_clients[-1]["Client ID"]
            last_suffix = last_client_id.split(group_id)[-1] 

            # If the suffix is a single letter, increment it; else, treat it as a sequence
            if len(last_suffix) == 1:
                next_suffix = chr(ord(last_suffix) + 1)  
            else:
                prefix, last_letter = last_suffix[:-1], last_suffix[-1]
                next_suffix = prefix + chr(ord(last_letter) + 1)
        else:
            # Start with 'A' if no clients exist
            next_suffix = "A"

        client_id = f"{group_id}{next_suffix}"

        # Prepare the data for MongoDB
        client_data = {
            "Client ID": client_id,
            "Group ID": group_id,
            "Field Name": field_name,
            "Group Name": group_name,
            "Client Registration Name": client_registration_name,
            "Client Registartion Date-Time":datetime.now(),
            "Reference": reference,
            "GST Number": gst_number,
            "Client Requirements": client_requirements,
            "Client Name": client_name,
            "Connecting Date-Time": connecting_date,
            "Contact Person": {
                "Contact Person Name": contact_name,
                "Contact Person Mobile": contact_mobile,
                "Contact Person Email": contact_email
            },
            "Created On": datetime.now(),
            "Registration Date-Time": datetime.now(),
            "Status": "Active",
            "Status Date-Time": datetime.now(),
            "Status Creator Name": m.getfullname(hn.get_username()),
        }

        clientcollection.insert_one(client_data)

        # Log the action
        log_entry_new_client_group = {
            "action_title": "Form Submission",
            "category": "Client Profile",
            "user_name": m.getfullname(hn.get_username()),
            "action": f"New Client registered with Client ID {client_id} for the Client group {group_name}",
            "date_time": datetime.now(),
            "collection_name": clientcollection.full_name,
            "html_file_source": "table_client_profile.html"
        }
        Log_table.insert_one(log_entry_new_client_group)

        # Flash success message
        flash("Client registered successfully!", "success")
    except Exception as e:
        # Flash error message
        flash(f"Error registering client: {str(e)}", "error")

    # Redirect back to the group profile table
    return redirect(url_for('client_profile.table_client_profile'))


@app.route('/table_client_profile', methods=['GET'])
def table_client_profile():
    loginid,portal_user_title = lm.get_user_info()
    check_login=hn.get_username()
    if check_login != loginid:
        loginid=""
    clients = list(clientcollection.find().sort('Client ID', -1))  
    menu_items = lm.get_loginid_menulist()
    return render_template('table_client_profile.html', clients=clients, username=loginid,menu_list=menu_items)


@app.route('/update_client_details', methods=['POST'])
def update_client_details():
    try:
        # Retrieve form data
        client_id = request.form.get('client_id')
        client_registration_name = request.form.get('client_registration_name')
        reference = request.form.get('reference')
        gst_number = request.form.get('gst_number')
        client_requirements = request.form.get('client_requirements')
        client_name = request.form.get('client_name')
        connecting_date = request.form.get('connecting_date')
        contact_name = request.form.get('contact_name')
        contact_mobile = request.form.get('contact_mobile')
        contact_email = request.form.get('contact_email')

        # Prepare updated data
        updated_data = {
            "Client Registration Name": client_registration_name,
            "Reference": reference,
            "GST Number": gst_number,
            "Client Requirements": client_requirements,
            "Client Name": client_name,
            "Connecting Date-Time": connecting_date,
            "selected_incidents": "",
            "Contact Person": {
                "Contact Person Name": contact_name,
                "Contact Person Mobile": contact_mobile,
                "Contact Person Email": contact_email
            },
            #"Status Date-Time": datetime.now(),  # Update status timestamp
            #"Status Creator Name": "Admin"  # Replace with actual user if applicable
        }

        # Update the record in MongoDB
        result = clientcollection.update_one(
            {"Client ID": client_id},  # Filter by Client ID
            {"$set": updated_data}    # Update with new data
        )

        # Check the result of the update
        if result.matched_count > 0:
            flash("Client details updated successfully!", "success")
        else:
            flash("Client not found. Update failed.", "error")

    except Exception as e:
        # Handle errors
        flash(f"Error updating client details: {str(e)}", "error")

    # Redirect back to the client profile table
    return redirect(url_for('table_client_profile'))

@app.route('/add_client_display_name', methods=['POST'])
def add_client_display_name():
    try:
        # Retrieve form data
        client_id = request.form.get('client_id')
        client_name = request.form.get('client_name')
        client_display_name = request.form.get('client_display_name')

        # Get the last client display id for the given client_id
        last_display = clientdisplaycollection.find({"Client ID": client_id}).sort('Client Display ID', -1).limit(1)
        last_display_list = list(last_display)

        if clientdisplaycollection.find_one({"Client Display Name": client_display_name}):
            flash("Client Display Name already exists.", "error")
            return redirect(url_for('client_profile.table_client_profile'))

        if last_display_list:
            # Extract the last client_display_id
            last_display_id = last_display_list[0]['Client Display ID']
            # Extract the numeric part and increment it
            count = int(last_display_id[len(client_id):] or '0') + 1
        else:
            # If no previous records, start from 1
            count = 1

        if count > 9:
            flash("Error: Client Display ID count cannot exceed 9.", "error")
            return redirect(url_for('table_client_profile'))

        # Generate the new client display id
        client_display_id = f"{client_id}{count}"

        # Insert the new client display profile
        clientdisplaycollection.insert_one({
            "Client Display ID": client_display_id,
            "Client ID": client_id,
            "Client Name": client_name,
            "Client Display Name": client_display_name,
            "Created On": datetime.now(),
            "Status" : "Active",
            "Status Date-Time": datetime.now(),
            "Status Creator Name": m.getfullname(hn.get_username()),

        })

        # Log the action
        log_entry_new_client_display_group = {
            "action_title": "Form Submission",
            "category": "Client Profile",
            "user_name": m.getfullname(hn.get_username()),
            "action": f"Client Display name {client_display_name} is assigned to the client {client_name}.",
            "date_time": datetime.now(),
            "collection_name": clientdisplaycollection.full_name,
            "html_file_source": "table_client_display_profile.html"
        }

        Log_table.insert_one(log_entry_new_client_display_group)

        flash("Client Display Name added successfully!", "success")
        return redirect(url_for('client_profile.table_client_display_profile'))

    except Exception as e:
        flash(f"Error adding Client Display Name: {str(e)}", "error")
        return redirect(url_for('client_profile.table_client_profile'))
     
@app.route('/table_client_display_profile', methods=['GET'])
def table_client_display_profile():
    loginid,portal_user_title = lm.get_user_info()
    check_login=hn.get_username()
    if check_login != loginid:
        loginid=""

    # Fetch data from clientdisplaycollection
    display_profiles = list(clientdisplaycollection.find().sort('Client Display ID', -1))
    menu_items = lm.get_loginid_menulist()
    return render_template('table_client_display_profile.html', display_profiles=display_profiles, username=loginid,menu_list=menu_items)


@app.route('/add_dept_name', methods=['POST'])
def add_dept_name():
    try:
        # Retrieve form data
        client_display_id = request.form.get('client_display_id')
        client_id = request.form.get('client_id')
        client_name = request.form.get('client_name')
        dept_names = request.form.getlist('dept_names[]')  
        dept_count=request.form.get('num_of_dept')
        
        # Fetch the current number of departments for the given Client Display ID
        existing_depts_cursor = departmentcollection.find({"Client Display ID": client_display_id})
        existing_depts = len(list(existing_depts_cursor))  
        
        # Loop through the department names and insert them into MongoDB
        for idx, dept_name in enumerate(dept_names, start=existing_depts + 1):
            # Generate dept_id based on the client_display_id and the sequential number
            dept_id = f"{client_display_id}{str(idx).zfill(2)}" 
            
            # Insert each department into the department collection with the generated dept_id
            departmentcollection.insert_one({
                "Department ID": dept_id,
                "Client ID": client_id,
                "Client Name": client_name,
                "Client Display ID": client_display_id,
                "Department Name/Port Number": dept_name,
                "Created On": datetime.now(),
                "Status": "Active",
                "Status Date-Time": datetime.now(),
                "Status Creator Name": m.getfullname(hn.get_username()),
            })

            # Log the action
            log_entry_new_department = {
                "action_title": "Form Submission",
                "category": "Client Profile",
                "user_name": m.getfullname(hn.get_username()),
                "action": f"{dept_count} departments has been added for the Client with ID: {client_id}.",
                "date_time": datetime.now(),
                "collection_name": departmentcollection.full_name,
                "html_file_source": "table_dept_profile.html"
            }

        Log_table.insert_one(log_entry_new_department)
        
        flash("Department(s) added successfully!", "success")
        return redirect(url_for('table_dept_profile'))  # No need for client_display_id in URL here
                    
    except Exception as e:
        flash(f"Error adding departments: {str(e)}", "error")
        return redirect(url_for('client_profile.table_dept_profile'))  # No need for client_display_id in URL here
    

@app.route('/table_dept_profile', methods=['GET'])
def table_dept_profile():
    loginid,portal_user_title = lm.get_user_info()
    check_login=hn.get_username()
    if check_login != loginid:
        loginid=""
    # Fetch department profiles and sort by 'Dept ID' in descending order
    dept_profiles = list(departmentcollection.find().sort('Dept ID', -1))
    # Pass dept_profiles as a list to the template
    menu_items = lm.get_loginid_menulist()
    return render_template('table_dept_profile.html', dept_profiles=dept_profiles, username=loginid,menu_list=menu_items)

@app.route('/add_camera', methods=['POST'])
def add_camera():
    try:
        # Retrieve form data
        client_id = request.form.get('client_id')
        client_name = request.form.get('client_name')
        department_name = request.form.get('department_name')
        department_id = request.form.get('department_id')
        num_cameras = int(request.form.get('camera_number'))  # The number of cameras to be added

        # Fetch the current number of cameras for the given Department ID
        existing_cameras_cursor = cameracollection.find({"Department ID": department_id})
        existing_cameras = len(list(existing_cameras_cursor))

        # Loop to add the required number of cameras
        for idx in range(existing_cameras + 1, existing_cameras + num_cameras + 1):
            # Generate Camera ID based on the department_id and the sequential number
            camera_id = f"{department_id}{str(idx).zfill(3)}"

            # Insert each camera into the camera collection with the generated camera_id
            cameracollection.insert_one({
                "Camera ID": camera_id,
                "Client ID": client_id,
                "Client Name": client_name,
                "Department ID": department_id,
                "Department Name": department_name,
                "Camera Number": idx,  # Sequential camera number
                "Camera Name": "N/A",
                "Location Type": "N/A", 
                "Working Shift": "N/A", 
                "Status": "Pending",
                "Status Date-Time": datetime.now(),
                "Status Creator Name": m.getfullname(hn.get_username()),
            })

            # Log the action
            log_entry_camera_entry = {
                "action_title": "Form Submission",
                "category": "Client Profile",
                "user_name": m.getfullname(hn.get_username()),
                "action": f"{num_cameras} cameras has been added for the Department ID: {department_id}.",
                "date_time": datetime.now(),
                "collection_name": cameracollection.full_name,
                "html_file_source": "table_camera_profile.html"
            }

            Log_table.insert_one(log_entry_camera_entry)

        flash(f"{num_cameras} Camera(s) added successfully!", "success")
        return redirect(url_for('client_profile.table_camera_pending_list'))

    except Exception as e:
        flash(f"Error adding cameras: {str(e)}", "error")
        return redirect(url_for('client_profile.table_camera_pending_list'))
    
@app.route('/table_camera_pending_list', methods=['GET'])
def table_camera_pending_list():
    loginid,portal_user_title = lm.get_user_info()
    check_login=hn.get_username()
    if check_login != loginid:
        loginid=""

    menu_items = lm.get_loginid_menulist()
    # Fetch department profiles and sort by 'Camera ID' in descending order
    camera_profiles = list(cameracollection.find({'Status':'Pending'}).sort('Camera ID', -1))
    #camera_profiles = list(cameracollection.find({'Status': 'Joining Form Sent'}).sort('_id', -1))
    # Pass camera_profiles as a list to the template
    return render_template('table_camera_pending_list.html', camera_profiles=camera_profiles, username=loginid,menu_list=menu_items)

@app.route('/update_camera', methods=['POST'])
def update_camera():
    departmentID=cameracollection['department_id']
    try:
        data = request.json
        updated_data = data.get('updatedData', [])

        for record in updated_data:
            camera_id = record.get('Camera ID')  # Unique identifier
            if not camera_id:
                continue

            # Check which fields are updated
            updated_fields = {key: value for key, value in record.items() if key not in ['Camera ID']}
            
            # Fetch the original record for comparison
            original_record = cameracollection.find_one({"Camera ID": camera_id})

            # If any of the editable fields are updated, proceed
            if any(
                original_record.get(key) != value
                for key, value in updated_fields.items()
                if key in ['Camera Name', 'Location Type', 'Working Shift']
            ):
                # Add status to the updated fields
                updated_fields['Status'] = 'Active'

                # Update the record in both pending and active tables
                cameracollection.update_one(
                    {"Camera ID": camera_id},  # Find by unique Camera ID
                    {"$set": updated_fields},  # Update the modified fields
                    upsert=True  # Ensure the record exists or is updated
                )

                # Log the action
                log_entry_camera_info_edit1 = {
                    "action_title": "Form Submission",
                    "category": "Client Profile",
                    "user_name": m.getfullname(hn.get_username()),
                    "action": f"Camera details modified with Camera name, Location type & Working Shift. Department ID: {departmentID} ",
                    "date_time": datetime.now(),
                    "collection_name": cameracollection.full_name,
                    "html_file_source": "table_camera_pending_list.html"
                }

                Log_table.insert_one(log_entry_camera_info_edit1)

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/table_camera_profile', methods=['GET'])
def table_camera_profile():
    loginid,portal_user_title = lm.get_user_info()
    check_login=hn.get_username()
    if check_login != loginid:
        loginid=""
    # Fetch department profiles and sort by 'Camera ID' in descending order
    active_camera_profiles = list(cameracollection.find({'Status': {'$in': ['Active', 'Inactive','Non-Selection']}}).sort('Camera ID', -1))
   
    menu_items = lm.get_loginid_menulist()
    return render_template('table_camera_profile.html', active_camera_profiles=active_camera_profiles, username=loginid,menu_list=menu_items)

@app.route('/update_camera_details', methods=['POST'])
def update_camera_details():
    try:
        # Retrieve form data
        camera_id = request.form.get('camera_id')
        camera_name = request.form.get('camera_name')
        status = request.form.get('status')

        if not camera_name or not status:
            flash("Camera Name and Status are required.", "error")
            return redirect(url_for('table_camera_profile'))

        # Prepare updated data
        updated_data = {
            "Camera Name": camera_name,
            "Status": status,
        }

        # Update the camera details in the MongoDB collection
        result = cameracollection.update_one(
            {"Camera ID": camera_id},  
            {"$set": updated_data}     
        )

        # Log the action
        log_entry_camera_info_edit2 = {
            "action_title": "Form Submission",
            "category": "Client Profile",
            "user_name": m.getfullname(hn.get_username()),
            "action": f"Camera details modification confirmed using Modify Button.",
            "date_time": datetime.now(),
            "collection_name": cameracollection.full_name,
            "html_file_source": "table_camera_profile.html"
        }

        Log_table.insert_one(log_entry_camera_info_edit2)

        # Check the result of the update
        if result.matched_count > 0:
            flash("Camera details updated successfully!", "success")
        else:
            flash("Camera not found. Update failed.", "error")

    except Exception as e:
        # Handle errors
        flash(f"Error updating camera details: {str(e)}", "error")

    # Redirect back to the active camera profile page
    return redirect(url_for('table_camera_profile'))

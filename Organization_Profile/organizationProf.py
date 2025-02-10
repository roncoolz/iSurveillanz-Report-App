from flask import Flask, request, redirect, url_for, render_template, flash, jsonify, session, Blueprint
from datetime import datetime
from bson.objectid import ObjectId
import methods.employee_profile.get_para_from_officialid as m
import methods.common_functions.loginid_menulist as lm
import methods.common_functions.common_function as hn
from App_Setting import app, organizationProfile, orgnLocDept, Log_table, collectionofdesignations

# Initialize the Flask app
app = Blueprint('organization', __name__)

# Route to display organizations form
@app.route('/organizations_list_form', methods=['GET', 'POST'])
def organizations_list_form():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""
    menu_items = lm.get_loginid_menulist()

    if request.method == 'POST':
        org_name = request.form['org_name']
        short_name = request.form['short_name']
        
        # Insert the submitted data into MongoDB
        organizationProfile.insert_one({'org_name': org_name, 'short_name': short_name})

        # Log the action
        log_entry_new_organization = {
            "action_title": "Form Submission",
            "category": "Organization Profile",
            "user_name": m.getfullname(hn.get_username()),
            "action": f"New Organization added {org_name} with Short form as: {short_name}.",
            "date_time": datetime.now(),
            "collection_name": organizationProfile.full_name,
            "html_file_source": "organizations_table.html"
        }

        Log_table.insert_one(log_entry_new_organization)

        # Redirect to show the table after form submission
        return redirect(url_for('organization.organizations_table'))

    return render_template('organizations_list_form.html', username=loginid, menu_list=menu_items)

# Route to display only the organizations table
@app.route('/organizations_table')
def organizations_table():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""
    menu_items = lm.get_loginid_menulist()

    # Retrieve all organizations from the MongoDB database
    organizations = list(organizationProfile.find())

    # Render the table template and pass the organizations data
    return render_template('organizations_table.html', organizations=organizations, username=loginid, menu_list=menu_items)

# Route to display organization-location form
@app.route('/organization_location_form', methods=['GET', 'POST'])
def organization_location_form():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""
    menu_items = lm.get_loginid_menulist()

    # Fetch the list of organizations to show in the dropdown
    organizations = list(organizationProfile.find({}, {'_id': 0, 'org_name': 1}))

    if request.method == 'POST':
        # Get form data
        organization_name = request.form['organization_name']
        address_line1 = request.form['address_line1']
        address_line2 = request.form['address_line2']
        city = request.form['city']
        state = request.form['state']
        postal_code = request.form['postal_code']
        country = request.form['country']
        location_name = request.form['location_name']
        mobile_number = request.form['mobile_number']

        # Construct the full address
        full_address = f"{address_line1}, {address_line2}, {city}, {state}, {location_name}, {postal_code}"

        # Insert data into MongoDB
        organizationProfile.update_one(
        {'org_name': organization_name},  # Filter: Find the document with this org_name
        {
            '$set': {  # Update the fields with the new values
                'address_line1': address_line1,
                'address_line2': address_line2,
                'city': city,
                'state': state,
                'postal_code': postal_code,
                'country': country,
                'location_name': location_name,
                'mobile_number': mobile_number,
                'status': 'Active',
                'full_address': full_address  # Store the updated formatted full address
            }
        }
)

        # Log the action
        log_entry_organization_location = {
            "action_title": "Form Submission",
            "category": "Organization Profile",
            "user_name": m.getfullname(hn.get_username()),
            "action": f"{organization_name} is linked to the Location: {location_name}.",
            "date_time": datetime.now(),
            "collection_name": organizationProfile.full_name,
            "html_file_source": "organization_location_table.html"
        }

        Log_table.insert_one(log_entry_organization_location)

        # Redirect to the same form after submission to clear the form and prevent re-submission
        return redirect(url_for('organization.organization_location_form'))

    # Render the form
    return render_template('organization_location_form.html', organizations=organizations, username=loginid, menu_list=menu_items)

# Route to display organization-location table
@app.route('/organization_location_table', methods=['GET'])
def organization_location_table():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""
    menu_items = lm.get_loginid_menulist()

    # Fetch all organization-location data from MongoDB
    organizations = list(organizationProfile.find())

    # Prepare data for table with a formatted address
    organization_location_data = []
    for org in organizations:
        organization_location_data.append({
            'org_name': org.get('org_name', 'N/A'),  # Default to 'N/A' if not found
            'location_name': org.get('location_name', 'N/A'),  # Default to 'N/A' if not found
            'address': f"{org.get('address_line1', 'N/A')}, {org.get('address_line2', '')}, "
                       f"{org.get('city', 'N/A')}, {org.get('state', 'N/A')}, "
                       f"{org.get('location_name', 'N/A')}, {org.get('postal_code', 'N/A')}"
        })

    # Render the table template and pass the organization-location data
    return render_template('organization_location_table.html', organization_locations=organization_location_data, username=loginid, menu_list=menu_items)

# Route to display the 'Organization-Location-Department' form
@app.route('/organization_location_department_form', methods=['GET', 'POST'])
def organization_location_department_form():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""
    menu_items = lm.get_loginid_menulist()
    if request.method == 'POST':
        # Get form data
        organization_name = request.form['organization_name']
        location_name = request.form['location_name']
        department_name = request.form['department_name']
        mobile_number = request.form['mobile_number']
        
        # Insert into the database (can be your desired collection for storing)
        orgnLocDept.insert_one({
            'organization_name': organization_name,
            'location_name': location_name,
            'department_name': department_name,
            'mobile_number': mobile_number,
            'status': 'Active',  
            'status_created_on': datetime.now(),
            'status_creator': m.getfullname(hn.get_username())
        })
        
        # Log the action
        log_entry_organization_location_department = {
            "action_title": "Form Submission",
            "category": "Organization Profile",
            "user_name": m.getfullname(hn.get_username()),
            "action": f"({organization_name}) with ({location_name}) is linked to the Department: ({department_name}).",
            "date_time": datetime.now(),
            "collection_name": orgnLocDept.full_name,
            "html_file_source": "organization_location_department_table.html"
        }

        Log_table.insert_one(log_entry_organization_location_department)

        # Redirect to another page or success page
        return redirect(url_for('organization.organization_location_department_table'))

    # Get all distinct organization names
    organizations = organizationProfile.distinct('org_name')

    # Get all distinct organization names
    locations = organizationProfile.distinct('location_name')

    # Render the form template
    return render_template('organization_location_department_form.html', organizations=organizations, locations=locations, username=loginid, menu_list=menu_items)

@app.route('/organization_location_department_table', methods=['GET'])
def organization_location_department_table():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""
    menu_items = lm.get_loginid_menulist()

    # Fetch all records with status 'Active' from the Organization_Profile collection
    records = list(orgnLocDept.find({'status': 'Active'}))

    # Render the active departments table template and pass the records
    return render_template('organization_location_department_table.html', records=records, username=loginid, menu_list=menu_items)

@app.route('/change_status_inactive/<string:department_id>', methods=['GET'])
def change_status_inactive(department_id):
    try:
        # Convert the department_id string to ObjectId
        department_id = ObjectId(department_id)
    except Exception as e:
        return jsonify({'message': 'Invalid department ID format.'}), 400

    # Find the department record in Organization_Profile collection
    department = orgnLocDept.find_one({'_id': department_id})
    
    if department:
        # Mark the department as Inactive in the Organization_Profile collection
        result = orgnLocDept.update_one(
            {'_id': department_id},
            {'$set': 
             {
                'status': 'Inactive',
                'status_created_on': datetime.now(),
                'status_creator': m.getfullname(hn.get_username())
            }
            }  # Update status to Inactive
        )
        
        if result.modified_count > 0:
            # Successfully updated the status, now redirect to inactive table
            return redirect(url_for('organization.organization_location_department_table_inactive'))  # Redirect to Inactive list page
        else:
            # If no status change was made (maybe it's already Inactive)
            return jsonify({'message': 'Department already inactive or no changes made.'}), 400
    else:
        # If no department found
        return jsonify({'message': 'Department not found.'}), 404
    
@app.route('/change_status_active/<string:department_id>', methods=['GET'])
def change_status_active(department_id):
    try:
        # Convert the department_id string to ObjectId
        department_id = ObjectId(department_id)
    except Exception as e:
        return jsonify({'message': 'Invalid department ID format.'}), 400

    # Find the department record in Organization_Profile collection
    department = orgnLocDept.find_one({'_id': department_id})
    
    if department:
        # Mark the department as Inactive in the Organization_Profile collection
        result = orgnLocDept.update_one(
            {'_id': department_id},
            {'$set': 
             {
                'status': 'Active',
                'status_created_on': datetime.now(),
                'status_creator': m.getfullname(hn.get_username())
            }
            }  # Update status to Active
        )
        
        if result.modified_count > 0:
            # Successfully updated the status, now redirect to Active table
            return redirect(url_for('organization.organization_location_department_table'))  # Redirect to Inactive list page
        else:
            # If no status change was made (maybe it's already Inactive)
            return jsonify({'message': 'Department already active or no changes made.'}), 400
    else:
        # If no department found
        return jsonify({'message': 'Department not found.'}), 404

# Route to display inactive organization/location/department records
@app.route('/organization_location_department_table_inactive')
def organization_location_department_table_inactive():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""
    menu_items = lm.get_loginid_menulist()

    # Retrieve only 'Inactive' records from the Organization_Profile collection
    records = list(orgnLocDept.find({'status': 'Inactive'}))

    # Render the inactive departments table template and pass the records
    return render_template('organization_location_department_table_inactive.html', records=records, username=loginid, menu_list=menu_items)

# Route to display the 'Organization-Location-Department' form
@app.route('/designations_list_form', methods=['GET', 'POST'])
def designations_list_form():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""
    menu_items = lm.get_loginid_menulist()
    if request.method == 'POST':
        # Get form data
        organization_name = request.form['organization_name']
        location_name = request.form['location_name']
        department_name = request.form['department_name']
        designation_name = request.form['designation_name']
        
        # Insert into the database (can be your desired collection for storing)
        collectionofdesignations.insert_one({
            'organization_name': organization_name,
            'location_name': location_name,
            'department_name': department_name,
            'designation_name': designation_name,
            'status': 'Active',  
            'designation_created_on': datetime.now(),
            'designation_creator': m.getfullname(hn.get_username())
        })
        
        # Log the action
        log_entry_organization_location_department = {
            "action_title": "Form Submission",
            "category": "Organization Profile",
            "user_name": m.getfullname(hn.get_username()),
            "action": f"New Designation ({designation_name}) added for Department: ({department_name}).",
            "date_time": datetime.now(),
            "collection_name": orgnLocDept.full_name,
            "html_file_source": "organization_location_department_table.html"
        }

        Log_table.insert_one(log_entry_organization_location_department)

        # Redirect to another page or success page
        return redirect(url_for('organization.designations_list'))

    # Get all distinct organization names
    organizations = organizationProfile.distinct('org_name')

    # Get all distinct organization names
    locations = organizationProfile.distinct('location_name')

    # Get all distinct organization names
    departments = orgnLocDept.distinct('department_name')

    # Render the form template
    return render_template('designations_list_form.html', organizations=organizations, locations=locations, departments=departments, username=loginid, menu_list=menu_items)

@app.route('/designations_list', methods=['GET'])
def designations_list():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""
    menu_items = lm.get_loginid_menulist()

    # Fetch all records with status 'Active' from the Organization_Profile collection
    records = list(collectionofdesignations.find({'status': 'Active'}))

    # Render the active departments table template and pass the records
    return render_template('designations_list.html', records=records, username=loginid, menu_list=menu_items)
import sys
import os
from flask import Flask, request, redirect, url_for, render_template, flash, send_file, jsonify, session, Blueprint
from flask_mail import Mail, Message
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app_settings')))
from App_Setting import PortalTitlesList, collection, db_FusionBizCentral, app, MongoClient, Interviewers_List, Log_table, PC_profile, CollectionOfPersonalInfo, CollectionOfOfficialInfo, CollectionOfBankDetails, PreHRApproved, ActiveEmployees
import gridfs
from bson.objectid import ObjectId
import io
import re
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'User_Profile')))
import methods.employee_profile.get_para_from_officialid as m
import methods.common_functions.loginid_menulist as lm
import socket
import methods.common_functions.common_function as hn
import random
import string
from jinja2 import FileSystemLoader
from jinja2 import Environment
from flask_pymongo import PyMongo
from pymongo import MongoClient, errors
from pymongo.errors import DuplicateKeyError

# Initialize the Flask app
app=Blueprint('register',__name__)

'''template_folders = [os.path.abspath("User_Profile/templates"),os.path.abspath("ctemplates")]
app.jinja_loader = FileSystemLoader(template_folders)
app.static_folder = os.path.abspath("static")

mail = Mail(app)'''
fs = gridfs.GridFS(db_FusionBizCentral)
#logs_collection=Log_table
fs = gridfs.GridFS(db_FusionBizCentral)

def generate_random_word():
    # Create a random six-letter word
    word = ''.join(random.choices(string.ascii_lowercase, k=6))
    return word

# Generate and print a random word
random_word = generate_random_word()

'''@app.route('/')
def index():
        if 'logged_in' in session:
            username = session.get('username', '')
            return render_template('report_master.html', username=username)
        return render_template('report_master.html')

@app.route('/log_in.html')
def log_in():
    return render_template('log_in.html')

@app.route('/login', methods=['POST'])
def login():
        username = request.form.get('username')
        password = request.form.get('password')

        # Find the user in MongoDB and check the password directly
        user = collection.find_one({'USERNAME': username, 'PASSWORD': password})

        if user:  
            session['logged_in'] = True
            session['username'] = username  # Store the username in the session
            hn.update_host_name(username)
            return redirect(url_for('register_form'))
        
        else:
            flash('Invalid username or password', 'error')
            return redirect(url_for('log_in'))

@app.route('/logout')
def logout():
        session.pop('logged_in', None)
        session.pop('username', None)  # Remove username from session
        #flash('You have been logged out.', 'info')
        hn.update_host_name('')
        return redirect(url_for('log_in'))'''

@app.route('/register_form', methods=['GET', 'POST'])
def register_form():
        print("test")
        if request.method == "POST":
            full_name = request.form.get("full_name")
            email_address = request.form.get("email_address")
            mobile_number = request.form.get("mobile_number")           
            Username=request.form.get("full_name")
            Password=random_word
                        
            '''# Check if a user with the same email or mobile number already exists
            existing_user = collection.find_one({
                "$or": [
                    {"email_address": email_address},
                    {"mobile_number": mobile_number}
                ]
            })

            if existing_user:
                # Flash a message to inform the user that registration already exists
                flash('A user with this email or mobile number already exists. Please check your details or try logging in.', 'error')
                return redirect(url_for('register'))'''

            # Validate mobile number (must be exactly 10 digits)
            if not re.fullmatch(r'\d{10}', mobile_number):
                flash('Mobile number must be exactly 10 digits.', 'error')
                return redirect(url_for('register'))
            
            # Generate a registration number
            registration_number = datetime.now().strftime("%Y%m%d%H%M%S")
            
            # File upload handling
            uploaded_file = request.files['cv_file']
            file_id = None
            if uploaded_file and uploaded_file.filename.endswith('.pdf'):
                file_id = fs.put(uploaded_file, filename=uploaded_file.filename)

            # Insert data into MongoDB
            data = {
                "full_name": full_name,
                "email_address": email_address,
                "mobile_number": mobile_number,
                "registration_number": registration_number,
                "cv_file_id": file_id,
                "Status": "Registered",
                "USERNAME":Username,
                "PASSWORD":Password

            }
            db_result=collection.insert_one(data)

            # Log entry for the registration action
            log_entry_registration_form = {
                "action_title": "Form Submission",
                "official_id": Username,
                "action": "Registration form received",
                #"detailed_info": f"Registration Form filled by { m.getfullname(hn.get_username())}",
                "user": "Employee",
                "user_name":  Username,
                "date_time": datetime.now(),
                "collection_name": collection.full_name,
                "collection_id":db_result.inserted_id,
                "html_file_source": "register_form.html",
                "category":"User Profile"
            }

            # Insert log into MongoDB collection (Registration Form)
            Log_table.insert_one(log_entry_registration_form)

            return redirect(url_for('settings_SelectionProcess'))
        return render_template('register_form.html')

@app.route('/log_table')
def log_table():
    # Fetch all logs from the MongoDB logs collection
    logs = list(Log_table.find({}))  # Fetch all documents in the 'logs' collection    
    loginid,portal_user_title = lm.get_user_info()
    check_login=hn.get_username()
    print(loginid)
    print(check_login)
    if check_login != loginid:
        loginid=""
    return render_template('log_table.html', logs=logs, username=loginid)
    
@app.route('/handle_user_action', methods=['POST'])
def handle_user_action():
        email_address = request.form.get('email_address')
        registration_number = request.form.get('registration_number')
        full_name = request.form.get('full_name')
        action = request.form.get('action')

        if action == 'cancel':
            # Update user status to 'cancelled' in the database
            result = collection.update_one({'registration_number': registration_number}, {'$set': {'Status': 'cancelled'}})

            if result.modified_count > 0:
                flash(f"Registration for {full_name} has been cancelled.", 'info')
                # After cancelling, redirect to the cancelled table
                return redirect(url_for('cancel_table'))

        elif action == 'interview_missed':
            # Update user status to 'interview missed' in the database
            result = collection.update_one(
                {'registration_number': registration_number},
                {'$set': {'Status': 'interview missed'}}
            )

            if result.modified_count > 0:
                flash(f"Interview for {full_name} was missed.", 'info')
                # After marking as interview missed, redirect to the cancelled table
                return redirect(url_for('cancel_table'))

        # Handle other actions (e.g., moving to scheduled, etc.)
        return redirect(url_for('show_table'))

@app.route('/handle_notes_submission', methods=['POST'])
def handle_notes_submission():
        full_name = request.form.get('full_name')
        registration_number = request.form.get('registration_number')
        notes = request.form.get('notes')

        # Update the user record with the new note or append it
        result = collection.update_one(
            {'registration_number': registration_number},
            {'$set': {'notes': notes}}
        )

        if result.modified_count > 0:
            flash(f"Notes updated for {full_name}.", 'success')
        else:
            flash(f"Failed to update notes for {full_name}.", 'error')

        return redirect(url_for('register.show_table'))

@app.route('/show_table', methods=['GET', 'POST'])
def show_table():
        # Fetch only the users with 'Registered' status
        records = list(collection.find({'Status': 'Registered'}).sort('_id', -1))
        loginid,portal_user_title = lm.get_user_info()
        check_login=hn.get_username()
        print(loginid)
        print(check_login)
        if check_login != loginid:
            loginid=""
        
        menu_items = lm.get_loginid_menulist()
        return render_template('table.html', records=records, username=loginid, menu_list=menu_items )

@app.route('/cancel_table')
def cancel_table():
        cancelled_records = list(collection.find({
            'Status': {'$in': ['Interview Missed', 'Interview Rescheduled', 'Interview Cancelled', 'cancelled','Not Selected/On-Hold', 'cancelled from Scheduled List']}
        }).sort('_id', -1))
        return render_template('cancel_table.html', records=cancelled_records)

@app.route('/view_cv/<file_id>')
def view_cv(file_id):
        try:
            file_data = fs.get(ObjectId(file_id))
            response = send_file(
                io.BytesIO(file_data.read()),
                mimetype='application/pdf',
                as_attachment=False,
                download_name=file_data.filename
            )
            return response
        except Exception as e:
            flash(f"Error loading CV: {e}", 'error')
            return redirect(url_for('show_table'))
        
@app.route('/review_form', methods=['POST'])
def review_form():
        registration_number = request.form.get('registration_number')
        full_name = request.form.get('full_name')
        email = request.form.get('email')

        user = collection.find_one({'registration_number': registration_number})
        name=user.get('USERNAME')

        # Handle form submission
        relevant_skills = request.form['relevant_skills']
        communication_skills = request.form['communication_skills']
        problem_solving = request.form['problem_solving']
        culture_fit = request.form['culture_fit']
        comments = request.form['comments']

        # Define a mapping for the marks based on the rating
        rating_map = {'Poor': 1, 'Average': 3, 'Good': 5}

        # Calculate the total marks
        total_marks = (
            rating_map.get(relevant_skills, 0) +
            rating_map.get(communication_skills, 0) +
            rating_map.get(problem_solving, 0) +
            rating_map.get(culture_fit, 0)
        ) / 4
        print(total_marks)
        # Assuming you have a way to update the interview records in the database
        record = db_FusionBizCentral.records.find_one({'registration_number': registration_number})
        
        # Update the record with the comments and interview review marks
        result= collection.update_one(
            {'registration_number': registration_number},
            {'$set': {'comments': comments, 'interview_review_marks': total_marks}}
        )

        log_entry_review_form = {
                "action_title": "Form Submission",
                "official_id": hn.get_username(),
                "action": f"Interview Evaluation for {name}",
                #"detailed_info": f"Interview taken by interviewers & Evaluation Done. Received Marks = {total_marks}",
                "user": "Employee",
                "user_name":  m.getfullname(hn.get_username()),
                "date_time": datetime.now(),
                "collection_name": collection.full_name,
                "collection_id":user['_id'],
                "html_file_source": "scheduled_table.html",
                "category":"User Profile"
            }

        # Insert log into MongoDB collection
        Log_table.insert_one(log_entry_review_form)

        if result.modified_count > 0:
            flash('Review submitted successfully!', 'success')
        else:
            flash('Failed to submit review.', 'error')

        #flash('Review submitted successfully!', 'success')
        return redirect(url_for('register.scheduled_interviews'))

@app.route('/schedule_interview', methods=['POST'])
def schedule_interview():
    registration_number = request.form['registration_number']
    full_name = request.form['full_name']
    interview_date = request.form['interview_date']

    user = collection.find_one({'registration_number': registration_number})

    updated_data = {
        'interview_date': interview_date,
        'Status': 'Interview Scheduled',
    }

    # Update user status in the collection
    db_result=collection.update_one({'registration_number': registration_number}, {'$set': updated_data})

    # Log entry for the registration action
    log_entry_schedule_interview_form = {
            "action_title": "Form Submission",
            "official_id": hn.get_username(),
            "action": f"Interview Scheduled for {full_name} on {interview_date}.",
            #"detailed_info": f"Interview Scheduled on {interview_date} by { m.getfullname(hn.get_username())}" ,
            "user": "Employee",
            "user_name": m.getfullname(hn.get_username()),
            "date_time": datetime.now(),
            "collection_name": collection.full_name,
            "collection_id":user['_id'],
            "html_file_source": "table.html",
            "category":"User Profile"
        }

    # Insert log into MongoDB collection
    Log_table.insert_one(log_entry_schedule_interview_form)

    if db_result.modified_count > 0:
        flash(f"Interview for {full_name} has been scheduled.", 'success')
    else:
        flash(f"Failed to schedule interview for {full_name}.", 'error')

    return redirect(url_for('register.scheduled_interviews'))

'''@app.route('/selected_interviewers', methods=['POST'])
def selected_interviewers():
        # Fetch all scheduled interviews
        records= Interviewers_List.find({})
        #interviewers = records.Interviewer_Name.find()
        interviewers_list = [interviewer['Interviewer_Name'] for interviewer in records]  # List of names
        print(interviewers_list)
        #return redirect(url_for('selected_interviewers'))
        return render_template('scheduled_table.html', interviewer11=tuple(interviewers_list))'''

@app.route('/assign_interviewers', methods=['POST'])
def assign_interviewers():
        registration_number = request.form['registration_number']
        selected_interviewers = request.form.getlist('interviewers')  # List of selected interviewers

        user = collection.find_one({'registration_number': registration_number})
        name=user.get('USERNAME')
        
        # Update the interviewers list for the specific interview
        Result=collection.update_one(
            {'registration_number': registration_number},
            {'$set': {'interviewers_list': str(selected_interviewers)}}
        )

        # Log entry for the registration action
        log_entry_select_interviewer = {
            "action_title": "Form Submission",
            "official_id": hn.get_username(),
            "action": f"Interviewers selected for {name}.",
            "detailed_info": f"Interviewers selected are - ({selected_interviewers}).",
            #"detailed_info": f"Interview Scheduled on {interview_date} by { m.getfullname(hn.get_username())}" ,
            "user": "Employee",
            "user_name": m.getfullname(hn.get_username()),
            "date_time": datetime.now(),
            "collection_name": collection.full_name,
            "collection_id":user['_id'],
            "html_file_source": "scheduled_table.html",
            "category":"User Profile"
        }

        # Insert log into MongoDB collection
        Log_table.insert_one(log_entry_select_interviewer)

        flash('Interviewers successfully assigned!', 'success')
        return redirect(url_for('register.scheduled_interviews'))

'''@app.route('/scheduled_interviews')
    def scheduled_interviews():
        # Fetch users whose status is 'Interview Scheduled'
        scheduled_users = list(collection.find({'Status': 'Interview Scheduled'}).sort('_id', -1))
        return render_template('scheduled_table.html', records=scheduled_users)'''


@app.route('/scheduled_interviews')
def scheduled_interviews():
        # Fetch users whose status is 'Interview Scheduled' or 'Next Interview Scheduled'
        scheduled_users = list(collection.find({'Status': {'$in': ['Interview Scheduled', 'Next Interview Scheduled']}}).sort('_id', -1))
        records= Interviewers_List.find({})
        interviewers_list = [interviewer['Interviewer_Name'] for interviewer in records]  # List of names
        print(interviewers_list)
        loginid,portal_user_title = lm.get_user_info()
        check_login=hn.get_username()
        print(loginid)
        print(check_login)
        if check_login != loginid:
            loginid=""
        
        menu_items = lm.get_loginid_menulist()
        return render_template('scheduled_table.html', records=scheduled_users,interviewer11=interviewers_list, username=loginid, menu_list=menu_items)

@app.route('/update_status_interview/<registration_number>', methods=['GET', 'POST'])
def update_status_interview(registration_number):
        user = collection.find_one({'registration_number': registration_number})
        if request.method == 'POST':
            updated_status = request.form['interview_status']
            interview_date = request.form.get('interview_date')
            
            result = collection.update_one(
                {'registration_number': registration_number},
                {'$set': {'Status': updated_status, 'interview_date': interview_date}}
            )

            if result.modified_count > 0:
                flash('Interview status updated successfully!', 'success')

                # Redirect to the appropriate table based on the updated status
                if updated_status == 'Not Selected/On-Hold':
                    return redirect(url_for('cancel_table'))
            else:
                flash('Failed to update interview status.', 'error')

            # Default redirect if status is not 'Not Selected/On-Hold'
            return redirect(url_for('scheduled_interviews'))
        
        return render_template('update_interview_modal.html', user=user)


@app.route('/interview_updates', methods=['POST'])
def interview_updates():
        registration_number = request.form.get('registration_number')
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        interview_status = request.form.get('interview_status')

        # Update the user status in the database
        result = collection.update_one(
            {'registration_number': registration_number},
            {'$set': {'Status': interview_status}}
        )

        if result.modified_count > 0:
            flash(f"Interview status updated to '{interview_status}' for {full_name}.", 'success')
            # Redirect to cancel_table.html if status is 'Interview Cancel'
            if interview_status == 'Interview Cancel':
                return redirect(url_for('cancel_table'))
        else:
            flash(f"Failed to update interview status for {full_name}.", 'error')

        return redirect(url_for('scheduled_interviews'))

@app.route('/add_to_shortlist/<registration_number>', methods=['POST'])
def add_to_shortlist(registration_number):
        #registration_number = request.form['registration_number']
        user = collection.find_one({'registration_number': registration_number})
        name=user.get('USERNAME')
        # Logic to move the record to "Interview Reviewed List"
        result = collection.update_one(
            {'registration_number': registration_number},
            {'$set': {'Status': 'Shortlisted'}}
        )

        # Log entry for the registration action
        log_entry_add_to_shortlist = {
            "action_title": "Button Confirmation",
            "official_id": hn.get_username(),
            "action": f"{name} added to the Shortlist",
            #"detailed_info": f"Candidate added to shortlist for further selection process.",
            "user": "Employee",
            "user_name": m.getfullname(hn.get_username()),
            "date_time": datetime.now(),
            "collection_name": collection.full_name,
            "collection_id":user['_id'],
            "html_file_source": "scheduled_table.html",
            "category":"User Profile"
        }

        # Insert log into MongoDB collection
        Log_table.insert_one(log_entry_add_to_shortlist)  
        
        if result.modified_count > 0:
            flash('Candidate has been added to the shortlist!', 'success')
        else:
            flash('Failed to add candidate to the shortlist.', 'error')

        return redirect(url_for('register.scheduled_interviews'))

@app.route('/schedule_next_interview', methods=['POST'])
def schedule_next_interview():
        registration_number = request.form['registration_number']
        full_name = request.form['full_name']
        email_address = request.form['email_address']
        interview_date = request.form['interview_date']
        comments = request.form['comments']

        # Update the user record with the next interview date and comments
        result = collection.update_one(
            {'registration_number': registration_number},
            {
                '$set': {
                    'Status': 'Next Interview Scheduled',
                    'interview_date': interview_date,
                    'comments': comments
                }
            }
        )

        if result.modified_count > 0:
            flash(f"Next interview scheduled for {full_name}.", 'success')
        else:
            flash(f"Failed to schedule next interview for {full_name}.", 'error')

        return redirect(url_for('interview_reviewed_list'))

@app.route('/interview_reviewed_list')
def interview_reviewed_list():
    # Fetch only the users with 'Shortlisted' status
    shortlisted_records = list(collection.find({'Status': 'Shortlisted'}).sort('_id', -1))
    loginid,portal_user_title = lm.get_user_info()
    check_login=hn.get_username()
    print(loginid)
    print(check_login)
    if check_login != loginid:
        loginid=""
        
    menu_items = lm.get_loginid_menulist()
    return render_template('interview_reviewed_list.html', records=shortlisted_records,username=loginid, menu_list=menu_items)

@app.route('/add_to_selected/<registration_number>', methods=['POST'])
def add_to_selected(registration_number):
        user = collection.find_one({'registration_number': registration_number})
        name=user.get('USERNAME')
        # Update the status to 'Selected' to indicate the candidate was selected
        result = collection.update_one(
            {'registration_number': registration_number},
            {'$set': {'Status': 'Selected'}}
        )

        # Log entry for the registration action
        log_entry_select_confirmation = {
            "action_title": "Button Confirmation",
            "official_id": hn.get_username(),
            "action": f"Selection Confirmation for {name}",
            #"detailed_info": f"Candidate selection confirmation to proceed with trial period.",
            "user": "Employee",
            "user_name": m.getfullname(hn.get_username()),
            "date_time": datetime.now(),
            "collection_name": collection.full_name,
            "collection_id":user['_id'],
            "html_file_source": "interview_reviewed_list.html",
            "category":"User Profile"
        }

        # Insert log into MongoDB collection
        Log_table.insert_one(log_entry_select_confirmation)  

        if result.modified_count > 0:
            flash('Candidate has been added to the selected list!', 'success')
        else:
            flash('Failed to add candidate to the selected list.', 'error')

        return redirect(url_for('register.interview_reviewed_list'))

@app.route('/selected_candidates')
def selected_candidates():
        # Fetch users whose status is 'Selected'
        selected_records = list(collection.find({'Status': 'Selected'}).sort('_id', -1))
        loginid,portal_user_title = lm.get_user_info()
        check_login=hn.get_username()
        print(loginid)
        print(check_login)
        if check_login != loginid:
            loginid=""
        
        menu_items = lm.get_loginid_menulist()
        return render_template('selected_candidates.html', records=selected_records,username=loginid, menu_list=menu_items)

@app.route('/schedule_trial', methods=['POST'])
def schedule_trial():
        registration_number = request.form['regNumber']
        full_name = request.form['fullName']
        email_address = request.form['email']
        trial_start_date = request.form['trialStartDate']
        trial_end_date = request.form['trialEndDate']
        user = collection.find_one({'registration_number': registration_number})
        name=user.get('USERNAME')

        # Update the user record with the trial details
        result = collection.update_one(
            {'registration_number': registration_number},
            {
                '$set': {
                    'Status': 'Trial Scheduled',
                    'trial_start_date': trial_start_date,
                    'trial_end_date': trial_end_date
                }
            }
        )

        # Log entry for the registration action
        log_entry_trial_form = {
            "action_title": "Form Submission",
            "official_id": hn.get_username(),
            "action": f"Trial Period set for {name} from {trial_start_date} to {trial_end_date}",
            #"detailed_info": f"Trial Period Assigned to the candidate.",
            "user": "Employee",
            "user_name": m.getfullname(hn.get_username()),
            "date_time": datetime.now(),
            "collection_name": collection.full_name,
            "collection_id":user['_id'],
            "html_file_source": "interview_reviewed_list.html",
            "category":"User Profile"
        }

        # Insert log into MongoDB collection
        Log_table.insert_one(log_entry_trial_form)  

        if result.modified_count > 0:
            flash(f"Trial has been scheduled for {full_name}.", 'success')
        else:
            flash(f"Failed to schedule trial for {full_name}.", 'error')

        return redirect(url_for('register.on_trial_list'))

@app.route('/on_trial_list')
def on_trial_list():
        # Fetch only the users with 'Trail Scheduled' status
        on_trial_records = list(collection.find({'Status': 'Trial Scheduled'}).sort('_id', -1))
        loginid,portal_user_title = lm.get_user_info()
        check_login=hn.get_username()
        print(loginid)
        print(check_login)
        if check_login != loginid:
            loginid=""
        
        menu_items = lm.get_loginid_menulist()
        return render_template('on_trial_list.html', records=on_trial_records,username=loginid, menu_list=menu_items)

@app.route('/joining_form/<registration_number>', methods=['GET', 'POST'])
def joining_form(registration_number):
    candidate = collection.find_one({'registration_number': registration_number})
    name=candidate.get('USERNAME')

    loginid,portal_user_title = lm.get_user_info()
    check_login=hn.get_username()
    print(loginid)
    print(check_login)
    if check_login != loginid:
        loginid=""
        
    menu_items = lm.get_loginid_menulist()
    
    if request.method == 'POST':
        user_id = ObjectId()  # Generate a shared ID for linking data in all collections

        # Official ID generation logic
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        initials = (first_name[0] if first_name else "").upper() + (last_name[0] if last_name else "").upper()
        random_number = str(random.randint(100, 999))
        official_id = f"ISEMP{random_number}{initials}"

        # Personal Info Data
        adhar_card_number = request.form.get("aadhar_card_number")
        print("test="+str(adhar_card_number))
        # Check if the Aadhar Card Number is provided and not null
        if adhar_card_number:
            # Check if the Aadhar Card Number already exists in the collection
            existing_aadhar = CollectionOfPersonalInfo.find_one({"adhar_card_details.Aadhar Card Number": adhar_card_number})
            if existing_aadhar:
                flash("Aadhar Card Number already exists", "error")
                return redirect(url_for('register.joining_form', registration_number=registration_number))
        else:
            flash("Aadhar Card Number is required", "error")
            return redirect(url_for('register.joining_form', registration_number=registration_number))

        udid_number = request.form.get("udid_card_number")
        if not udid_number:  # If UDID Number is not provided or is empty
            flash("UDID Number is required", "error")
            return redirect(url_for('register.joining_form', registration_number=registration_number))

        personal_data = {
            "User ID": registration_number,
            "Official ID": official_id,
            "Date of Birth": request.form.get("dob"),
            "Gender": request.form.get("gender"),
            "Marital Status": request.form.get("marital_status"),
            "Blood Group": request.form.get("blood_group"),
            "UDID Number": request.form.get("udid_card_number") or None,
            "address_line_1": request.form.get("corr_address_line1"),
            "address_line_2": request.form.get("corr_address_line2"),
            "City": request.form.get("corr_city"),
            "District": request.form.get("corr_state"),
            "Country": request.form.get("corr_country"),
            "Postal Code": request.form.get("corr_postal_code"),
            "address_line_1": request.form.get("perm_address_line1"),
            "address_line_2": request.form.get("perm_address_line2"),
            "City": request.form.get("perm_city"),
            "District": request.form.get("perm_state"),
            "Country": request.form.get("perm_country"),
            "Postal_Code": request.form.get("perm_postal_code"),
            "Whatsapp Number": request.form.get("whatsapp_number"),
            "Aadhar Card Number": adhar_card_number,
            "is_aadhar_linked_to_mobile_number": request.form.get("aadhar_linked"),
            "linked_mobile_number": request.form.get("aadhar_contact"),
            "Family Name": request.form.get("emergency_name"),
            "Emergency Contact Number": request.form.get("emergency_phone"),
            "Relation": request.form.get("emergency_relationship"),
            "Hearing Status (Deaf/Normal)": request.form.get("hearing_impaired") == "Yes",
            "Status": "Pending"
        
        }

        # Remove the UDID field if it's None
        if not personal_data["UDID Number"]:
            personal_data.pop("UDID Number")

        CollectionOfPersonalInfo.insert_one(personal_data)
        
        # Official Info Data
        official_data = {
            "User ID": registration_number,
            "Official ID": official_id,
            "First Name": first_name,
            "Middle Name": request.form.get("middle_name"),
            "Last Name": last_name,
            "Email Address": request.form.get("email"),
            "Mobile Number": request.form.get("whatsapp_number"),
            "Registration Number": registration_number,
            "User Login ID":official_id,
            "Status": "Joined Form",
            "Portal User Title": None,
            "Passcode": None
        }
        CollectionOfOfficialInfo.insert_one(official_data)

        # Bank Details Data
        bank_data = {
            "User ID": registration_number,
            "Official ID": official_id,
            "Bank Name": request.form.get("bank_name"),
            "Bank Account Number": request.form.get("bank_account_number"),
            "IFSC Code": request.form.get("ifsc_code"),
            "Branch Name": request.form.get("branch"),
            "PAN Card Number": request.form.get("pan_card_number"),
            "has_debit_card": request.form.get("has_debit_card") == "Yes",
            "has_upi": request.form.get("has_upi") == "Yes",
            "Status": "Pending"
            }
        
        CollectionOfBankDetails.insert_one(bank_data)

        # Update candidate status to "Joined Form" and move to another collection
        collection.delete_one({'registration_number': registration_number})

        log_entry_joining_form = {
                "action_title": "Form Submission",
                "official_id": hn.get_username(),
                "action": f"Joining Form filled for {name}",
                #"detailed_info": f"Interview taken by interviewers & Evaluation Done. Received Marks = {total_marks}",
                "user": "Employee",
                "user_name":  m.getfullname(hn.get_username()),
                "date_time": datetime.now(),
                "collection_name": collection.full_name,
                "collection_id":candidate['_id'],
                "html_file_source": "Joining_Form.html",
                "category":"User Profile"
            }

        # Insert log into MongoDB collection
        Log_table.insert_one(log_entry_joining_form)

        '''# Move the candidate's data to a different table/collection (or a new entry in a list)
        candidate_data = collection.find_one({'registration_number': registration_number})
        collection.insert_one(candidate_data)

        # Remove from the 'on_trial_list' collection (if applicable)
        collection.delete_one({'registration_number': registration_number})'''

        return redirect(url_for('register.joining_form_list'))

    return render_template('Joining_Form.html',candidate=candidate,registration_number=registration_number,username=loginid, menu_list=menu_items)

@app.route('/joining_form_list')
def joining_form_list():
    loginid,portal_user_title = lm.get_user_info()
    check_login=hn.get_username()
    print(loginid)
    print(check_login)
    if check_login != loginid:
        loginid=""
    
    menu_items = lm.get_loginid_menulist()
    # Fetch all the personal, official, and bank details
    personal_info = list(CollectionOfPersonalInfo.find())
    official_info = list(CollectionOfOfficialInfo.find())
    bank_details = list(CollectionOfBankDetails.find())
    employee_info=list(CollectionOfOfficialInfo.find({'Status': 'Joined Form'}).sort('_id', -1))
    users = {}

    # Merge personal info
    for info in personal_info:
        user_id = str(info.get("User ID"))
        users[user_id] = {"personal": info}

    # Merge official info
    for info in official_info:
        user_id = str(info.get("User ID"))
        if user_id in users:
            users[user_id]["official"] = info

    # Merge bank details
    for info in bank_details:
        user_id = str(info.get("User ID"))
        if user_id in users:
            users[user_id]["bank"] = info
    
    for info in employee_info:
        user_id=str(info.get("registration_number"))
        if user_id in users:
            users[user_id]["emp"]=info

    # Flatten data for template
    merged_users = []
    for user_id, data in users.items():
        merged_users.append({**data.get("personal", {}), **data.get("official", {}), **data.get("bank", {}), **data.get("emp",{})})
    portal_categories = list(PortalTitlesList.distinct('category'))  # Fetch distinct categories
    return render_template('joining_form_list.html', users=merged_users,records=employee_info,categories=portal_categories,username=loginid, menu_list=menu_items)

@app.route('/update_user', methods=['POST'])
def update_user():
    user_id = request.form.get('user_id')

    # Prepare updates for the main collection
    base_collection_updates = {
        "First Name": request.form.get('first_name'),
        "Last Name": request.form.get('last_name'),
        "email_address": request.form.get('email'),
        "Mobile Number": request.form.get('whatsapp_number'),
        "Official ID": request.form.get('official_id'),
        "bank_details.Bank Account Number": request.form.get('bank_account'),
        "Date of Birth": request.form.get('dob'),
        "Gender": request.form.get('gender'),
        "Marital Status": request.form.get('marital_status'),
        "Blood Group": request.form.get('blood_group'),
        "UDID Number": request.form.get('udid'),
        "adhar_card_details.Whatsapp Number": request.form.get('whatsapp_number'),
        "adhar_card_details.Aadhar Card Number": request.form.get('aadhar_card_number'),
        "emergency_contact.Family Name": request.form.get('emergency_name'),
        "emergency_contact.Emergency Contact Number": request.form.get('emergency_phone'),
        "emergency_contact.Relation": request.form.get('emergency_relationship')
    }

    # Prepare updates for different collections
    personal_info_updates = {
        "First Name": request.form.get('first_name'),
        "Last Name": request.form.get('last_name'),
        "email_address": request.form.get('email'),
        "Mobile Number": request.form.get('whatsapp_number'),
        "Date of Birth": request.form.get('dob'),
        "Gender": request.form.get('gender'),
        "Marital Status": request.form.get('marital_status'),
        "Blood Group": request.form.get('blood_group'),
        "UDID Number": request.form.get('udid'),
        "adhar_card_details.Whatsapp Number": request.form.get('whatsapp_number'),
        "adhar_card_details.Aadhar Card Number": request.form.get('aadhar_card_number'),
        "emergency_contact.Family Name": request.form.get('emergency_name'),
        "emergency_contact.Emergency Contact Number": request.form.get('emergency_phone'),
        "emergency_contact.Relation": request.form.get('emergency_relationship'),
    }

    official_info_updates = {
        "Official ID": request.form.get('official_id'),
    }

    bank_details_updates = {
        "bank_details.Bank Account Number": request.form.get('bank_account'),
        "bank_details.Bank Name": request.form.get('bank_name'),
        "bank_details.IFSC Code": request.form.get('ifsc'),
        "bank_details.Branch Name": request.form.get('branch'),
        "bank_details.PAN Card Number": request.form.get('pan'),
        "bank_details.has_debit_card": request.form.get('debit_card'),
        "bank_details.has_upi": request.form.get('upi'),
    }

    # Update the main collection
    result = collection.update_one(
        {'registration_number': user_id},
        {'$set': base_collection_updates}
    )

    # Update each specific collection
    personal_info_result = CollectionOfPersonalInfo.update_one(
        {'User ID': user_id},
        {'$set': personal_info_updates}
    )

    official_info_result = CollectionOfOfficialInfo.update_one(
        {'User ID': user_id},
        {'$set': official_info_updates}
    )

    bank_details_result = CollectionOfBankDetails.update_one(
        {'User ID': user_id},
        {'$set': bank_details_updates}
    )

    # Check results and give feedback
    if (
        result.matched_count > 0 and
        personal_info_result.matched_count > 0 and
        official_info_result.matched_count > 0 and
        bank_details_result.matched_count > 0
    ):
        flash('User details updated successfully in all collections.', 'success')
    else:
        flash('User not found or update failed in one or more collections.', 'error')

    return redirect(url_for('joining_form_list'))

@app.route('/employment_confirmation/<registration_number>', methods=['POST'])
def submit_employment_confirmation(registration_number):
    # Fetch the user's current details from the 'joining_form' collection
    candidate = CollectionOfOfficialInfo.find_one({'Registration Number': registration_number})
    name=candidate.get('USERNAME')
    #user = collection.find_one({'registration_number': registration_number})

    if candidate:
        # Capture new form data
        full_name = request.form['fullName']
        email = request.form['email']
        organization = request.form.get("organization")
        location = request.form.get("location")
        department = request.form.get("department")
        designation = request.form.get("designation")
        shift = request.form.get("shift")
        date_of_joined = request.form.get("dateJoined")
        portalcategory=request.form.get("category")
        portaltitle=request.form.get("portal_title")
        elective_subject = request.form.get("electiveSubject")

        # Update the candidate's status to 'Pre HR Approved'
       
        '''result = collection.update_one(
            {'registration_number': registration_number},
            {'$set': {
                    'Status': 'Pre HR Approved',
                    'email': email,
                    'phone_number': candidate['mobile_number'],
                    'date_joined': date_of_joined,
                    'elective_subject': elective_subject,
                    'organization': organization,
                    'location': location,
                    'department': department,
                    'designation': designation,
                    'shift': shift
                }
            }
        )'''

        #Update the data in Official Info 
        officialinfoupdating=CollectionOfOfficialInfo.update_one(
            {'Registration Number': registration_number},
            {'$set': 
                {
                    "Portal User Title": portaltitle,
                    "Passcode": random_word,
                    "Status": "Pre HR Approved",
                    "email": email,
                    "phone_number": candidate['Mobile Number'],
                    "date_joined": date_of_joined,
                    "elective_subject": elective_subject,
                    "organization": organization,
                    "location": location,
                    "department": department,
                    "designation": designation,
                    "shift": shift
                }
            }
        )

        # Log entry for the confirmation of employment
        log_entry_confirmation_of_employment = {
            "action_title": "Form Submission",
            "official_id": hn.get_username(),
            "action": f"Confirmation of Employment for {name}",
            #"detailed_info": f"Trial Period Assigned to the candidate.",
            "user": "Employee",
            "user_name": m.getfullname(hn.get_username()),
            "date_time": datetime.now(),
            "collection_name": collection.full_name,
            "collection_id":candidate['_id'],
            "html_file_source": "interview_reviewed_list.html",
            "category":"User Profile"
        }

        # Insert log into MongoDB collection
        Log_table.insert_one(log_entry_confirmation_of_employment)  
   

        if officialinfoupdating.modified_count > 0:
            flash(f"Employment has been confirmed for {full_name}.", 'success')
        else:
            flash(f"Failed to confirm the employement for {full_name}.", 'error')

    # Redirect to the pre_hr_approved page
    return redirect(url_for('register.pre_hr_approved'))

@app.route('/pre_hr_approved')
def pre_hr_approved():
    loginid,portal_user_title = lm.get_user_info()
    check_login=hn.get_username()
    print(loginid)
    print(check_login)
    if check_login != loginid:
        loginid=""
    
    menu_items = lm.get_loginid_menulist()
    # Fetch only the users with 'Pre HR Approved List' status
    approved_users=list(CollectionOfOfficialInfo.find({'Status': 'Pre HR Approved'}).sort('_id', -1))
    return render_template('pre_hr_approved_list.html',users=approved_users,username=loginid, menu_list=menu_items)

@app.route('/extend_trial/<record_id>', methods=['POST'])
def extend_trial(record_id):
        new_trial_end_date = request.form['new_trial_end_date']
        result = collection.update_one(
            {'registration_number': record_id},
            {'$set': {'trial_end_date': new_trial_end_date}}
        )
        
        if result.modified_count > 0:
            flash('Trial period extended successfully!', 'success')
        else:
            flash('Failed to extend trial period.', 'error')
        
        return redirect(url_for('on_trial_list'))

@app.route('/send_joining_form', methods=['POST'])
def send_joining_form():
        reg_number = request.form.get('regNumber')
        full_name = request.form.get('fullName')
        email = request.form.get('email')
        confirm = request.form.get('confirm')

        if confirm == 'yes':
            # Insert the record into a new collection/table called 'Joining Form Sent List'
            data = {
                'registration_number': reg_number,
                'full_name': full_name,
                'email': email,
                'status': 'Joining Form Sent',
                'timestamp': datetime.now()
            }
            db_FusionBizCentral.joining_form_sent.insert_one(data)
            flash('Joining Form sent successfully!', 'success')
        else:
            flash('Action cancelled. No form was sent.', 'info')

        return redirect(url_for('show_joining_form_sent_list'))

@app.route('/joining_form_sent_list')
def show_joining_form_sent_list():
        # Fetch records from the 'Joining Form Sent List' collection
        joining_records = list(db_FusionBizCentral.joining_form_sent.find().sort('_id', -1))
        return render_template('joining_form_sent_list.html', records=joining_records)

@app.route('/portal_approval/<registration_number>', methods=['POST'])
def portal_approval(registration_number):
    # Fetch the user from the collection
    candidate = CollectionOfOfficialInfo.find_one({'Registration Number': registration_number})
    #name = candidate.get('USERNAME')

    if candidate:
        # Update the user's status to 'Active'
        officialinfoupdating2 = CollectionOfOfficialInfo.update_one(
            {'Registration Number': registration_number},
            {'$set': 
                {
                    'Status': 'Active'
                }
            }
        )

               # Update the user's status to 'Active'
        personalinfoupdating = CollectionOfPersonalInfo.update_one(
            {'User ID': registration_number},
            {'$set': 
                {
                    'Status': 'Active'
                }
            }
        )

        bankinfoupdating = CollectionOfBankDetails.update_one(
            {'User ID': registration_number},
            {'$set': 
                {
                    'Status': 'Active'
                }
            }
        )


        '''active_employee_data = {
                'registration_number': candidate['Registration Number'],
                'full_name': candidate['First Name'] + " " + candidate['Middle Name'] + " " + candidate['Last Name'],
                'email': candidate['Email Address'],
                'phone_number': candidate['Mobile Number'],
                'Status': 'Active',
                'date_joined': candidate['date_joined'],
                'elective_subject': candidate['elective_subject'],
                'organization': candidate['organization'],
                'location': candidate['location'],
                'department': candidate['department'],
                'designation': candidate['designation'],
                'shift': candidate['shift'],
        }

        # Insert into Active Employees collection
        ActiveEmployees.insert_one(active_employee_data)'''

        # Log entry for the confirmation of employment
        log_entry_confirmation_of_portal = {
            "action_title": "Form Submission",
            "official_id": hn.get_username(),
            "action": f"Confirmation of portal",
            #"detailed_info": f"Trial Period Assigned to the candidate.",
            "user": "Employee",
            "user_name": m.getfullname(hn.get_username()),
            "date_time": datetime.now(),
            "collection_name": collection.full_name,
            "collection_id":candidate['_id'],
            "html_file_source": "interview_reviewed_list.html",
            "category":"User Profile"
        }

        # Insert log into MongoDB collection
        Log_table.insert_one(log_entry_confirmation_of_portal) 

        if officialinfoupdating2.modified_count > 0:
            flash(f"Portal has been confirmed.", 'success')
        else:
            flash(f"Failed to confirm the employement.", 'error')

    # Redirect to the pre_hr_approved page
    return redirect(url_for('register.active_employees_list'))

@app.route('/active_employees_list')
def active_employees_list():
    loginid,portal_user_title = lm.get_user_info()
    check_login=hn.get_username()
    print(loginid)
    print(check_login)
    if check_login != loginid:
        loginid=""

    menu_items = lm.get_loginid_menulist()
    # Fetch only the users with 'Active' status
    active_employees_records = list(CollectionOfOfficialInfo.find({'Status': 'Active'}).sort('_id', -1))
    return render_template('active_employees_list.html', users=active_employees_records,username=loginid, menu_list=menu_items)

@app.route('/settings_SelectionProcess')
def selection_process():
    loginid,portal_user_title = lm.get_user_info()
    check_login=hn.get_username()
    print(loginid)
    print(check_login)
    if check_login != loginid:
        loginid=""
    # Count the documents where Status is 'Registered'
    registered_count = collection.count_documents({'Status': 'Registered'})

    # Count the documents where Status is 'Interview Scheduled'
    scheduled_count = collection.count_documents({'Status': 'Interview Scheduled'})

    # Count the documents where Status is 'Shortlisted'
    shortlisted_count = collection.count_documents({'Status': 'Shortlisted'})

    # Count the documents where Status is 'Selected'
    selected_count = collection.count_documents({'Status': 'Selected'})

    # Count the documents where Status is 'Active'
    active_count = CollectionOfOfficialInfo.count_documents({'Status': 'Active'})

    # Count the documents where Status is 'Inactive'
    inactive_count = CollectionOfOfficialInfo.count_documents({'Status': 'Inactive'})
    
    # Count the documents where Status is 'Trial Scheduled'
    trialperiod_count = collection.count_documents({'Status': 'Trial Scheduled'})

    # Count the documents where Status is 'Joined Form'
    joiningform_count = CollectionOfOfficialInfo.count_documents({'Status': 'Joined Form'})

    # Count the documents where Status is 'Pre HR Approved'
    prehr_count = CollectionOfOfficialInfo.count_documents({'Status': 'Pre HR Approved'})

    menu_items = lm.get_loginid_menulist()

    return render_template('settings_SelectionProcess.html', registered_count=registered_count,scheduled_count=scheduled_count, shortlisted_count=shortlisted_count,
                           selected_count=selected_count, active_count=active_count,inactive_count=inactive_count,trialperiod_count=trialperiod_count,
                           joiningform_count=joiningform_count,username=loginid, menu_list=menu_items, prehr_count=prehr_count)

#if __name__ == '__main__':
    #app.run(debug=True)

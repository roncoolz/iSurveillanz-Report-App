@app.route('/portal_approval/<registration_number>', methods=['POST'])
def portal_approval(registration_number):
    # Fetch the user from the collection
    candidate = CollectionOfOfficialInfo.find_one({'Registration Number': registration_number})
    name=candidate.get('USERNAME')

    if candidate:
        # Update the user's status to 'Active'
        officialinfoupdating = CollectionOfOfficialInfo.update_one(
            {'Registration Number': registration_number},
            {'$set': 
                {
                    'Status': 'Active'
                }
            }
        )

        active_employee_data = {
                'registration_number': candidate['registration_number'],
                'full_name': candidate['full_name'],
                'email': candidate['email'],
                'phone_number': candidate['phone_number'],
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
        ActiveEmployees.insert_one(active_employee_data)

        # Log entry for the confirmation of employment
        log_entry_confirmation_of_portal = {
            "action_title": "Form Submission",
            "official_id": hn.get_username(),
            "action": f"Confirmation of portal for {name}",
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

        if officialinfoupdating.modified_count > 0:
            flash(f"Portal has been confirmed.", 'success')
        else:
            flash(f"Failed to confirm the employement.", 'error')

    # Redirect to the pre_hr_approved page
    return redirect(url_for('register.active_employees_list'))




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

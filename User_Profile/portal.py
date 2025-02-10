import sys
import os
from flask import Flask, request, redirect, url_for, render_template, flash, jsonify, session, Blueprint
from flask_mail import Mail, Message
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app_settings')))
from App_Setting import collection, app, MongoClient, Log_table, HtmlFilesList,MenuBarList,PC_profile, CollectionOfPersonalInfo, CollectionOfOfficialInfo, CollectionOfBankDetails, PortalTitlesList, PortalPermission
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
from bson.objectid import ObjectId

# Initialize the Flask app
app = Blueprint('portal', __name__)

# Existing route for portal_titles_form
@app.route('/portal_titles_form', methods=['GET', 'POST'])
def portal_titles_form():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""

    # Fetch existing categories from MongoDB to populate the dropdown
    categories = list(PortalTitlesList.distinct('category'))  # Fetch distinct categories from the database
    categories.append('Other')  # Add the "Other" option to the list

    # Initialize form data (this will be populated after form submission)
    form_data = {
        'category': '',
        'manual_category': '',
        'portal_title': ''
    }

    # If it's a POST request, handle form submission
    if request.method == 'POST':
        category = request.form['category']
        manual_category = request.form.get('manual_category')  # This will get the manual category if it's filled
        portal_title = request.form['portal_title']

        # If "Other" was selected, use the manual category
        if category == 'Other' and manual_category:
            category = manual_category

        # Save the new category and portal title to MongoDB
        new_entry = {
            "category": category,
            "portal_title": portal_title
        }
        PortalTitlesList.insert_one(new_entry)  # Save to the database

        df=PortalPermission.find({})
        for d in df:
            filter = {'_id': d.get('_id')}
            update = {'$set': {portal_title:"No"}}
            PortalPermission.update_one(filter,update)

        # Set form data for re-population in the template
        form_data = {
            'category': category,
            'manual_category': manual_category,
            'portal_title': portal_title
        }

        # Log the action
        log_entry_new_portal_title = {
            "action_title": "Form Submission",
            "category": "Permission Profile",
            "user_name": m.getfullname(hn.get_username()),
            "action": f"new Portal Title added. {portal_title}",
            "date_time": datetime.now(),
            "collection_name": PortalTitlesList.full_name,
            "html_file_source": "portal_titles_form.html"
        }

        Log_table.insert_one(log_entry_new_portal_title)

        # Redirect to the same form to show the newly added category and title
        return redirect(url_for('portal.portal_titles_form'))

    menu_items = lm.get_loginid_menulist()
    return render_template('portal_titles_form.html', username=loginid, menu_list=menu_items, categories=categories, form_data=form_data)

# Portal HTML Linking Form Route
@app.route('/portal_html_linking', methods=['GET', 'POST'])
def portal_html_linking():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""

    menu_items = lm.get_loginid_menulist()
    # Fetch categories from PortalTitlesList collection
    categories = list(PortalTitlesList.distinct('category'))  # Fetch distinct categories

    # If form is submitted
    if request.method == 'POST':
        portal_title=request.form.get('portal_title')
        selected_files = request.form.getlist('selected_files')  # List of selected HTML file names
        # Update MongoDB based on selected checkboxes
        for file_name in selected_files:
            # Update the 'is_marked' field to 'Yes' for selected files
            PortalPermission.update_one(
                {'htmlName': file_name},
                {'$set': {str(portal_title): 'Yes'}}
            )

        # Also update files that were not selected (set 'is_marked' to 'No')
        all_files = list(PortalPermission.find({str(portal_title): {'$in': ['Yes', 'No']}}))
        all_selected_files = set(selected_files)

        for file in all_files:
            if file['htmlName'] not in all_selected_files:
                PortalPermission.update_one(
                    {'htmlName': file['htmlName']},
                    {'$set': {str(portal_title): 'No'}}
                )
        
        # Log the action
        log_entry_portal_html_linking = {
            "action_title": "Form Submission",
            "category": "Permission Profile",
            "user_name": m.getfullname(hn.get_username()),
            "action": f"Permission settings modification done for Portal Title :{portal_title} ",
            "date_time": datetime.now(),
            "collection_name": PortalTitlesList.full_name,
            "html_file_source": "portal_html_linking.html"
        }

        Log_table.insert_one(log_entry_portal_html_linking)

        # Redirect after submission to avoid resubmitting the form on refresh
        #return redirect(url_for('portal.portal_html_linking'))
        return redirect(url_for('portal.portal_html_linking', categories=categories, username=loginid, menu_list=menu_items))

    # Render the template for the form with the portal titles, categories, and HTML files
    return render_template('portal_html_linking_form.html',
                        username=loginid,
                        menu_list=menu_items,
                        categories=categories)

# Fetch portal titles based on selected category
@app.route('/get_portal_titles', methods=['GET'])
def get_portal_titles():
    category = request.args.get('category')
    
    # Fetch portal titles for the selected category from PortalTitlesList
    portal_titles = list(PortalTitlesList.find({'category': category}, {'portal_title': 1, '_id': 0}))

    # Extract only the portal titles (not the full documents)
    portal_titles = [title['portal_title'] for title in portal_titles]

    return jsonify(portal_titles)  # Return the list of portal titles as JSON

# New route to get distinct permission parameters
@app.route('/get_permission_parameters', methods=['GET'])
def get_permission_parameters():
    # Fetch distinct permission parameters from the PortalPermission collection
    permission_parameters = list(PortalPermission.distinct('permission_parameter'))
    return jsonify(permission_parameters)

@app.route('/html_file_entry_form', methods=['GET', 'POST'])
def html_file_entry_form():
    loginid, portal_user_title = lm.get_user_info()
    check_login = hn.get_username()
    if check_login != loginid:
        loginid = ""

    # Fetch existing categories from MongoDB to populate the dropdown
    #categories_html = list(HtmlFilesList.distinct('category_html'))  # Fetch distinct categories from the database
    #categories_html.append('Other')  # Add the "Other" option to the list

    # Initialize form data with empty values to avoid the 'undefined' error
    form_data_html = {
        'category_html': '',
        'manual_category_html': '',
        'html_file_name': ''
    }

    # If it's a POST request, handle form submission
    if request.method == 'POST':
        #category_html = request.form['category_html']
        manual_category_html = request.form.get('manual_category_html')  # This will get the manual category if it's filled
        html_file_name = request.form['html_file_name']
        permission_parameter = request.form['parameter']
        Action=request.form['action']
        menu1=request.form['menu_1']
        menu2=request.form["menu_2"]

        # If "Other" was selected, use the manual category
        '''if category_html == 'Other' and manual_category_html:
            category_html = manual_category_html'''

        # Save the new category and HTML file name to MongoDB
        '''new_entry_html = {
            "category_html": category_html,
            "html_file_name": html_file_name
        }
        HtmlFilesList.insert_one(new_entry_html)  # Save to the database'''

        menubar_entry = {
            "HTMLfile":html_file_name,
            "Menu1": menu1,
            "Menu2":menu2,
            "Parameter": permission_parameter,
            "action": Action
        }

        MenuBarList.insert_one(menubar_entry)  # Save to the database

        # Retrieve all portal titles from the 'PortalTitlesList' collection
        allportaltitles = PortalTitlesList.find()

        # Initialize a dictionary to store portal titles as keys with "No" as the value
        portal_titles_dict = {}

        # Iterate through all the portal titles retrieved from allportaltitles
        for portal_title in allportaltitles:
            # Assuming that each portal_title document has a 'title' field for the portal title
            title = portal_title.get('portal_title')  # Get the title from each portal entry

            # If title exists, assign "No" to it
            if title:
                portal_titles_dict[title] = "No"

        # Prepare the entry to insert into the 'PortalPermission' collection
        PortalPermission_entry = {
            "htmlName": html_file_name,
            "permission_parameter": permission_parameter,
            "action": Action,  # Customize the htmlName
            **portal_titles_dict  # Add the portal titles with "No" as their values
        }

        # Insert the document into the 'PortalPermission' collection
        PortalPermission.insert_one(PortalPermission_entry)

        # Optional: Print the inserted entry for debugging
        print("Insertion successful:", PortalPermission_entry)

        # Set form data for re-population in the template
        form_data_html = {
            'manual_category_html': manual_category_html,
            'html_file_name': html_file_name
        }

        # Log the action
        log_entry_new_html_file = {
            "action_title": "Form Submission",
            "category": "Permission Profile",
            "user_name": m.getfullname(hn.get_username()),
            "action": f"Permission settings modification done for Portal Title :{portal_title} ",
            "date_time": datetime.now(),
            "collection_name": PortalTitlesList.full_name,
            "html_file_source": "portal_html_linking.html"
        }

        Log_table.insert_one(log_entry_new_html_file)

        # Redirect to the same form to show the newly added category and file name
        return redirect(url_for('portal.html_file_entry_form'))

    # For GET request, pass the initialized form data (empty or previously filled)
    menu_items = lm.get_loginid_menulist()
    return render_template('html_file_entry_form.html', username=loginid, menu_list=menu_items, form_data_html=form_data_html)

'''@app.route('/get_checked_htmlfiles', methods=['GET'])
def get_checked_htmlfiles():
    category = request.args.get('category')
    portal_title = request.args.get('portal_title')
    #selected_files = request.args.get('htmlfiles')
    #checkedhtmlfiles1=list(PortalPermission.find({str(portal_title):"Yes"}))
    checkedhtmlfiles=list(PortalPermission.find({}))
    html_namess = [file['htmlName'] for file in checkedhtmlfiles if 'htmlName' in file]
    form_data = {
    'category': category,
    'portal_title': portal_title,
    'selected_files': html_namess
    }
    html_files_data = [{'htmlName': file['htmlName'], 'is_marked': True if file.get(str(portal_title)) == 'Yes' else False} for file in checkedhtmlfiles]
    print(portal_title)
    print(html_files_data)
    return jsonify(html_files_data)  # Return the list of portal titles as JSON'''

@app.route('/get_checked_htmlfiles', methods=['GET'])
def get_checked_htmlfiles():
    category = request.args.get('category')
    portal_title = request.args.get('portal_title')
    
    # Fetch HTML files from the 'PortalPermission' collection
    checkedhtmlfiles = list(PortalPermission.find({}))
    
    # Debug: Print the fetched data to inspect the structure
    print("Fetched HTML Files from PortalPermission:")
    for file in checkedhtmlfiles:
        print(file)  # Log each file document to see its fields

    # Generate the list of HTML file names with their associated 'permission_parameter' and 'action'
    html_files_data = []
    for file in checkedhtmlfiles:
        html_name = file.get('htmlName')
        
        # Debug: Print the permission_parameter and action to verify if they exist
        permission_parameter = file.get('permission_parameter', 'undefined')
        action = file.get('action', 'undefined')
        
        print(f"htmlName: {html_name}, permission_parameter: {permission_parameter}, action: {action}")
        
        if html_name:
            is_marked = True if file.get(str(portal_title)) == 'Yes' else False
            html_files_data.append({
                'htmlName': html_name,
                'permission_parameter': permission_parameter,
                'action': action,
                'is_marked': is_marked
            })

    return jsonify(html_files_data)  # Return the list of HTML files with their data as JSON


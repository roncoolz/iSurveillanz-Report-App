from flask import request, session
import socket
import sys
import os
#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '...', 'app_settings')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'app_settings')))
from App_Setting import CollectionOfOfficialInfo, MenuBarList, PortalPermission
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.', 'User_Profile')))
import methods.common_functions.common_function as hn

# Function to get the user login ID and Portal User Title
def get_user_info():
    #username = session.get('username')
    loginid = hn.get_username()
    # Fetch User Login ID and Portal User Title from the User Profile - Official Info collection
    user_info = CollectionOfOfficialInfo.find_one({'User Login ID': loginid})
    if user_info:
        portal_user_title = user_info.get('Portal User Title')
        return loginid, portal_user_title
    return None, None

# Function to check if a portal user has permission to view the HTML menu
def gethtmllist(portal_user_title):
    # Fetch the permission from the Portal Permission collection based on Portal User Title
    df = PortalPermission.find({portal_user_title: "Yes"})
    htmllist=[]
    if df:
        # Check if the permission for the specific html filename is 'Yes'
        for d in df:
            htmllist.insert(len(htmllist),d.get("htmlName"))
        return htmllist
    return False

# Function to get the menu details from the MenuBarList collection
def get_menu_items(htmlfilelist):
    # Fetch menu items from MenuBarList collection
    menuname1= list()
    menuname2= list()
    htmlfile=list()
    for j in htmlfilelist:
        datafetch = MenuBarList.find({"HTMLfile":j})
        for i in datafetch:
            menuname1.insert(len(menuname1), i.get("Menu1"))
            menuname2.insert(len(menuname2), i.get("Menu2"))
            htmlfile.insert(len(htmlfile), i.get("HTMLfile"))
    return menuname1,menuname2,htmlfile

def get_loginid_menulist():

    loginid,portal_user_title = get_user_info()
    htmllist= gethtmllist(portal_user_title)
    menuname1,menuname2,htmlfile = get_menu_items(htmllist)
    menu_items = list(zip(menuname1,menuname2, htmlfile))
    sorted_menu_items = sorted(menu_items, key=lambda x: x[0])

    # Group the sorted menu items by name1
    grouped_menu = {}

    for name1, name2, htmlfile in sorted_menu_items:
        if name1 not in grouped_menu:
            grouped_menu[name1] = []  # Create an empty list for new name1
        grouped_menu[name1].append((name2, htmlfile))  # Append (name2, htmlfile) to the list

    return grouped_menu

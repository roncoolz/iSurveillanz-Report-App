from flask import request, session
import socket
import sys
import os
#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '...', 'app_settings')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'app_settings')))
from App_Setting import PC_profile, CollectionOfOfficialInfo, MenuBarList, PortalPermission

def update_host_name(username):
    client_ip = request.remote_addr  # This is equivalent to Request.ServerVariables["REMOTE_ADDR"]

    try:
        # Resolve the IP address to a hostname
        hostname = socket.gethostbyaddr(client_ip)[0]

        # Check if the hostname contains a period
        if '.' in hostname.lower():
            # Split the hostname and keep the first token
            tokens = hostname.split('.')
            hostname = tokens[0]
        result = PC_profile.update_one({'PC Name': hostname},{'$set': {'Assigned User ID': username}})    

    except socket.herror:
        pass
        #return "Hostname could not be resolved."

def get_username():
    client_ip = request.remote_addr  # This is equivalent to Request.ServerVariables["REMOTE_ADDR"]
    result = None  # Initialize the result variable to None
    try:
        # Resolve the IP address to a hostname
        hostname = socket.gethostbyaddr(client_ip)[0]

        # Check if the hostname contains a period
        if '.' in hostname.lower():
            # Split the hostname and keep the first token
            tokens = hostname.split('.')
            hostname = tokens[0]
        # Retrieve the assigned user ID based on the hostname
        result = PC_profile.find_one({'PC Name': hostname}).get('Assigned User ID')

    except socket.herror:
        # Handle exception (e.g., if hostname cannot be resolved)
        pass

    finally:
        return result  # Return the result, which will be None if an exception occurred
    
def getportaltitle():
    client_ip = request.remote_addr  # This is equivalent to Request.ServerVariables["REMOTE_ADDR"]
    result = None  # Initialize the result variable to None
    try:
        # Resolve the IP address to a hostname
        hostname = socket.gethostbyaddr(client_ip)[0]

        # Check if the hostname contains a period
        if '.' in hostname.lower():
            # Split the hostname and keep the first token
            tokens = hostname.split('.')
            hostname = tokens[0]
        # Retrieve the assigned user ID based on the hostname
        UserID = PC_profile.find_one({'PC Name': hostname}).get('Assigned User ID')
        # Retrieve the portal title based on the user ID
        result = CollectionOfOfficialInfo.find_one({'User Login ID': UserID}).get('Portal User Title')

    except socket.herror:
        # Handle exception (e.g., if hostname cannot be resolved)
        pass

    finally:
        return result  # Return the result, which will be None if an exception occurred

import sys
import os

# Adjust sys.path to include the project root directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import App_Setting as a

def getfullname(official_id):
    # Find the document by official_id in the collection
    document = a.CollectionOfOfficialInfo.find_one({"User Login ID": official_id})
    
    # Check if the document was found
    if document:
        # Return the full_name if found, or a default message if full_name is missing
        fn=document.get('First Name')
        mn=document.get('Middle Name')
        sn=document.get('Last Name')
        return str(fn)+' '+str(mn)+' '+str(sn)
    else:
        # If no document was found, return an appropriate message
        return "Official ID not found"

# Example usage (for testing purposes):
# print(getfullname('some_official_id'))

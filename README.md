# iSurveillanz-Report-App
(Web Application Overview)

This document provides an overview of a web application developed using Flask, MongoDB, and Jinja2 templates. The application serves as a system for entering, processing, and reporting incident details, along with data analysis and management of various settings and profiles. It is designed for use in organizations that manage incidents and need to generate reports for clients and internal purposes.


Key Features
1. User Authentication and Login System: 
Users can log in to the application via a login page, which authenticates credentials (username and password) against a MongoDB collection of user data (CollectionOfOfficialInfo).
Upon successful login, users are redirected to a menu bar with options based on their roles and permissions. If login fails, an error message is displayed.

2. Incident Details Entry and Reporting: 
Users can enter incident details using a form where information is captured and processed. This includes specific attributes of the incident, client, and PC (Personal Computer) assignments.
After entering the data, it can be processed and reported to the respective clients or internal teams.
The system integrates with MongoDB to store incident data and relevant information in various collections (e.g., incident_sentences_collection, client_collection).

3. Profile Management: 
The application manages several types of profiles, including:
Client Profile: Information about clients, including department and camera information.
PC Profile: Details about user PCs, including the PC name, title, and assigned users.
Organization Profile: Information about the organization, including general settings and configurations.
Profiles can be updated or viewed from the settings page.

4. Settings and Permissions: 
The application allows administrators to configure various settings, such as managing user permissions, client profiles, organization settings, and more.
Specific settings pages allow for updating Block PC Profiles, Client Profiles, Organization Profiles, and other administrative configurations.

5. Data Analysis and Reporting: 
Once incidents are reported, the application provides a robust system for viewing and analyzing logs and reports.
Logs are stored in a MongoDB collection (Log_table) and can be filtered based on various criteria such as category, action, and user. The logs are displayed in a tabular format, with options to filter and sort the data.
The logs provide insights into the actions taken on the system, including who performed specific actions, what changes were made, and when.

6. Dynamic Menu and Permissions: 
Based on the user’s role and login credentials, the application dynamically generates a menu for the user, displaying relevant options and ensuring access control.
Users without appropriate permissions are not granted access to restricted areas of the application.

7. Interactive Forms and Report Generation: 
The application supports various interactive forms for entering incident details, selecting reports, and viewing data.
Report generation allows for detailed data analysis, enabling users to filter reports based on different parameters (e.g., category, collection, user).
The system also supports the creation of different report forms that cater to various use cases.

8. MongoDB Integration: 
MongoDB is used as the backend database, storing user information, incident data, logs, and profile details in various collections. This allows for scalable and efficient data storage and retrieval.
The application interfaces with MongoDB using PyMongo, performing operations such as querying, updating, and deleting records.

9. Log Table and Data Auditing: 
Every action performed by users (such as entering incident details or updating profiles) is logged in the Log_table collection.
The logs provide detailed information, including the category of action, the user who performed it, the timestamp, and the collection name affected.
This feature enables auditing and traceability of user activities within the system.

10. HTML Form Management: 
The application allows users to enter data through HTML forms and manage those entries dynamically. This is facilitated by templates rendered through Flask’s Jinja2 engine.
Users can upload and manage incident files, configure custom settings, and generate various reports.


Application Workflow
1. Login:
Users log into the application, and the system authenticates their credentials.
Once authenticated, the system redirects users to the main menu based on their roles and permissions.

2. Incident Data Entry:
Users can enter detailed incident data, including descriptions, client-related information, and PC assignments.
The data is stored in MongoDB for future processing and reporting.

3. Data Processing:
After incident data is entered, it can be processed according to business rules, and reports are generated for the respective clients or internal stakeholders.

4. Report Generation:
Users can generate reports based on entered incidents, with the option to filter and analyze the data according to categories and other parameters.

5. Log and Data Auditing:
All system actions are logged in MongoDB. Users can view logs and perform auditing on activities, ensuring transparency and accountability.

6. Settings and Profile Management:
Administrators can manage user profiles, client profiles, and organization settings. This includes managing permissions, viewing logs, and updating system settings.


Conclusion
This web application is a comprehensive tool designed for managing incident data, generating reports, and analyzing system actions. With its robust integration with MongoDB, dynamic forms, and interactive user interface, it provides a seamless experience for users to enter and process data, manage profiles, and access detailed reports. The application’s audit trail and permissions system ensure data integrity and security, making it an ideal solution for organizations that need to manage incident details and generate reports efficiently.



Important Note:

Please take a look in the MongoDB folder. You will see two files that you can download and save to your own MongoDB server.

Use the following credentials:

Login: ISEMP514AA

Password: btvvrz

Make sure to change your PC name to 'DESKTOP-CRAD02', as there is a section in the code that retrieves the PC name and saves the database with your name and PC name.

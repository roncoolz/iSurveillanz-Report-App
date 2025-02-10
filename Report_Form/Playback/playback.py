from flask import Flask, render_template, request, redirect, flash, url_for, jsonify
from App_Setting import playbackcollection, cameracollection
from bson import ObjectId  # Ensure ObjectId is imported

app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.route('/add_playback', methods=['GET', 'POST'])
def add_playback():
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
    return render_template('playback.html', client_names=client_names)


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
    # Fetch playback records sorted by Serial Number
    playbacks = list(playbackcollection.find().sort("Serial Number", 1))
    pc_names = playbackcollection.distinct("PC Name")
    return render_template('table_playback.html', playbacks=playbacks, pc_names=pc_names)


'''@app.route('/debug_playback', methods=['GET'])
def debug_playback():
    data = list(playbackcollection.find().sort("Serial Number", 1))
    return jsonify(data)'''


@app.route('/update_playback_sequence', methods=['POST'])
def update_playback_sequence():
    updated_order = request.json.get('order')

    for new_serial, playback_id in enumerate(updated_order, start=1):
        playbackcollection.update_one(
            {"_id": ObjectId(playback_id)},  
            {"$set": {"Serial Number": new_serial}}
        )

    return jsonify({"status": "success", "message": "Sequence updated successfully"})


if __name__ == '__main__':
    app.run(debug=True)

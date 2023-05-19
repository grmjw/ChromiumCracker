from flask import Flask, request, jsonify
import os
import json

app = Flask(__name__)

# Create a folder to store JSON files if it doesn't exist
data_folder = "stolen_data"
os.makedirs(data_folder, exist_ok=True)

# set the route for the http POST request 
@app.route('/send/json', methods=['POST'])

# method that receives the json from the request
def receive_json():
    data = request.get_json()  # Get JSON data from the request
    # Process the received data here
    print(data)  # Example: print the received data

    # Generate a unique filename for the JSON file
    filename = f"data_{len(os.listdir(data_folder)) + 1}.json"
    file_path = os.path.join(data_folder, filename)

    # Save the JSON data to a file
    with open(file_path, 'w') as f:
        json.dump(data, f)

    return 'Received JSON data successfully'

# Set the route for the page to view received JSON data
@app.route('/view')
def view_data():
    json_files = os.listdir(data_folder)
    data = []

    # Read the JSON data from each file
    for filename in json_files:
        file_path = os.path.join(data_folder, filename)
        with open(file_path, 'r') as f:
            json_data = json.load(f)
            data.append(json_data)

    return jsonify(data) if data else 'No JSON data received yet'

# Set the route to fetch JSON data from the folder
@app.route('/json_data')
def fetch_data_from_folder():
    json_files = os.listdir(data_folder)
    data = []

    # Read the JSON data from each file
    for filename in json_files:
        file_path = os.path.join(data_folder, filename)
        with open(file_path, 'r') as f:
            json_data = json.load(f)
            data.append(json_data)

    return jsonify(data) if data else 'No JSON data available in the folder'

# run the web app
if __name__ == '__main__':
    app.run()

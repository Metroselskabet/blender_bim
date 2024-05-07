import bpy
import os
import ifcopenshell
from blenderbim.bim.module.tester import *
import json
import csv

"""
Definitions/functions
"""
def get_text_file_paths(root_folder):
    text_file_paths = []

    for foldername, subfolders, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename.endswith('.ifc'):
                file_path = os.path.join(foldername, filename)
                text_file_paths.append(file_path)

    return text_file_paths

def execute_ifc_tester(ifc_file_path, ids_file_path):
   
   # Set IfcTesterProperties.specs to ifc_file_path
    bpy.ops.bim.select_ifctester_ifc_file=ifc_file_path
    bpy.ops.bim.select_specs=ids_file_path
    bpy.context.scene.IfcTesterProperties.specs = ids_file_path
    bpy.context.scene.IfcTesterProperties.ifc_file=ifc_file_path
    
    # Check if ids_file_path exists
    if not os.path.exists(ids_file_path):
        print(f"File does not exist: {ids_file_path}")

    # Set other IfcTesterProperties
    bpy.context.scene.IfcTesterProperties.generate_html_report = True

    # Execute the operator
    bpy.ops.bim.execute_ifc_tester()

def move_and_rename_html_report(ids_file_path,ifc_file_path, new_base_folder):
    try:
        # Extract the immediate subfolder from the IFC file path
        _, immediate_subfolder = os.path.split(os.path.dirname(ifc_file_path))

        # Construct the new subfolder path under 'reports'
        new_subfolder_path = os.path.join(new_base_folder, 'reports', immediate_subfolder)

        # Create the new subfolder if it doesn't exist
        os.makedirs(new_subfolder_path, exist_ok=True)

        # Construct the new path with the specified subfolder
        new_path = os.path.join(new_subfolder_path, os.path.basename(ifc_file_path).replace(".ifc", ".json"))

        # Move the HTML report file
        os.rename(ids_file_path.replace(".ids", ".ids.json"), new_path)

        print(f"File moved and renamed: {ifc_file_path.replace('.ifc', '.json')} -> {new_path}")
        return new_path
    
    except OSError as e:
        print(f"Error moving/renaming file: {e}")


"""
User imported variables
"""
ids_file_path = r'YOUR_IDS_FILEPATH'
ifc_folder_path = r'YOUR_IFC_FOLDER'
new_base_folder = r'YOUR_OUTPUT_FOLDER'

"""
Ifc script
"""

result = get_text_file_paths(ifc_folder_path)
# Function to extract failed entities data
def extract_failed_entities(req):
    failed_entities = req.get('failed_entities', [])
    return {entity['global_id']: entity for entity in failed_entities}
for ifc_file_path in result:
    # if 'STA-Prb' in ifc_file_path:
        print(ifc_file_path)
        execute_ifc_tester(ifc_file_path, ids_file_path)
        json_file_path = move_and_rename_html_report(ids_file_path,ifc_file_path, new_base_folder)

        csv_file_path =json_file_path.replace(".json",".csv")
        # Read the JSON data from the file
          # Read the JSON data from the file
        with open(json_file_path, 'r') as json_file:
            json_data = json.load(json_file)

        # Extract 'description', 'status', and 'failed_entities'
        data_to_append = {}
        descriptions = set()  # Initialize the descriptions set
        for spec in json_data['specifications']:
            for req in spec['requirements']:
                description = req['description']
                status = req['status']
                global_id = None
                failed_entities = extract_failed_entities(req)

                for entity_global_id, entity_data in failed_entities.items():
                    descriptions.add(description)
                    data_to_append.setdefault(entity_global_id, {}).setdefault(description, 'Fail')
                
                if not failed_entities:
                    global_id = 'N/A'
                    descriptions.add(description)
                    data_to_append.setdefault(global_id, {}).setdefault(description, 'Pass')

        # Fill empty values with "Pass" for each global_id
        for global_id, data in data_to_append.items():
            for desc in descriptions:
                if desc not in data:
                    data[desc] = 'Pass'

        # Remove rows with 'N/A' global_id
        data_to_append.pop('N/A', None)

        # Write data to the CSV file
        with open(csv_file_path, 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            # Create header
            header = ['global_id'] + sorted(descriptions)  # Sort to ensure consistency
            writer.writerow(header)  # Write header
            
            # Write rows
            for global_id, data in data_to_append.items():
                row = [global_id]
                row += [data.get(desc, '') for desc in header[1:]]
                writer.writerow(row)
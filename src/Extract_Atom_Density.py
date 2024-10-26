"""
Atom Density Extraction and Processing Script

This script processes atom density data from an MCNP output file and writes the results to an Excel file. 
It supports extracting data for either nonactinide or actinide inventories.

Dependencies:
- Python 3
- pandas
- xlsxwriter
- multiprocessing

Installation:
1. Install Python 3 if not already installed.
2. Install the required Python libraries using pip:

    pip install pandas xlsxwriter

Usage:
1. Prepare the Input File:
   Ensure you have an MCNP output file with atom density data. Specify the file path in the script.

2. Configure the Script:
   Update the following variables in the script:
   
   - filename: Path to your MCNP output file.
   - isotopes: List of isotopes to process.
   - output_filename: Path to the output Excel file.
   - inventory_type: Type of inventory to search for ('nonactinide' or 'actinide').

3. Run the Script:
   Execute the script to process the data and generate the Excel file.

   python script.py

4. Output:
   The output will be an Excel file with separate sheets for each isotope, containing the average atom density data for each ring.

Script Details:
- ring_ranges: Dictionary defining the materials for each ring.
- extract_atom_density: Function to extract atom density values for a specified material and isotope.
- calculate_average_density: Function to calculate the average density for each time step across all materials in a ring.
- process_isotope_data: Function to process atom density data for a given isotope across all rings.
- write_to_excel: Function to write the processed data to an Excel file with separate sheets for each isotope.

Example Configuration:

filename = 'MCNP_Results.o'  # Ensure the correct file path
isotopes = ['36085', '38090']
output_filename = 'DATA.xlsx'
inventory_type = 'nonactinide'  # Change to 'actinide' as needed

This script is designed to be flexible and handle different types of inventories, making it useful for various analyses involving atom density data. Adjust the configuration as needed for your specific use case.
"""

import re
import pandas as pd
from multiprocessing import Pool

# Define the ring material ranges
ring_ranges = {
    'Ring B': ['material 10221', 'material 10222', 'material 10223', 'material 10224', 'material 10225', 'material 10241'],
    'Ring C': ['material 10226', 'material 10227', 'material 10228', 'material 10242', 'material 10229', 'material 10230', 'material 10231', 'material 10232', 'material 10233', 'material 10289', 'material 10235', 'material 10236'],
    'Ring D': ['material 10243', 'material 9162', 'material 10244', 'material 9161', 'material 6607', 'material 10237', 'material 10238', 'material 10239', 'material 10240', 'material 10267', 'material 10284', 'material 10285', 'material 10286', 'material 10287', 'material 10288', 'material 10290', 'material 10291', 'material 9096'],
    'Ring E': ['material 9097', 'material 9098', 'material 9099', 'material 9100', 'material 9102', 'material 9103', 'material 9104', 'material 9105', 'material 9106', 'material 9107', 'material 9108', 'material 9109', 'material 9110', 'material 9111', 'material 9112', 'material 9101', 'material 9113', 'material 9114', 'material 9127', 'material 9116', 'material 9117', 'material 9118', 'material 10292', 'material 9145'],
    'Ring F': ['material 9130', 'material 9121', 'material 9120', 'material 9131', 'material 9146', 'material 9132', 'material 9129', 'material 9126', 'material 9133', 'material 9134', 'material 9135', 'material 9125', 'material 9128', 'material 9136', 'material 9147', 'material 9137', 'material 9124', 'material 9122', 'material 9138', 'material 9148', 'material 9145', 'material 9139', 'material 9140', 'material 10234', 'material 9141', 'material 9145', 'material 9142', 'material 9143', 'material 9119', 'material 9144'],
    'Ring G': ['material 9154', 'material 9156', 'material 9144', 'material 9157', 'material 9158', 'material 9159', 'material 9153', 'material 9152', 'material 9151', 'material 9150', 'material 9149']
}

def extract_atom_density(lines, material, isotope, inventory_type):
    """
    Extract atom density values for a specified material and isotope from the file lines.

    Args:
    lines (list): List of lines from the input file.
    material (str): The material identifier.
    isotope (str): The isotope identifier.
    inventory_type (str): Type of inventory to search for ('nonactinide' or 'actinide').

    Returns:
    list: List of extracted atom density values.
    """
    # Compile the regex pattern to match the start of the material section
    material_pattern = re.compile(rf'{inventory_type} inventory for {material}')
    
    # Compile the regex pattern to match the isotope data
    isotope_pattern = re.compile(rf'\s+\d+\s+{isotope}\s+([\d.E+-]+)\s+([\d.E+-]+)\s+([\d.E+-]+)\s+([\d.E+-]+)\s+([\d.E+-]+)\s+([\d.E+-]+)\s+')
    
    # Compile the regex pattern to match the start of a new material section
    new_material_pattern = re.compile(rf'{inventory_type} inventory for material')
    
    extracting = False
    atom_density_values = []

    for line in lines:
        if extracting:
            if new_material_pattern.search(line) and not material_pattern.search(line):
                # Stop extracting if we reach the start of a new material section that is not the same material
                extracting = False
            match = isotope_pattern.match(line)
            if match:
                # Extract the "atom den." value (4th group in the match)
                atom_density = float(match.group(4))
                atom_density_values.append(atom_density)
        elif material_pattern.search(line):
            # Start extracting when we find the material section
            extracting = True
    
    return atom_density_values

def calculate_average_density(ring_data):
    """
    Calculate the average density for each time step across all materials in a ring.

    Args:
    ring_data (list): List of lists containing atom density values for each material in the ring.

    Returns:
    list: List of average densities for each time step.
    """
    # Calculate the average density for each time step
    average_density = [sum(step_data) / len(step_data) for step_data in zip(*ring_data)]
    return average_density

def process_isotope_data(args):
    """
    Process atom density data for a given isotope across all rings.

    Args:
    args (tuple): A tuple containing the filename, isotope, ring ranges, and inventory type.

    Returns:
    tuple: A tuple containing the isotope and a dictionary of average densities by ring.
    """
    filename, isotope, ring_ranges, inventory_type = args
    with open(filename, 'r') as file:
        lines = file.readlines()

    data = {}
    for ring, materials in ring_ranges.items():
        ring_data = []
        for material in materials:
            atom_density_values = extract_atom_density(lines, material, isotope, inventory_type)
            ring_data.append(atom_density_values)
        
        # Calculate the average density for the ring
        average_density = calculate_average_density(ring_data)
        data[ring] = average_density
    
    return isotope, data

def write_to_excel(filename, ring_ranges, isotopes, output_filename, inventory_type):
    """
    Write the processed data to an Excel file with separate sheets for each isotope.

    Args:
    filename (str): Path to the input file.
    ring_ranges (dict): Dictionary of ring ranges with materials.
    isotopes (list): List of isotopes to process.
    output_filename (str): Path to the output Excel file.
    inventory_type (str): Type of inventory to search for ('nonactinide' or 'actinide').
    """
    writer = pd.ExcelWriter(output_filename, engine='xlsxwriter')
    
    pool = Pool()
    args = [(filename, isotope, ring_ranges, inventory_type) for isotope in isotopes]
    results = pool.map(process_isotope_data, args)
    
    for isotope, data in results:
        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name=isotope, index=False)
    
    writer.save()

# Example usage
filename = 'MCNP_Results.o'  # Ensure the correct file path
isotopes = ['36085', '38090']
output_filename = 'DATA.xlsx'
inventory_type = 'nonactinide'  # Change to 'actinide' as needed

write_to_excel(filename, ring_ranges, isotopes, output_filename, inventory_type)

print(f"Data written to {output_filename}")


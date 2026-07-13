"""
Script to Extract and Store Nuclide Concentrations

This script reads depletion results from an 'depletion_results.h5' file and processes
the concentration of specified nuclides over time. It performs the following tasks:
1. Extracts the nuclide concentrations for a range of materials and sums them.
2. Converts the time from seconds to days.
3. Writes the extracted and processed data to .txt files, with each file corresponding to a different nuclide.
4. Writes the same data to an Excel file, with each nuclide's data in a separate sheet.

Dependencies:
- numpy
- openmc.deplete
- pandas
- xlsxwriter

Usage:
1. Ensure you have the required dependencies installed.
2. Specify the nuclides of interest in the 'nuclide_names' list.
3. Specify the path to the depletion results file in the 'results_file' variable.
4. Specify the type of density data you want to extract: 'atoms' or 'mass' in the `density_type` variable.
5. If you want to extract mass densities, ensure that you are using OpenMC version 14 or higher.
6. Run the script to generate the .txt and Excel files with the nuclide concentration data.
"""

def write_nuclide_concentration(results, nuclide_names, density_type='atoms', decimal_places=5):
    # Create a Pandas Excel writer using XlsxWriter as the engine
    excel_writer = pd.ExcelWriter('nuclide_concentrations.xlsx', engine='xlsxwriter')

    for nuclide_name in nuclide_names:
        nuclide_concentration_total = None
        for material_id in range(14, 115):
            if density_type == 'atoms':
                time, nuclide_concentration_material = results.get_atoms(str(material_id), nuclide_name, nuc_units='atom/b-cm')
            elif density_type == 'mass':
                time, nuclide_concentration_material = results.get_mass(str(material_id), nuclide_name, mass_units='g')
            else:
                raise ValueError("density_type must be either 'atoms' or 'mass'")

            if nuclide_concentration_total is None:
                nuclide_concentration_total = nuclide_concentration_material
            else:
                nuclide_concentration_total += nuclide_concentration_material

        # Convert time from seconds to days
        time_in_days = time / (24 * 60 * 60)

        # Adjust total concentration for atom densities
        if density_type == 'atoms':
            nuclide_concentration_total = nuclide_concentration_total / 101

        # Prepare the data with custom formatting
        formatted_data = np.column_stack((time_in_days, nuclide_concentration_total)).astype(float)

        # Define the header
        header = f"Time [d]\t{nuclide_name} ({'atom/b-cm' if density_type == 'atoms' else 'g'})"

        # Construct the output file name based on the nuclide name
        output_file = f"{nuclide_name}VsBurnup.txt"

        # Save the formatted data to the dynamically generated output file
        np.savetxt(output_file, formatted_data, delimiter='\t', header=header, comments='')

        # Create a DataFrame for the Excel file
        df = pd.DataFrame(formatted_data, columns=['Time [d]', f'{nuclide_name} ({"atom/b-cm" if density_type == "atoms" else "g"})'])

        # Write the DataFrame to a sheet named after the nuclide
        df.to_excel(excel_writer, sheet_name=nuclide_name, index=False)

    # Save the Excel file
    excel_writer.save()

nuclide_names = ['U234', 'U235', 'U238', 'Np237', 'Pu238', 'Pu239', 'Pu240', 'Pu241', 'Pu242', 'Am241', 'Am243', 'Cm244', 'Cm245']
#nuclide_names = ['I131', 'Ba140', 'Ce141', 'Nb95', 'Sr89', 'Ce144', 'Ru106', 'Pm147', 'Tc99', 'Cs135', 'Pd107', 'I129', 'Cs137', 'Sr90', 'Xe135', 'Sm149']
results_file = "../depletion_results.h5"
density_type = 'atoms'  # Change to 'mass' if you want mass densities
results = openmc.deplete.Results(results_file)
write_nuclide_concentration(results, nuclide_names, density_type)


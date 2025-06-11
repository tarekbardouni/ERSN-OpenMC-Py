import os
import sys
import os.path
import PyQt5
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
#from PyQt5.QtWidgets import QMessageBox
import datetime
import shutil
import subprocess
from pathlib import Path
#from PyQt5.QtGui import QFont, QTextCharFormat, QBrush
from src.PyEdit import TextEdit, NumberBar, tab, lineHighlightColor
import numpy as np
from matplotlib import pyplot as plt, cm
from matplotlib import colors
from matplotlib.ticker import ScalarFormatter
from matplotlib.ticker import FuncFormatter

import pandas as pd
import glob
import h5py
from PyQt5.QtWidgets import (QPlainTextEdit, QWidget, QVBoxLayout, QApplication, QFileDialog, QMessageBox, QLabel, QCompleter, 
                            QHBoxLayout, QTextEdit, QToolBar, QComboBox, QAction, QLineEdit, QDialog, QPushButton, QSizePolicy, 
                            QToolButton, QMenu, QMainWindow, QInputDialog, QColorDialog, QStatusBar, QSystemTrayIcon)
from PyQt5.QtGui import (QIcon, QPainter, QTextFormat, QColor, QTextCursor, QKeySequence, QClipboard, QTextDocument, 
                            QPixmap, QStandardItemModel, QStandardItem, QCursor, QFontDatabase)
from PyQt5.QtCore import (Qt, QVariant, QRect, QDir, QFile, QFileInfo, QTextStream, QSettings, QTranslator, QLocale, 
                            QProcess, QPoint, QSize, QCoreApplication, QStringListModel, QLibraryInfo)
from PyQt5 import QtPrintSupport
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtGui import QTextOption

from PyQt5.QtCore import Qt, pyqtSignal

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

def global_exception_handler(exc_type, exc_value, exc_traceback):
    """
    Custom exception handler to display unhandled exceptions in a dialog.
    """
    if issubclass(exc_type, KeyboardInterrupt):
        # Let the interpreter handle KeyboardInterrupt (e.g., Ctrl+C).
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    # Create an error message dialog
    error_message = f"Unhandled Exception:\n{exc_value}"
    QMessageBox.critical(None, "Application Error", error_message)

    # Optionally log the exception
    with open("error_log.txt", "a") as f:
        import traceback
        f.write("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))

# Assign the custom exception handler
sys.excepthook = global_exception_handler

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

iconsize = QSize(24, 24)
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('max_colwidth', 30)

try:
    import openmc
except:
    pass

class TallyDataProcessing(QtWidgets.QMainWindow):
    from src.func import resize_ui, showDialog

    def __init__(self, Directory, Sp, DeplRes, Chain, parent=None):
        super(TallyDataProcessing, self).__init__(parent)
        uic.loadUi("src/ui/TallyDataProcessing.ui", self)
        try:
            from openmc import __version__
            self.openmc_version = int(__version__.split('-')[0].replace('.', ''))
        except:
            self.openmc_version = 0

        self.FILTER_TYPES = ['UniverseFilter', 'MaterialFilter', 'CellFilter', 'CellFromFilter', 'CellBornFilter',
                        'CellInstanceFilter', 'CollisionFilter', 'SurfaceFilter', 'MeshFilter', 'MeshSurfaceFilter',
                        'EnergyFilter', 'EnergyoutFilter', 'MuFilter', 'PolarFilter', 'AzimuthalFilter',
                        'DistribcellFilter', 'DelayedGroupFilter', 'EnergyFunctionFilter', 'LegendreFilter',
                        'SpatialLegendreFilter', 'SphericalHarmonicsFilter', 'ZernikeFilter', 'ZernikeRadialFilter',
                        'ParticleFilter', 'TimeFilter']
        self.Filter_names = ['']
        self.Display = False
        self.Tallies = {}
        self.Mesh_xy_RB.hide()
        self.Mesh_xz_RB.hide()
        self.Mesh_yz_RB.hide()
        self.spinBox.hide()
        self.spinBox_2.hide()
        self.Normalizing_GB.hide()
        self.buttons = [self.xLog_CB, self.yLog_CB, self.Add_error_bars_CB, self.xGrid_CB, self.yGrid_CB, self.MinorGrid_CB, self.label_2, self.label_3]
        self.buttons_Stack = [self.label_5, self.label_6, self.label_7, self.row_SB, self.col_SB]
        for elm in self.buttons: 
            elm.setEnabled(False)
        for elm in self.buttons_Stack: 
            elm.setEnabled(False)
        self.Graph_Layout_CB.setEnabled(False)        
        # add new editor for output window
        self.editor = TextEdit()
        self.editor.setWordWrapMode(QTextOption.NoWrap)
        self.numbers = NumberBar(self.editor)
        layoutH7 = QHBoxLayout()
        layoutH7.addWidget(self.numbers)
        layoutH7.addWidget(self.editor)    
        self.gridLayout_18.addLayout(layoutH7, 0, 0)
        # add editor to second tab 
        self.editor1 = TextEdit()
        self.editor1.setWordWrapMode(QTextOption.NoWrap)
        self.numbers1 = NumberBar(self.editor1)
        layoutH7 = QHBoxLayout()
        layoutH7.addWidget(self.numbers1)
        layoutH7.addWidget(self.editor1)  
        self.gridLayout_5.addLayout(layoutH7, 0, 0)  
        # add editor to third tab (depletion results)
        self.editor2 = TextEdit()
        self.editor2.setWordWrapMode(QTextOption.NoWrap)
        self.numbers2 = NumberBar(self.editor2)
        layoutH7 = QHBoxLayout()
        layoutH7.addWidget(self.numbers2)
        layoutH7.addWidget(self.editor2) 
        self.gridLayout_45.addLayout(layoutH7, 0, 0)
        self.Y2Label_CB.setEnabled(False)
        self.Y2Label_CB.setChecked(False)
        self.y2Grid_CB.setEnabled(False)
        self.Curve_y2Label.clear()
        self.Curve_y2Label.setEnabled(False)
        self.YSecondary = False
        self.xgrid = False; self.ygrid = False; self.y2grid = False
        self.which_axis = 'none'
        self.which_grid = 'both'
        self.resize_ui()
        self.Norm_Bins_comboBox = CheckableComboBox()
        self.Norm_Bins_comboBox.addItem('Check item')
        self.gridLayout_Norm.addWidget(self.Norm_Bins_comboBox)
        self.Norm_Bins_comboBox.model().item(0).setEnabled(False)
        self.Norm_Bins_comboBox.model().item(0).setCheckState(Qt.Unchecked)
        # Create time_steps combobox
        self.Time_steps_comboBox = CheckableComboBox()
        self.Time_steps_comboBox.addItems(['Check step', 'All bins'])
        self.Time_steps_GL.addWidget(self.Time_steps_comboBox)
        # Create nuclides combobox
        self.Nuclides_ComboBx = CheckableComboBox()
        self.Nuclides_ComboBx.addItems(['Check nuclide', 'All bins'])
        self.Nuclide_GL.addWidget(self.Nuclides_ComboBx)
        # +++++++++++++++++++++++
        self.Tally_name_LE.setPlaceholderText("Name")
        self.root = QFileInfo.path(QFileInfo(QCoreApplication.arguments()[0]))
        self.openPath = ""
        self.dirpath = QDir.homePath() + "/Documents/tmp/"
        self.filename = ""
        #self.MaxRecentFiles = 15
        self.recentFileActs = []
        self.settings = QSettings("PyEdit", "PyEdit")
        #self.createActions()
        # +++++++++++++++++++++++
        if not self.score_plot_PB.isEnabled():
            self.score_plot_PB.setToolTip('If filter bins or selected nuclides or selected score change, press select button first')
        self.scores_display_PB.setToolTip('Press this button before ploting!')
        #self._initButtons()
        sys.stdout = EmittingStream(textWritten=self.normalOutputWritten)
        #sys.stderr = EmittingStream(textWritten=self.normalOutputWritten)
        
        self.directory = Directory
        if Sp != '':
            if os.path.isfile(Sp): 
                self.sp_file = Sp
                self.lineEdit.setText(self.sp_file)
                self.Get_data_from_SP_file()
            else:
                self.sp_file = None

        if DeplRes != '':
            if os.path.isfile(DeplRes): 
                self.Depl_Res_file = DeplRes
                self.Depl_Res_LE.setText(self.Depl_Res_file)
                self.Get_Data_from_Depl_Res_file()
            else:
                self.Depl_Res_file = None
        if Chain != '':
            if os.path.isfile(self.directory + '/' + Chain):
                self.Chain = self.directory + '/' + Chain
            else:
                self.Chain = None
                self.showDialog('Warning', 'No depletion chain file was specified!')
        else:
            self.Chain = None

        self.Get_Summary_File()

        self.Omit_Blank_Graph_CB.setEnabled(False)

        # Possible scores
        self.FlUX_SCORES = ['flux']
        self.FlUX_UNIT = ' particle-cm per source particle'
        self.REACTION_SCORES = ['absorption', 'elastic', 'fission', 'scatter', 'total', '(n,elastic)', '(n,2nd)', '(n,2n)', '(n,3n)',
                                '(n,na)', '(n,n3a)', '(n,2na)', '(n,3na)', '(n,np)', '(n,n2a)', '(n,2n2a)', '(n,nd)',
                                '(n,nt)', '(n,n3He)', '(n,nd2a)', '(n,nt2a)', '(n,4n)', '(n,2np)', '(n,3np)', '(n,n2p)',
                                '(n,n*X*)', '(n,nc)', '(n,gamma)', '(n,p)', '(n,d)', '(n,t)', '(n,3He)', '(n,a)',
                                '(n,2a)', '(n,3a)', '(n,2p)', '(n,pa)', '(n,t2a)', '(n,d2a)', '(n,pd)', '(n,pt)', '(n,da)',
                                'coherent-scatter', 'incoherent-scatter', 'photoelectric', 'pair-production', 'Arbitrary integer']
        self.REACTION_UNIT = ' reactions per source particle'
        self.PARTICLE_PRODUCTION_SCORES = ['delayed-nu-fission', 'prompt-nu-fission', 'nu-fission', 'nu-scatter',
                                           'H1-production', 'H2-production', 'H3-production', 'He3-production', 'He4-production']
        self.PARTICLE_PRODUCTION_UNIT = ' particles produced per source particle'
        self.MISCELLANEOUS_SCORES = ['current', 'events', 'inverse-velocity', 'decay-rate']
        self.MISCELLANEOUS_UNIT = [' particles per source particle', 'events per source particle', ' s/cm', ' /s']
        self.ENERGY_SCORES = ['heating', 'heating-local', 'kappa-fission', 'damage-energy', 'pulse-height',
                                     'fission-q-prompt', 'fission-q-recoverable']
        self.ENERGY_SCORES_UNIT = ' eV per source particle'

        x_Format = ['x axis format ', '1.0 10\u00b3', '1.00 10\u00b3', '1.000 10\u00b3']
        self.x_Format_CB.addItems(x_Format)
        self._initButtons()

    def _initButtons(self):
        self.browse_PB.clicked.connect(self.Get_SP_File)
        self.get_tally_info_PB.clicked.connect(self.Display_Tallies_Inf)
        self.Tally_id_comboBox.currentIndexChanged.connect(self.SelectTally)
        self.tally_display_PB.clicked.connect(self.Display_tally)
        self.Filters_comboBox.currentIndexChanged.connect(self.SelectFilter)
        self.filters_display_PB.clicked.connect(self.Display_filters)
        self.nuclides_display_PB.clicked.connect(self.Clear_nuclides)
        self.Nuclides_comboBox.currentIndexChanged.connect(self.SelectNuclides)
        self.Scores_comboBox.currentIndexChanged.connect(self.SelectScores)
        self.scores_display_PB.clicked.connect(self.Display_scores)
        self.Mesh_xy_RB.clicked.connect(self.Mesh_settings)
        self.Mesh_xz_RB.clicked.connect(self.Mesh_settings)
        self.Mesh_yz_RB.clicked.connect(self.Mesh_settings)
        self.Graph_type_CB.currentIndexChanged.connect(self.set_Scales)
        self.Plot_by_CB.currentIndexChanged.connect(self.set_Scales)
        self.Plot_by_CB.currentIndexChanged.connect(self.Set_PB_Label)
        self.Y2Label_CB.toggled.connect(self.Y2Label)
        self.xGrid_CB.stateChanged.connect(self.plot_grid_settings)
        self.yGrid_CB.stateChanged.connect(self.plot_grid_settings)
        self.y2Grid_CB.stateChanged.connect(self.plot_grid_settings)
        self.MinorGrid_CB.stateChanged.connect(self.plot_grid_settings)
        self.Graph_Layout_CB.currentIndexChanged.connect(self.set_Graph_stack)
        self.Plot_by_CB.currentIndexChanged.connect(self.set_Graph_stack)
        self.score_plot_PB.clicked.connect(self.Plot)
        self.Close_Plots_PB.clicked.connect(lambda:plt.close('all'))
        self.ResetPlotSettings_PB.clicked.connect(self.Reset_Plot_Settings)
        self.Nuclides_List_LE.textChanged.connect(lambda:self.score_plot_PB.setEnabled(False))
        self.Scores_List_LE.textChanged.connect(lambda:self.score_plot_PB.setEnabled(False))
        self.Tally_Normalizing_CB.toggled.connect(self.Enable_Tally_Normalizing)
        self.Norm_to_BW_CB.toggled.connect(self.Normalize_to_Bin_Width)
        self.Norm_to_UnitLethargy_CB.toggled.connect(self.Normalize_to_Unit_of_Lethargy)
        self.Norm_to_Vol_CB.toggled.connect(self.Normalize_to_Volume)
        self.Norm_to_SStrength_CB.toggled.connect(self.Normalize_to_SourceStrength)
        self.S_Strength_LE.textChanged.connect(lambda:self.Norm_to_SStrength_CB.setChecked(False))
        self.Vol_List_LE.textChanged.connect(lambda:self.Norm_to_Vol_CB.setChecked(False))
        # depletion results actions
        self.browse_Depl_Res_PB.clicked.connect(self.Get_Depl_Res_File)
        self.browse_Sim_PB.clicked.connect(self.Get_Simulation_File)
        self.Display_Depl_Res_Data_PB.clicked.connect(self.Display_Depletion_Results)
        self.Display_Data_PB.clicked.connect(self.Display_Depletion_Data)
        self.Time_Units_CB.currentIndexChanged.connect(self.Convert_Time_Units)
        self.Time_steps_comboBox.currentIndexChanged.connect(self.Get_Time_steps_from_Depl_Res_file)
        self.Material_CB.currentIndexChanged.connect(self.Get_material_specific_data)
        self.Nuclide_Data_type_CB.currentIndexChanged.connect(self.Get_specific_nuclides_data)
        self.Nuclides_ComboBx.currentIndexChanged.connect(self.CheckNuclides)
        self.Nuclides_ComboBx.model().dataChanged.connect(self.CheckNuclides)
        self.Data_Threshold_CB.currentIndexChanged.connect(self.Apply_Filter_Nuclides)
        self.Data_CB.currentIndexChanged.connect(self.Reset_Widgets)
        self.Define_Buttons()
        
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#++++++++++++++++++++++ CODE TO PROCESS SIMULATION SP FILE +++++++++++++++++++++++++++++++++++++++++++
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def Get_Summary_File(self):
        # read summary file
        if self.directory == '':
            return
        self._f = h5py.File(self.directory + '/summary.h5', 'r')
        self.Cells = []; self.Cells_id = []; self.surfaces = []
        self.materials = []; self.materials_id = []
        self.depletable_materials = []; self.depletable_materials_id = []
        self.materials_depletable = []; self.materials_volumes = []
        for key, group in self._f['geometry/cells'].items():
            cell_id = int(key.lstrip('cell '))
            self.Cells_id.append(cell_id)
            name = group['name'][()].decode() if 'name' in group else ''
            self.Cells.append(name)
        for group in self._f['geometry/surfaces'].values():
            name = group['name'][()].decode() if 'name' in group else ''
            self.surfaces.append(name)

        # Get all materials
        summary = openmc.Summary(self.directory + '/summary.h5')
        materials = summary.materials
        for mat in materials:
            self.materials.append(mat.name)
            self.materials_id.append(str(mat.id))
            self.materials_depletable.append(mat.depletable)
            self.materials_volumes.append(mat.volume)
            if mat.depletable:
                self.depletable_materials.append(mat.name) 
                self.depletable_materials_id.append(mat.id)            

    ################################################################
    # Handle depletion results file
    ################################################################

    def Get_Depl_Res_File(self):
        self.editor2.clear()
        self.Time_steps_comboBox.clear()
        self.Depl_Nuclides_List_LE.clear()
        self.tabWidget_2.setCurrentIndex(2)
        self.cursor = self.editor2.textCursor()
        self.Depl_Res_file = QtWidgets.QFileDialog.getOpenFileName(self, "Select HDF5 File", self.directory, "Depletion results file (depletion*.h5)")[0]
        self.directory = os.path.dirname(self.Depl_Res_file)    
        self.Depl_Res_LE.setText(self.Depl_Res_file)
        self.Get_Data_from_Depl_Res_file()
        self.lineLabel3.clear()
    
    def Get_Simulation_File(self):
        self.tabWidget_2.setCurrentIndex(2)
        self.Simulation_file = QtWidgets.QFileDialog.getOpenFileName(self, "Select HDF5 File", self.directory, "Simulation file (openmc_simulation*.h5)")[0]
        self.directory = os.path.dirname(self.Simulation_file)    
        self.Simulation_file_LE.setText(self.Simulation_file)
        self.Get_Data_from_Depl_Res_file()
        self.lineLabel3.clear()

    def Get_Data_from_Depl_Res_file(self):
        import openmc.deplete
        from openmc.deplete.stepresult import StepResult, VERSION_RESULTS
        import openmc.checkvalue as cv
        self.tabWidget_2.setCurrentIndex(2)
        self.Material_CB.setCurrentIndex(0)
        self.Data_CB.setCurrentIndex(0)
        self.Nuclide_Data_type_CB.setCurrentIndex(0)
        self.Data_Threshold_CB.setCurrentIndex(0)

        if not os.path.isfile(self.Depl_Res_file):
            self.showDialog('Warning', "depletion_results.h5 not available!" )
            return

        with h5py.File(self.Depl_Res_file, "r") as f:
            cv.check_filetype_version(f, 'depletion results', VERSION_RESULTS[0])
            # Get number of results stored
            self.n = f["number"][...].shape[0]
            Results_Keys = list(f.keys())
            #print('Available datasets/groups in openmc.deplete.Results :\t' + str(Results_Keys))
            """for group in range(len(f.keys())):
                present_group = list(f.keys())[group]  # e.g., '0'
                print(f"Keys in group '{present_group}':")
                print(list(f[present_group]))"""

        # get data frpm depletion_results.h5 file
        self.results = openmc.deplete.Results(self.Depl_Res_file)
        # fill Data combobox
        self.Data_CB.clear()
        self.Data_CB.addItem('select data')
        self.Data_CB.setCurrentIndex(0)
        
        if 'eigenvalues' in Results_Keys:
            self.Data_CB.addItems(['Keff data', 'Nuclide data'])
        else:
            self.Data_CB.addItem('Nuclide data')

        # Obtain time steps
        self.Time_Steps = [None] * self.n
        for i, result in enumerate(self.results):
            self.Time_Steps[i] = result.time[0]
        # convert time units
        #self.Time_Steps = self.Convert_Time_Units()
        # Fill time steps combobox
        self.Time_steps_comboBox.clear()
        self.Time_steps_comboBox.addItems(['Check step', 'All bins'])
        self.Time_steps_comboBox.addItems([str(t) for t in self.Time_Steps])
        self.Time_steps_comboBox.model().item(0).setEnabled(False)
        self.Time_steps_comboBox.model().item(0).setCheckState(Qt.Unchecked)


    def Get_Time_steps_from_Depl_Res_file(self):
        results = self.results
        if self.Data_CB.currentIndex() == 1:  # get Keff
            Keff = results.get_keff(time_units='d')[1]
        elif self.Data_CB.currentIndex() == 2: # get nuclide data
            self.Material_CB.clear()
            self.Material_CB.addItem('select material')
            self.Material_CB.addItems(self.depletable_materials)
            self.Material_CB.setCurrentIndex(0)

        if self.Time_steps_comboBox.checkedItems():
            self.Checked_Time_Steps = [self.Time_steps_comboBox.itemText(i) for i in self.Time_steps_comboBox.checkedItems()]
            if 'All bins' in self.Checked_Time_Steps:
                self.Checked_Time_Steps.pop(self.Checked_Time_Steps.index('All bins'))
        else:
            self.Checked_Time_Steps = []
        
    def Display_Depletion_Results(self):
        Keys = ['time', 'materials', 'nuclides', 'reactions']
        with h5py.File(self.Depl_Res_file, 'r') as f:
            Results_Keys = list(f.keys())
            print('Available datasets/groups in openmc.deplete.Results :\n')
            for key in Keys:
                print(f"  - Keys in group '{key}':")
                if key in ['materials']:    
                    print(f"\t{np.array(f[key])}")
                elif key == 'time':
                    times = f[key]
                    np.set_printoptions(precision=5, suppress=True) 
                    print(f"\t{np.array(f[key])}")
                elif key == 'source rate':
                    power = f[key]
                elif key in ['nuclides', 'reactions']:
                    self.Print_Formated_Data(list(f[key]), 10, 110, 9, 'str_kind') 
            power_vs_time = [(t, p, ) for t, p in zip(time, power)]
            print(str(power_vs_time))
            print(f"{'#'*80}")
            for group in range(len(Results_Keys)):
                present_group = list(f.keys())[group]  # e.g., '0'
                print(f"\t- Keys in group '{present_group}':")
                print(f"\t\t{list(f[present_group])}")
            
            """
            print("Available datasets/groups:", list(f.keys()))
            print(f)
            materials = list(f['materials'].keys())
            print('materials : ' + str(materials))
            print("Materials:", list(f["materials"].keys()))
            print("Nuclides:", list(f["nuclides"].keys()))
            print("Reactions:", list(f['reactions']))
            rates = f['reaction rates'][()]"""

    def Print_Formated_Data(self, data, cols, LWidth, StrWidth, StrKind):
        # Calculate required padding
        padding = (cols - (len(data) % cols)) % cols  # Ensures correct padding (0 if already divisible)
        padded_data = data + [""] * padding  # Fill missing with empty strings

        # Reshape into matrix
        matrix = np.array(padded_data).reshape(-1, cols)  # -1 = auto compute rows

        #np.set_printoptions(edgeitems=3, infstr='inf', linewidth=75, nanstr='nan', precision=8, suppress=False, threshold=1000, formatter=None)
        np.set_printoptions(edgeitems=3, infstr='inf', linewidth=LWidth, nanstr='nan', suppress=False, threshold=1000, formatter=None)
        # Print formatted
        print(np.array2string(
            matrix,
            formatter={StrKind: lambda x: f"{x:{StrWidth}}"},  # Fixed width
            threshold=np.inf  # Ensure all rows print
        ).replace('[', '').replace(']', ''))


        """padding = (cols - (len(data) % cols)) % cols
        padded_data = data + [""] * padding

        for i in range(0, len(padded_data), cols):
            row = padded_data[i:i+cols]
            print(" | ".join(f"{x:10}" for x in row))  # Fixed width"""
        
    def Display_Depletion_Data(self):
        self.tabWidget_2.setCurrentIndex(2)
        results = self.results
        if self.Time_steps_comboBox.checkedItems():
            self.Checked_Time_Steps = [self.Time_steps_comboBox.itemText(i) for i in self.Time_steps_comboBox.checkedItems()]
            if 'All bins' in self.Checked_Time_Steps:
                self.Checked_Time_Steps.pop(self.Checked_Time_Steps.index('All bins'))
        else:
            self.Checked_Time_Steps = []
            self.showDialog('Warning', 'Check time step first!')
            return        
        
        material_data = {}
        for material_id in self.depletable_materials_id:
            for step in self.Checked_Time_Steps:
                i_step = self.Time_Steps.index(float(step))
                current_step = self.results[i_step]
                id = str(material_id)
                material_data[id] = current_step.get_material(id)
                nuclides = material_data[id].nuclides
                print(f'nuclides in material {id} at step {i_step}\n ')
                print(f"Nuclide\t Atom fraction \t Atoms")
                for nuclide in nuclides:  
                    times, atoms_numb = self.results.get_atoms(id, nuclide.name)
                    print(f'{str(nuclide.name)} \t {str(nuclide.percent)} \t {str(atoms_numb[list(times).index(float(step))])}')

        if self.Data_CB.currentText() == 'Keff data':  # display Keff
            Keff = results.get_keff(time_units='d')[1]
            print(f"Time [{self.Time_Units_CB.currentText()}]\t\tKeff\tdKeff")
            for i in range(len(self.Checked_Time_Steps)):  
                print(f"{float(self.Checked_Time_Steps[i]):12.3f}\t{Keff[i][0]:7.5f}\t{Keff[i][1]:7.5f}")
        elif self.Data_CB.currentText() == 'Nuclide data':  # display nuclide data
            print('Checked time steps : ' + str(self.Checked_Time_Steps))
            materials = {}; nuclides = {}; activities = {}
            for id in self.depletable_materials_id:
                materials['id = ' +f'{id}'] = self.depletable_materials[self.depletable_materials_id.index(id)]
            print('Depleted materials :\t' + str(materials))
            
            for id in self.depletable_materials_id:
                mat = materials['id = ' +f'{id}']
                nuclides[mat] = []
                times, activities[id] = results.get_activity(str(id), by_nuclide=True)
                times, activities[id] = results.get_activity(str(id), by_nuclide=True)
                for time_step in self.Checked_Time_Steps:
                    print(f'nuclides in {mat} at time_step {time_step} {self.Time_Units_CB.currentText()} :')
                    t_idx = list(times).index(float(time_step))   
                    nuclide = [nuc for nuc in activities[id][t_idx].keys()]
                    activity = [val for val in activities[id][t_idx].values()]
                    nuclides[mat].append(nuclide)
                    print('\t Nuclide \t Activity [Bq/cm3]')
                    for nuc, act in zip(nuclide, activity):    
                        print('\t' + str(nuc) + '\t' + str(act))
            print("Nuclides tracked:\t", nuclides)
            #print("Nuclides tracked:", list(results['nuclides']))
            
            return

            print('Nuclides at last step:\t' + str(list(f["nuclides"].keys())))
            for i in range(len(self.Checked_Time_Steps)):
                step_idx = self.Time_Steps.index(float(self.Checked_Time_Steps[i]))
                current_result = results[step_idx]
                print('step : ' + str() + '\tT = ' + \
                       str(self.Checked_Time_Steps[i]) + ' ' + str(self.Time_Units_CB.currentText())) 

    def Get_material_specific_data(self):  
        self.Nuclide_Data_type_CB.setCurrentIndex(0)
        self.Data_Threshold_CB.setCurrentIndex(0) 

        if self.Data_CB.currentIndex() != 2:
            return
        if self.Material_CB.currentIndex() <= 0:
            self.Nuclides_ComboBx.clear()
            return
        self.Nuclides_ComboBx.clear()
        self.Nuclides_ComboBx.addItems(['check nuclide', 'All bins'])
        self.Nuclides_ComboBx.model().item(0).setEnabled(False)
        self.Nuclides_ComboBx.model().item(0).setCheckState(Qt.Unchecked)
    
        materials = {}; self.tracked_nuclides = {}; self.activities = {}
        self.decay_heat = {}; self.atoms = {}; self.mass = {}; self.reaction_rate = {}

        self.id = self.depletable_materials_id[self.depletable_materials.index(self.Material_CB.currentText())]
        id = self.id
        materials['id = ' +f'{id}'] = self.depletable_materials[self.depletable_materials_id.index(id)]
        self.mat = materials['id = ' +f'{id}']
        mat = self.mat
        self.tracked_nuclides[mat] = []
        results = self.results
        self.times, self.activities[id] = results.get_activity(str(id), by_nuclide=True)
        # get nuclide list at last time step
        self.tracked_nuclides[mat] = [nuc for nuc in self.activities[id][-1].keys()]
        self.Nuclides_ComboBx.addItems(self.tracked_nuclides[mat])
        if self.Chain:
            openmc.config['chain_file'] = self.Chain
            times, self.decay_heat[id] = results.get_decay_heat(str(id), units='W', by_nuclide=True)
            self.Nuclide_Data_type_CB.model().item(self.Nuclide_Data_type_CB.findText('decay heat')).setEnabled(True)
        else:
            pass
            reply = QMessageBox.question(self, "Message", "Load a chain depletion file ?", QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                self.Chain = QtWidgets.QFileDialog.getOpenFileName(self, "Select depletion chain file", self.directory, "Depletion results file (chain*.xml)")[0]
                self.Nuclide_Data_type_CB.model().item(self.Nuclide_Data_type_CB.findText('decay heat')).setEnabled(True)
            else:    
                self.Nuclide_Data_type_CB.model().item(self.Nuclide_Data_type_CB.findText('decay heat')).setEnabled(False)

        self.atoms[id] = {}; self.mass[id] = {}; self.reaction_rate[id] = {}
        
        print(results.keys())
        return
        for nuc in self.tracked_nuclides[mat]:
            RXs = results.reactions[nuc]
            print(f'Available reactions for {nuc} : {str(RXs)}')
            times, self.atoms[id][nuc] = results.get_atoms(str(id), nuc_units='atoms', nuclide=nuc)
            times, self.mass[id][nuc] = results.get_mass(str(id), mass_units='atoms', nuclide=nuc)
            self.reaction_rate[id][nuc] = {}
            for reaction in RXs:
                times, self.reaction_rate[id][nuc][reaction] = results.get_reaction_rate(str(id), nuclide=nuc, rx=reaction)

    def CheckNuclides(self):
        self.Depl_Nuclides_List_LE.clear()
        if self.Nuclides_ComboBx.checkedItems():
            self.Checked_Nuclides = [self.Nuclides_ComboBx.itemText(i) for i in self.Nuclides_ComboBx.checkedItems()]
            if 'All bins' in self.Checked_Nuclides:
                self.Checked_Nuclides.pop(self.Checked_Nuclides.index('All bins'))
            self.Depl_Nuclides_List_LE.setText(str(self.Checked_Nuclides))
        else:
            self.Checked_Nuclides = []
            self.Depl_Nuclides_List_LE.clear()
        self.Nuclides_ComboBx.setCurrentIndex(0)




    def Apply_Filter_Nuclides(self):
        self.Remained_Nuclides = set()  # Using a set to avoid duplicates
        self.Rejected_Nuclides = set()
        self.Remained_Activities = {}; self.Rejected_Activities = {}
        self.Remained = {}; self.Rejected = {}
        
        if self.Data_Threshold_CB.currentIndex() in [-1,0,1]:  # no filter
            Threshold = -1.
        elif self.Data_Threshold_CB.currentIndex() == 2:    # only non null data nuclides
            Threshold = 0
        else:                                               # only satisfying threshold nuclides 
            #Threshold = float(self.Data_Threshold_CB.currentText())
            Threshold = self.parse_scientific_unicode(self.Data_Threshold_CB.currentText())

        if self.Nuclide_Data_type_CB.currentText() == 'atoms':
            pass
        elif self.Nuclide_Data_type_CB.currentText() == 'mass':
            pass
        elif self.Nuclide_Data_type_CB.currentText() == 'activity':
            for time in self.Checked_Time_Steps:
                t_idx = list(self.times).index(float(time)) 
                self.Remained[str(t_idx)] = []; self.Rejected[str(t_idx)] = []
                self.Remained_Activities[str(t_idx)] = []; self.Rejected_Activities[str(t_idx)] = []  
                for nuclide in self.Checked_Nuclides:
                    Nuc_idx = self.Checked_Nuclides.index(nuclide)   #self.tracked_nuclides[self.mat]
                    activity = list(self.activities[self.id][t_idx].values())[Nuc_idx]
                    if activity > Threshold:
                        self.Remained_Nuclides.add(nuclide)
                        self.Remained_Activities[str(t_idx)].append(activity)
                        self.Remained[str(t_idx)].append((nuclide, activity,))
                    else:
                        self.Rejected_Nuclides.add(nuclide)
                        self.Rejected_Activities[str(t_idx)].append(activity)
                        self.Rejected[str(t_idx)].append((nuclide, activity,))
                
        elif self.Nuclide_Data_type_CB.currentText() == 'reaction rate':
            pass
        elif self.Nuclide_Data_type_CB.currentText() == 'decay heat':
            pass
        
        self.Depl_Nuclides_List_LE.setText(str(list(self.Remained_Nuclides)))
        if self.Data_Threshold_CB.currentIndex() not in [0, 1]:
            print(f'Nuclides satisfying {self.Nuclide_Data_type_CB.currentText()} > {Threshold}')
        elif self.Data_Threshold_CB.currentIndex() == 2:
            print(f'Nuclides satisfying non null {self.Nuclide_Data_type_CB.currentText()}')
        
        for time in self.Checked_Time_Steps:
            t_idx = list(self.times).index(float(time))
            print(f'\nMaterial {self.mat} data at step {t_idx} :\n')
            print(f'Remained nuclides : {len(self.Remained_Nuclides)} among {len(self.Checked_Nuclides)} checked nuclides \
                    with {len(self.Remained_Activities[str(t_idx)])} activity values.')
            print(f'List of remained nuclides : {list(self.Remained_Nuclides)}')
            print(f'Nuclide\t{self.Nuclide_Data_type_CB.currentText()}')
            '''for nuc, act in zip(self.Remained_Nuclides, self.Remained_Activities[str(t_idx)]):    
                print(f'{str(nuc)}\t{str(act)}')
            '''
            for i in range(len(self.Remained[str(t_idx)])):
                print(f'{self.Remained[str(t_idx)][i][0]}\t{self.Remained[str(t_idx)][i][1]}')
        
    def generate_powers_of_10(self, min_value, max_value):
        """Generate powers of 10 (10^n) between min_value and max_value."""
        if min_value <= 0 or max_value <= 0:
            raise ValueError("min_value and max_value must be positive")
        
        powers = []
        n = -20
        while True:
            current_power = 10 ** n
            if current_power > max_value:
                break
            if current_power >= min_value:
                powers.append(self.sci_notation(current_power))
            n += 5
        
        return powers

    def sci_notation(self, number, precision=0):
        superscript_map = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")
        base, exp = f"{number:.{precision}e}".split('e')
        base = base.rstrip('0').rstrip('.')  # remove trailing .0
        exp = int(exp)
        #return f"{base} × 10{str(exp).translate(superscript_map)}"
        return f"10{str(exp).translate(superscript_map)}"

    def parse_scientific_unicode(self, sci_str):
        # Mapping from superscript to normal digits
        superscript_map = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789-")
        
        # Split by '× 10'
        if '10' in sci_str:
            #base = 1
            exp = sci_str.split('10', 1)[1]
            #base = float(base.strip())
            exp = int(exp.translate(superscript_map))
            #return base * (10 ** exp)
            return (10 ** exp)
        else:
            raise ValueError("Input must be in format like '3 × 10⁻⁶'")

    def Get_specific_nuclides_data(self):
        self.Data_Threshold_CB.setCurrentIndex(0)
        if len(self.Checked_Nuclides) == 0 and self.Nuclide_Data_type_CB.currentIndex() != 0:
            self.showDialog('Warning', 'Check nuclides first!')
            self.Nuclide_Data_type_CB.setCurrentIndex(0)
            return
        if self.Nuclide_Data_type_CB.currentText() == 'activity':
            mat = self.mat
            activity = {}; activity[mat] = {}
            act_min = 1E+35; act_max = 1E-35
            for time in self.Checked_Time_Steps:
                t_idx = list(self.times).index(float(time))
                activity[mat][t_idx] = [val for val in self.activities[self.id][t_idx].values()]
                act_min = np.min([act_min, np.min([x for x in activity[mat][t_idx] if x != 0])])
                act_max = np.max([act_max, np.max(activity[mat][t_idx])])
                print('values', activity[mat][t_idx])
                print(f'min : {str(act_min)}\t max: {str(act_max)}')
            
            Thresholds = self.generate_powers_of_10(act_min, act_max)
            self.Data_Threshold_CB.clear()
            self.Data_Threshold_CB.addItems(['select threshold', 'no threshold', 'non null values only'])
            self.Data_Threshold_CB.addItems([str(x) for x in Thresholds])
        return
        # Export materials from the last timestep
        # Get final result
        last_result = self.results[-1]

        print('ResultList type: ' + str(type(openmc.deplete.ResultsList)) + '   ' + str(openmc.deplete.ResultsList))
        print('StepResult type: ' + str(type(self.results)) + '   ' + str(type(last_result)))
        print('k:\t' + str(last_result.k[0]))
        #print('k:\t' + f"{last_result.k[0]:7.5f}\t{last_result.k[1]:7.5f}")
        print('n mat:\t' + str(last_result.n_mat))
        print('index_mat:\t' + str(last_result.index_mat))
        print('n_nuc:\t' + str(last_result.n_nuc))
        print('index_nuc:\t' + str(last_result.index_nuc))
        print('rates:\t' + str(last_result.rates))
        print('n_stages: ' + str(last_result.n_stages))
        print('data: ' + str(last_result.data))

        with h5py.File(self.Depl_Res_file, 'r') as f:
            print("Available datasets/groups:", list(f.keys()))
            print(f)
            materials = list(f['materials'].keys())
            print('materials : ' + str(materials))
            print("Materials:", list(f["materials"].keys()))
            print("Nuclides:", list(f["nuclides"].keys()))
            print("Reactions:", list(f['reactions']))
            rates = f['reaction rates'][()]

            ################################
            # List all top-level groups (materials + metadata like 'time', 'decay_heat')
            keys_names = [key for key in f.keys() if isinstance(f[key], h5py.Group)]
            
            print("Keys in Materials in depletion_results.h5:")
            for name in keys_names:
                print(f"  - {name}")
                
            nuclides_last_step = list(self.results[-1].index_nuc.keys())
            print('nuclides: ', nuclides_last_step)
            # ############################
            nuclides = {}  #f['nuclides'][()].astype(str)
            densities = {}
            #print('nuclides : ', nuclides)
            for material in materials:
                # Get time steps (in days)
                time_steps = f['time'][()]  # Shape: (n_steps,)
                print('******  ' + str(f['materials'][material]))   #.astype(str))
                # Get nuclides and their densities
                print('material :  ' + material)
                #print(self.results[0].get_nuclide_densities(materials.index(material)).keys())
                #print(self.results[1].get_nuclide_densities(materials.index(material)).keys())
        

                #print(list(f[f"materials/{materials.index(material)}/{0}/nuclides"]))
                #print(list(f[f"materials/{materials.index(material)}/{1}/nuclides"]))
                print(f.keys())
                densities[material] = f['number']  # Shape: (n_nuclides, n_steps)
                print(f['materials'][material])  # List of mat
                print(f['nuclides'] ) # List of nuclides
                print(densities)
                # Convert to a Pandas DataFrame for easy analysis
                df = pd.DataFrame(densities[material], columns=nuclides)  #[material])
                df['time (days)'] = time_steps
                print('nuclides by mat: ' +  str(material) +'-->' + nuclides[material])
                print("\nNuclide densities over time:")
                print(df.head())


        #############################        
        for step_id in range(4):
            step = self.results[step_id]
            materials = []
            for m in ["1", "3"]:   
                material = step.get_material(m)
                nuclides = material.get_activity(by_nuclide=True, units='Bq/cm3')

                nuclide_df = pd.DataFrame(nuclides.items(), columns=['nuclide', 'activity_bq_per_cc'])
                nuclide_df = nuclide_df.sort_values('activity_bq_per_cc', ascending=False)
                print(nuclide_df)
                materials.append(material)
            

                # materials is a list of Material objects, so you'll need to get the right index 
                # for the material of interest
                
                print(str(material))

                # Get number of atoms
                atoms = material.get_nuclide_atoms()
                print(str(atoms))

                # Get total activity and activity by nuclide
                activity_by_nuclide = material.get_activity()
                print('material: ' + m)
                print(str(activity_by_nuclide))

                
                nuclides, densities = self.results.get_atoms(m, step_id)
                print('nuclides : ' + str(nuclides) + str(densities))


            res_df = pd.DataFrame(materials)
            print(res_df)

        
        self.Nuclides_comboBox.addItems(Nuclides)
        self.Nuclides_comboBox.model().item(0).setEnabled(False)
        self.Nuclides_comboBox.model().item(0).setCheckState(Qt.Unchecked)

    
        # Obtain U235 concentration as a function of time
        _, n_U235 = self.results.get_atoms("1", 'U235')
        # Obtain Xe135 capture reaction rate as a function of time
        _, Xe_capture = self.results.get_reaction_rate("1", 'Xe135', '(n,gamma)')

    def Reset_Widgets(self):
        self.Material_CB.setCurrentIndex(0)
        self.Nuclide_Data_type_CB.setCurrentIndex(0)
        self.Data_Threshold_CB.setCurrentIndex(0)
        self.Nuclides_ComboBx.setCurrentIndex(0)
        self.Time_steps_comboBox.setCurrentIndex(0)
        self.Depl_Nuclides_List_LE.clear()
        for i in range(1,len(self.Time_Steps) + 2):
            self.Time_steps_comboBox.setItemChecked(i, False)

    def Get_data_from_Simulation_file(self):
        if not os.path.isfile(self.Simulation_file):
            return
        self._f = h5py.File(self.Simulation_file, 'r')

    def Convert_Time_Units(self):
        T = np.array(self.Time_Steps)
        self.Time_steps_comboBox.clear()
        self.Time_steps_comboBox.addItems(['Check step', 'All bins'])

        if self.Time_Units_CB.currentText() == 'min':
            SECONDS_PER_ = 60
        elif self.Time_Units_CB.currentText() == 'h':
            SECONDS_PER_ = 3600
        elif self.Time_Units_CB.currentText() == 'd':
            SECONDS_PER_ = 86400
        elif self.Time_Units_CB.currentText() == 'a':
            SECONDS_PER_ = 31557600
        else:
            SECONDS_PER_ = 1
        Times = T / SECONDS_PER_
        
        self.Time_steps_comboBox.addItems([str(t) for t in Times])
        #return Times

    ################################################################
    # Handle tallies from statepoint file
    ################################################################

    def Get_SP_File(self):
        self.Tally_id_comboBox.clear()
        self.Tally_id_comboBox.addItem("Select the tally's ID")
        self.editor.clear()
        self.Plot_by_CB.clear()
        self.Filters_comboBox.clear()
        self.Nuclides_comboBox.clear()
        self.Scores_comboBox.clear()
        self.tabWidget_2.setCurrentIndex(0)
        self.sp_file = QtWidgets.QFileDialog.getOpenFileName(self, "Select HDF5 File", self.directory, "statepoint file (statepoint*.h5);;openmc_simulation file (openmc*.h5)")[0]
        self.directory = os.path.dirname(self.sp_file)    
        self.lineEdit.setText(self.sp_file)
        self.Get_data_from_SP_file()
        self.lineLabel3.clear()
        self.Get_Summary_File()

    def Get_data_from_SP_file(self):
        global sp
        self.Heating_LE.clear()
        self.Factor_LE.clear()
        if not os.path.isfile(self.sp_file):
            return
        self._f = h5py.File(self.sp_file, 'r')
        self.run_mode = self._f['run_mode'][()].decode()
        try:
            for i in range(len(self.Bins_comboBox)):
                self.Bins_comboBox[i].hide()
        except:
            pass
        try:
            sp = openmc.StatePoint(self.sp_file)
            self.names = {}
            self.Nuclides = {}
            self.Scores = {}
            self.Estimator = {}                
            self.Tallies['tallies_ids'] = []
            self.Tallies['names'] = []
            self.meshes = {}
            self.Tally_id_comboBox.clear()
            self.Tally_id_comboBox.addItem("Select the tally's ID")
            if self.run_mode == 'eigenvalue':
                self.H = None
                self.Tally_id_comboBox.addItem('Keff result')
                self.batches = [i+1 for i in range(sp.n_batches)]
                self.Keff_List = sp.k_generation.tolist()
                self.keff = sp.keff.nominal_value
                self.dkeff = sp.keff.std_dev
                try:
                    self.H = sp.entropy.tolist()
                except:
                    pass

            self.tallies_group = self._f['tallies']
            self.n_tallies = self.tallies_group.attrs['n_tallies'] 
            if self.n_tallies > 0:
                self.tally_ids = self.tallies_group.attrs['ids']
                self.filters_group = self._f['tallies/filters']
                for tally_id in self.tally_ids:
                    tally = sp.get_tally(id=tally_id)  # Ok
                    name = tally.name
                    self.Tallies['tallies_ids'].append(tally_id)
                    self.Tallies['names'].append(name)
                    for score in tally.scores:
                        if score == 'heating':
                            heat = tally.mean.ravel()[0]
                            self.Heating_LE.setText(str(heat))
                # Read all meshes
                mesh_group = self._f['tallies/meshes']
                # Iterate over all meshes
                for group in mesh_group.values():
                    mesh = openmc.MeshBase.from_hdf5(group)
                    self.meshes[mesh.id] = mesh
                self.Tallies_in_SP = list(sp.tallies.keys())

                for key in self.Tallies_in_SP:
                    self.names[key] = []
                    self.Nuclides[key] = []
                    self.Scores[key] = []
                    self.Estimator[key] = []
                    text = str(sp.tallies[key]).split('\n')
                    for line in text:
                        if 'Name' in line:
                            name = line.split('=')[1].lstrip()
                            self.names[key].append(name)
                        if 'Nuclides' in line:
                            nuclide = line.split('=')[1].lstrip().split(' ')
                            self.Nuclides[key] = nuclide
                        if 'Scores' in line:
                            score1 = line.split('=')[1].lstrip().replace("'", "")
                            score = score1[score1.find('[') + 1: score1.find(']')].split(', ')
                            self.Scores[key] = [item for item in score]
                        if 'Estimator' in line:
                            estimator = line.split('=')[1].lstrip()
                            self.Estimator[key].append(estimator)
                    self.Tally_id_comboBox.addItem(str(key))
            if self.tabWidget.currentIndex() == 0:
                self.lineLabel1.setText('Statepoint file : ' + self.sp_file)
                self.lineLabel2.setText('containing :  ' + str(self.n_tallies) + '  tallies')
        except:
            pass
        self.Reset_Tally_CB()
        
    def Display_Tallies_Inf(self):
        self.Display = False
        self.Normalization = False
        self.sp_file = self.lineEdit.text()
        if not os.path.isfile(self.sp_file):
            self.showDialog('Warning', 'Load valid sp file!')
            return
        self.editor1.clear()
        self.tabWidget_2.setCurrentIndex(1)

        try:
            sp = openmc.StatePoint(self.sp_file)
            # print tallies summary
            self.editor1.insertPlainText('*'*57 + ' TALLIES SUMMARY ' + '*'*58 + '\n')
            for key in sp.tallies.keys():
                self.editor1.insertPlainText(str(sp.tallies[key])+ '\n')
            self.editor1.insertPlainText('*'*134 + '\n')
            if self.run_mode == 'eigenvalue':
                # print Keff results
                n = sp.n_batches
                keff_glob = sp.global_tallies
                INDEX = [str(idx,encoding='utf-8').ljust(25)  for idx in keff_glob['name']]
                df = pd.DataFrame(keff_glob, index=INDEX, columns = ['name', 'mean', 'std_dev'])
                for item in df['name']:
                    elem = str(item,encoding='utf-8').ljust(25)
                    df = df.replace({'name': item}, {'name': elem})
                df.loc['Combined keff'] = ['Combined keff', self.keff, self.dkeff]
                df.iloc[4], df.iloc[3] = df.iloc[3], df.iloc[4]
                self.Print_Formated_df_Keff(df, self.editor1, '', 0)
                # print Keff vs batches
                self.batches = [i+1 for i in range(n)]
                self.Keff_List = sp.k_generation.tolist()
                df1 = pd.DataFrame({'batch': self.batches, 'Keff': self.Keff_List})
                self.Print_Formated_df_Keff(df1, self.editor1, ' K EFFECTIVE VS BATCH ', 1)
                try:    
                    self.H = sp.entropy.tolist()
                    df1 = pd.DataFrame({'batch': self.batches, 'Entropy': self.H}) 
                    self.Print_Formated_df_Keff(df1, self.editor1, '   SHANNON  ENTROPY   ', 1)
                except:
                    pass
            if self.n_tallies > 0:
                # print tallies results
                self.tally_ids = self.tallies_group.attrs['ids']
                self.editor1.insertPlainText('*'*57 + ' TALLIES RESULTS ' + '*'*58 + '\n')
                for tally_id in self.tally_ids:
                    self.tally_id = tally_id
                    try:
                        self.tally = sp.get_tally(id=tally_id)
                        if self.tally:
                            df = self.tally.get_pandas_dataframe(float_format = '{:.2e}')  #'{:.6f}') 
                        try:
                            self.Print_Formated_df(df, tally_id, self.editor1) 
                        except:
                            self.showDialog('Warning', 'The size of statepoint file may be huge!')
                    except:
                        self.tally_ids = np.delete(self.tally_ids, self.tally_ids.tolist().index(self.tally_id))
                        self.n_tallies -= 1

                        pass
        except:
            self.showDialog('Warning', 'Some thing went wrong or invalid statepoint file!')
            return
        self.Tally_id_comboBox.setCurrentIndex(0)

    def Reset_Tally_CB(self):
        self.Tally_id_comboBox.setCurrentIndex(0)
        self.Tally_id_comboBox.clear()
        self.Tally_id_comboBox.addItem("Select the tally's ID")
        self.Plot_by_CB.clear()
        self.Filters_comboBox.clear()
        self.Nuclides_comboBox.clear()
        self.Scores_comboBox.clear()
        try:
            if os.path.isfile(self.lineEdit.text()):
                self.sp_file = self.lineEdit.text()
                sp = openmc.StatePoint(self.sp_file)
                if self.run_mode == 'eigenvalue':
                    self.Tally_id_comboBox.addItem('Keff result')
                self.Tally_id_comboBox.addItems([str(tally) for tally in list(sp.tallies.keys()) if tally])
            else:
                pass
        except:
            return

    def Check_if_SP_file_exists(self):
        self.sp_file == self.lineEdit.text()
        if not os.path.isfile(self.sp_file):
            self.showDialog('Warning', 'Invalid path to stateppoint file!')
            self.Tally_id_comboBox.clear()
            self.Tally_id_comboBox.addItem("Select the tally's ID")
        else:
            pass

    def Set_PB_Label(self):
        if self.Plot_by_CB.currentText() == 'Keff':
            self.score_plot_PB.setText('plot Keff')
        elif self.Plot_by_CB.currentText() == 'Keff & Shannon entropy':
            self.score_plot_PB.setText('plot H & Keff')
        elif self.Plot_by_CB.currentText() == 'Shannon entropy':
            self.score_plot_PB.setText('plot H')

    def SelectTally(self):
        global power_items, Norm_Other
        tally_id = ''
        name = ''
        if self.lineEdit.text():
            self.sp_file = self.lineEdit.text()
        try:
            if not os.path.isfile(str(self.sp_file)):
                self.lineLabel1.setText("Current statepoint file : No valid statepoint file")
                return
        except:
            pass
        self.score_plot_PB.setText('plot data')
        self.filters = []
        self.Filter_names = []
        self.selected_scores = []
        self.Bins = {}
        self.Tally_name_LE.clear()
        self.Curve_title.clear()
        self.Curve_xLabel.clear()
        self.Curve_yLabel.clear()
        self.Curve_y2Label.clear()
        self.Nuclides_List_LE.clear()
        self.Scores_List_LE.clear()
        self.Plot_by_CB.clear()
        self.Filters_comboBox.clear()
        self.Nuclides_comboBox.clear()
        self.Scores_comboBox.clear()
        self.Vol_List_LE.clear()
        for elm in self.buttons:
            elm.setEnabled(False)
        self.Graph_Layout_CB.setCurrentIndex(0)
        self.Graph_type_CB.setCurrentIndex(0)
        #self.Graph_Layout_CB.setEnabled(False)
        self.score_plot_PB.setEnabled(False)
        self.xGrid_CB.setChecked(False)
        self.yGrid_CB.setChecked(False)
        self.y2Grid_CB.setChecked(False)
        self.MinorGrid_CB.setChecked(False)
        Norm_CBs = [self.Tally_Normalizing_CB, self.Norm_to_BW_CB, self.Norm_to_UnitLethargy_CB, 
                   self.Norm_to_SStrength_CB, self.Norm_to_Vol_CB, self.Norm_to_Power_CB, self.Norm_to_Heating_CB]
        for CB in Norm_CBs:
            CB.setChecked(False)
        
        self.Graph_type_CB.clear()
        if self.Tally_id_comboBox.currentIndex() > 0 and 'Keff' not in self.Tally_id_comboBox.currentText():
            tally_id = int(self.Tally_id_comboBox.currentText())
            self.Filters_comboBox.clear()
            self.Scores_comboBox.clear()
            self.Nuclides_comboBox.clear()      
            idx = self.Tallies['tallies_ids'].index(tally_id)
            name = self.Tallies['names'][idx]
            self.Tally_name_LE.setText(name)
            self.Filters_comboBox.addItem('Select filter')
            self.Tallies[tally_id] = {}
            self.Tallies[tally_id]['id'] = [tally_id]
            self.Tallies[tally_id]['filter_ids'] = []
            self.Tallies[tally_id]['filter_types'] = []
            self.Tallies[tally_id]['filter_names'] = []
            self.tally = sp.get_tally(id=tally_id)
            group = self.tallies_group[f'tally {tally_id}']
            self.df = self.tally.get_pandas_dataframe()
            self.df_Keys = self.df.keys()[:-2].tolist()        
            self.n_filters = group['n_filters'][()]
            # hide comboBoxes in gridLayout_20
            for i in range(self.gridLayout_20.layout().count()):
                widget = self.gridLayout_20.layout().itemAt(i).widget()
                widget.hide()            
            # Read all filters
            if self.n_filters > 0:                  # filters are defined
                self.Bins_comboBox = [''] * self.n_filters
                for i in range(self.n_filters):
                    self.Bins_comboBox[i] = CheckableComboBox()
                    row = int(i / 3) + 1          
                    col = i + 4 - row * 3                
                    self.gridLayout_20.addWidget(self.Bins_comboBox[i], row , col)

                self.filter_ids = group['filters'][()].tolist()
                self.Tallies[tally_id]['filter_ids'] = self.filter_ids
                for filter_id in self.filter_ids:  
                    self.Tallies[tally_id][filter_id] = {}
                    self.Tallies[tally_id][filter_id]['Checked_bins_indices'] = []                  
                    self.Tallies[tally_id][filter_id]['Checked_bins'] = []                  
                    self.Tallies[tally_id][filter_id]['scores'] = []
                    filter_group = self.filters_group[f'filter {filter_id}']
                    new_filter = openmc.Filter.from_hdf5(filter_group, meshes=self.meshes)
                    filter_name = str(new_filter).split('\n')[0]
                    filter_type = filter_group['type'][()].decode()
                    self.Tallies[tally_id]['filter_types'] += [filter_type]
                    self.Tallies[tally_id]['filter_names'] += [filter_name]
                self.Filter_names = self.Tallies[tally_id]['filter_names']
                filters = [filter + ' , id= ' + str(id) for filter, id in zip(self.Filter_names, self.filter_ids)]
                self.Filters_comboBox.addItems(filters)
                self.Filters_comboBox.setCurrentIndex(1)
                for i in range(len(self.Bins_comboBox)):
                    self.Bins_comboBox[i].currentIndexChanged.connect(self.SelectBins) 
                    self.Bins_comboBox[i].currentIndexChanged.connect(lambda:self.score_plot_PB.setEnabled(False)) 
                    self.Bins_comboBox[i].setCurrentIndex(0)
                self.filters = self.Tallies[tally_id]['filter_types']
            else:                                    # no filter defined
                self.Tallies[tally_id]['scores'] = []
                self.Filter_names = []
            # fill scores combobox
            self.scores = sorted(self.tally.scores)
            self.Tallies[tally_id]['scores'] = self.scores
            self.Scores_comboBox.clear()
            self.Scores_comboBox.addItem('Select score')
            if len(self.scores) > 1:
                self.Scores_comboBox.addItem('All scores')
            self.Scores_comboBox.addItems(self.scores)
            # fill nuclides combobox
            self.nuclides = self.tally.nuclides
            self.Tallies[tally_id]['nuclides'] = self.nuclides
            self.Nuclides_comboBox.clear()
            self.Nuclides_comboBox.addItem('Select nuclide')
            if len(self.nuclides) > 1:
                self.Nuclides_comboBox.addItems(['All nuclides'])
            self.Nuclides_comboBox.addItems(self.nuclides)
            self.Nuclides_comboBox.setCurrentIndex(1)
            if len(self.scores) == 1:
                self.Scores_List_LE.setText(self.scores[0]) 
            self.nuclides_display_PB.setEnabled(True)
            self.scores_display_PB.setEnabled(True)     
            self.label.setText('plot by')   
            self.Plot_by_CB.clear()
            self.Tally_Normalizing_CB.setEnabled(True)
            self.Tally_Normalizing_CB.setChecked(False)
            
        elif 'Keff' in self.Tally_id_comboBox.currentText():
            self.Add_error_bars_CB.setEnabled(False)                # Keff errors could not be extracted from statepoint file
            self.Graph_Layout_CB.setEnabled(False)
            self.Checked_batches = []
            self.Checked_batches_bins = []
            self.Tally_name_LE.setText('Keff vs batches')
            self.Filters_comboBox.clear()
            self.Filters_comboBox.addItem('Select filter')
            self.Filters_comboBox.addItem('Batches Filter')
            for i in reversed(range(self.gridLayout_20.count())): 
                self.gridLayout_20.itemAt(i).widget().setParent(None)   
            self.Bins_comboBox = ['']
            self.Bins_comboBox[0] = CheckableComboBox()
            self.gridLayout_20.addWidget(self.Bins_comboBox[0], 0, 0)
            self.Filters_comboBox.setCurrentIndex(1)
            self.nuclides_display_PB.setEnabled(False)
            self.scores_display_PB.setEnabled(False)
            self.xLog_CB.setText('xLog')
            self.yLog_CB.setText('yLog')
            self.Add_error_bars_CB.setText('Error bars')
            self.filters_display_PB.setText('select')
            self.score_plot_PB.setText('plot Keff')
            self.Plot_by_CB.setEnabled(True)
            for bt in self.buttons:
                bt.setEnabled(True)
            self.Bins_comboBox[0].currentIndexChanged.connect(self.SelectBins)
            self.Graph_type_CB.setCurrentIndex(3)
            self.Curve_title.setText(self.Tally_name_LE.text())
            self.Curve_xLabel.setText('batches')
            self.Curve_yLabel.setText('Keff')
            self.label.setText('plot') 
            self.Plot_by_CB.clear()
            self.Plot_by_CB.addItem('select item')
            if self.H:
                self.Plot_by_CB.addItems(['Keff', 'Keff & Shannon entropy', 'Shannon entropy'])
            else:
                self.Plot_by_CB.addItem('Keff')
            self.Plot_by_CB.setCurrentIndex(1)
            self.Graph_type_CB.addItems(['Select Graph type', 'Lin-Lin', 'Scatter'])
            self.Graph_type_CB.setCurrentIndex(1)
            self.Tally_Normalizing_CB.setEnabled(False)
            self.Tally_Normalizing_CB.setChecked(False)
        else:
            self.Tally_name_LE.clear()
            self.Curve_title.clear()
            self.Curve_xLabel.clear()
            self.Curve_yLabel.clear()
            self.Curve_y2Label.clear()
            self.Filters_comboBox.clear()
            try:
                for i in range(len(self.Bins_comboBox)):
                    self.Bins_comboBox[i].hide()
            except:
                pass            
            self.Plot_by_CB.setCurrentIndex(0)
            self.Graph_Layout_CB.setCurrentIndex(0)
    
        power_items = [self.label_21, self.label_22, self.label_16, self.label_17, self.label_18, self.Nu_LE, 
                       self.Heating_LE, self.Keff_LE, self.Q_LE, self.Norm_to_Power_CB, self.Norm_to_Heating_CB, 
                       self.Power_LE, self.Factor_LE]
        Norm_Other = [self.label_37, self.label_19, self.Norm_to_BW_CB, self.Norm_to_Vol_CB, self.Norm_to_UnitLethargy_CB,
                      self.Norm_Bins_comboBox, self.Vol_List_LE, self.S_Strength_LE]
        CBoxes = [self.Norm_to_BW_CB, self.Norm_to_Vol_CB, self.Norm_to_UnitLethargy_CB, self.Norm_to_Power_CB, 
                    self.Norm_to_Heating_CB, self.Norm_to_SStrength_CB]
        for item in power_items:
            item.setEnabled(False)
        for item in Norm_Other:
            item.setEnabled(False)
        for CB in CBoxes:
            CB.setChecked(False)
        self.Norm_Bins_comboBox.clear()
        
        if tally_id != '':
            self.lineLabel2.setText('Selected tally id : ' + str(tally_id))
            self.lineLabel3.setText('  Tally name : ' + name)
        
        Widgets = [self.label, self.label_2, self.label_3, self.Plot_by_CB,self.xGrid_CB, self.yGrid_CB,
                  self.y2Grid_CB, self.MinorGrid_CB, self.Curve_y2Label, self.Y2Label_CB]  
        
        if self.Tally_id_comboBox.currentIndex() > 0 and 'Keff' not in self.Tally_id_comboBox.currentText():
            if 'MeshFilter' in self.Filter_names:
                self.Graph_type_CB.clear()
                self.Graph_type_CB.addItems(['Select Graph type', 'mesh plot', 'contourf' , 'contour'])
                self.Graph_type_CB.setItemData(1,'Display data as an image', QtCore.Qt.ToolTipRole)
                self.Graph_type_CB.setItemData(2,'Plot filled contours', QtCore.Qt.ToolTipRole)
                self.Graph_type_CB.setItemData(3,'Plot contour lines', QtCore.Qt.ToolTipRole)
                for W in Widgets:
                    W.hide()
                mesh = self.tally.find_filter(openmc.MeshFilter).mesh
                self.mesh_type = type(mesh).__name__

                if self.mesh_type == 'CylindricalMesh': 
                    self.Curve_xLabel.clear()
                    self.Curve_yLabel.clear()
                    self.Mesh_xy_RB.setText('mesh rphi')
                    self.Mesh_xz_RB.setText('mesh rz')
                    self.Mesh_yz_RB.setEnabled(False)
                else:
                    self.Mesh_xy_RB.setText('mesh xy')
                    self.Mesh_xz_RB.setText('mesh xz')
                    self.Mesh_yz_RB.setEnabled(True)
                    self.Curve_xLabel.setText('x/cm')
                    self.Curve_yLabel.setText('y/cm')
            else:
                self.Graph_type_CB.clear()
                self.Graph_type_CB.addItems(['Select Graph type', 'Bar', 'Stacked Bars' , 'Lin-Lin', 'Scatter', 'Stairs', 'Stacked Area'])
                self.Graph_type_CB.setItemData(1,'Make a bar plot', QtCore.Qt.ToolTipRole)
                self.Graph_type_CB.setItemData(2,'Make a stacked bar char', QtCore.Qt.ToolTipRole)
                self.Graph_type_CB.setItemData(3,'Plot y versus x as lines', QtCore.Qt.ToolTipRole)
                self.Graph_type_CB.setItemData(4,'A scatter plot of y vs. x with varying marker size and/or color.', QtCore.Qt.ToolTipRole)
                self.Graph_type_CB.setItemData(5,'Draw a stepwise constant function as a line', QtCore.Qt.ToolTipRole)
                self.Graph_type_CB.setItemData(6,'Draw a stacked area plot', QtCore.Qt.ToolTipRole)
                for W in Widgets:
                    W.show()

    def Display_tally(self):
        self.Display = False
        self.sp_file == self.lineEdit.text()
        self.Normalization = False
        self.tabWidget_2.setCurrentIndex(0)
        cursor = self.editor.textCursor()
        cursor.movePosition(cursor.End)
        try:
            if os.path.isfile(self.sp_file):
                sp = openmc.StatePoint(self.sp_file)
                self.tabWidget_2.setCurrentIndex(0)
                if self.Tally_id_comboBox.currentIndex() > 0 and 'Keff' not in self.Tally_id_comboBox.currentText():
                    df = self.tally.get_pandas_dataframe(float_format = '{:.2e}')  #'{:.6f}')
                    tally_id = int(self.Tally_id_comboBox.currentText())
                    self.Print_Formated_df(df.copy(), tally_id, self.editor)  
                elif self.Tally_id_comboBox.currentIndex() > 0 and 'Keff' in self.Tally_id_comboBox.currentText():
                    # print Keff results
                    n = sp.n_batches
                    keff_glob = sp.global_tallies
                    INDEX = [str(idx,encoding='utf-8').ljust(25)  for idx in keff_glob['name']]
                    df = pd.DataFrame(keff_glob, index=INDEX, columns = ['name', 'mean', 'std_dev'])
                    for item in df['name']:
                        elem = str(item,encoding='utf-8').ljust(25)
                        df = df.replace({'name': item}, {'name': elem})
                    df.loc['Combined keff'] = ['Combined keff', self.keff, self.dkeff]
                    df.iloc[4], df.iloc[3] = df.iloc[3], df.iloc[4]
                    self.Print_Formated_df_Keff(df, self.editor, '', 0)
                    # print Keff vs batches
                    df1 = pd.DataFrame({'batch': [i+1 for i in range(n)], 'Keff': sp.k_generation.tolist()})
                    self.Print_Formated_df_Keff(df1, self.editor, ' K EFFECTIVE VS BATCH ', 1)
                    try:
                        df1 = pd.DataFrame({'batch': [i+1 for i in range(n)], 'Entropy': sp.entropy.tolist()})
                        self.Print_Formated_df_Keff(df1, self.editor, '   SHANNON  ENTROPY   ', 1)
                    except:
                        pass
                else:
                    self.showDialog('Warning', 'Select Tally first!')
            else:
                self.showDialog('Warning', 'Select a valid StatePoint file first!')
                return
        except:
            return

    def Print_Formated_df(self, df, tally_id, editor):
        columns_header = []
        LTOT = 0
        for key in df.keys():
            if type(key) is tuple:
                if 'mesh' in key[0]:
                    KEY = key[0]
                    KEY1 = key[1]
                else:
                    KEY = key[0]
                    KEY1 = ''
            else:
                KEY = key
                KEY1 = ''
            """if KEY1 in ['x', 'y', 'z']:   #'mesh' in key:
                pass"""
            if 'mesh' in KEY:
                FMT = '{:<20}'
            elif KEY in ['surface', 'cell', 'cellfrom', 'cellborn', 'universe', 'material', 'collision']:
                FMT = '{:<13d}'
            elif KEY in ['distribcell']:
                FMT = '{:<14d}'
            elif KEY in ['delayedgroup']:
                FMT = '{:<20d}'
            elif KEY in ['energy low [eV]', 'energy high [eV]', 'energyout low [eV]', 'energyout high [eV]', 
                       'polar low [rad]', 'polar high [rad]', 'azimuthal low [rad]',
                       'azimuthal high [rad]', 'time low [s]', 'time high [s]']:
                FMT = '{:<20.3e}'
            elif KEY in ['mu low', 'mu high', "mean", "std. dev."]:
                FMT = '{:<22.3e}'
            elif KEY in ['nuclide', 'particle', 'legendre', 'zernike']:
                FMT = '{:<14}'
            elif KEY in ['score', 'spatiallegendre', 'sphericalharmonics', 'zernikeradial']:
                FMT = '{:<25}'
            elif KEY in ['multiplier']:
                FMT = '{:<16.6e}'
            elif 'level' in KEY:
                FMT = '{:<10d}'
            #df.loc[:, key] = df[key].map(FMT.format)
            df[key] = df[key].map(FMT.format)
            try:
                LJUST = int(FMT.split('<')[1].split('.')[0].replace('d', '').replace('}', ''))
            except:
                LJUST = 20
            LTOT += LJUST
            if type(key) is tuple:
                if 'mesh' in key[0]:
                    column_name = str(key).ljust(LJUST)
                else:
                    column_name = key[0].ljust(LJUST)
            else:   
                column_name = key.ljust(LJUST)
            columns_header.append(column_name)

        LTOT += 30
        LTOT05 = int(LTOT / 1.5) 
        df.columns = columns_header             
        
        cursor = editor.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText('*'*LTOT + '\n')
        if self.Normalization:
            cursor.insertText('\n' + ' '*int(LTOT05 * 0.66) + 'Tally ' + str(tally_id) + ' results to be plotted after normalization\n' + '\n')
        else:
            if self.Display:
                cursor.insertText('\n' + ' '*int(LTOT05 * 0.7) + 'Tally ' + str(tally_id) + ' results to be plotted\n' + '\n')
            else:
                cursor.insertText('\n\n' + '*'*int(LTOT05 * 0.66) + ' TALLY SUMMARY ' + '*'*int(LTOT05 * 0.66) + '\n\n')
                cursor.insertText(str(self.tally) + '\n\n') 
                cursor.insertText('*'*int(LTOT05 * 0.66) + ' TALLY RESULTS ' + '*'*int(LTOT05 * 0.66) + '\n\n\n')
                cursor.insertText(' '*LTOT05 + 'Tally id : ' + str(tally_id) + '\n')
        
        cursor.insertText('*'*LTOT + '\n')
        cursor.insertText(df.to_csv(sep='\t', index=False)) 
        cursor.insertText('*'*LTOT + '\n\n')
        editor.setTextCursor(cursor)

    def Print_Formated_df_Keff(self, df, editor, TITLE, j):
        cursor = editor.textCursor()
        cursor.movePosition(cursor.End)

        if j == 0:
            cursor.insertText('*'*60 + ' K EFFECTIVE ' + '*'*60 + '\n')
            for key in df.keys():
                if key in ['mean', 'std_dev']:
                    #df.loc[:, key] = df[key].map('{:<20.6f}'.format)
                    df[key] = df[key].map('{:<20.6f}'.format)
        elif j == 1:
            cursor.insertText('*'*55 + TITLE + '*'*55 + '\n')
            for key in df.keys():
                if 'batch' in key:
                    #df.loc[:, key] = df[key].map('{:d}'.format)
                    df[key] = df[key].map('{:d}'.format)
                elif 'Keff' in key or 'Entropy' in key:
                    #df.loc[:, key] = df[key].map('{:<20.6f}'.format)
                    df[key] = df[key].map('{:<20.6f}'.format)
        columns_header = [column_name for column_name in df.keys()]
        df.columns = columns_header  
                      
        cursor.insertText(df.to_csv(sep='\t', index=False)) 
        cursor.insertText('*'*134 + '\n')
        editor.setTextCursor(cursor)

    def SelectFilter(self):
        for elm in self.buttons:
            elm.setEnabled(False)
        self.Graph_Layout_CB.setEnabled(False)
        self.score_plot_PB.setEnabled(False)
        self.Mesh_xy_RB.hide()
        self.Mesh_xz_RB.hide()
        self.Mesh_yz_RB.hide()
        self.spinBox.hide()
        self.spinBox_2.hide()
        self.xlabel.setText('xlabel')
        self.ylabel.setText('ylabel')
        self.score_plot_PB.setText('plot data')
        self.Curve_title.clear()
        self.Curve_xLabel.clear()
        self.Curve_yLabel.clear()
        self.Curve_y2Label.clear()

        if self.Tally_id_comboBox.currentIndex() > 0 and 'Keff' not in self.Tally_id_comboBox.currentText():
            self.tally_id = int(self.Tally_id_comboBox.currentText())
            tally_id = self.tally_id
            self.tally = sp.get_tally(id=tally_id)
            tally = self.tally 
            try:
                for idx in range(self.n_filters):
                    self.Bins_comboBox[idx].clear()
            except:
                pass

            if self.Filters_comboBox.currentIndex() > 0:
                if 'MeshFilter' in self.Filter_names:
                    df_KEYS = [key[0] for key in self.df_Keys]
                else:
                    df_KEYS = [key for key in self.df_Keys]
                for idx in range(self.n_filters):
                    filter_name = self.Tallies[tally_id]['filter_names'][idx]
                    if filter_name != 'MeshFilter':
                        self.label_4.setText('Select bins')
                        filter_id = self.filter_ids[idx]
                        self.Tallies[tally_id][filter_id]['bins'] = [item for item in tally.filters[idx].bins]
                        Bins = self.Tallies[tally_id][filter_id]['bins']
                        if 'energy low [eV]' in df_KEYS and filter_name == 'EnergyFilter':
                            first = [item[0] for item in Bins]
                            last = [item[1] for item in Bins]
                            self.Checked_energies_Low = first
                            self.Checked_energies_High = last
                            bins = [str(("{:.3E}".format(x), "{:.3E}".format(y),)).replace("'", "") for x, y in
                                    zip(first, last)]
                        elif 'energyout low [eV]' in df_KEYS and filter_name == 'EnergyoutFilter':                            
                            first = [item[0] for item in Bins]
                            last = [item[1] for item in Bins]
                            self.Checked_energiesout_Low = first
                            self.Checked_energiesout_High = last
                            bins = [str(("{:.3E}".format(x), "{:.3E}".format(y),)).replace("'", "") for x, y in
                                    zip(first, last)]
                        elif 'mu low' in df_KEYS and filter_name == 'MuFilter':
                            first = [item[0] for item in Bins]
                            last = [item[1] for item in Bins]
                            self.Checked_mu_Low = first
                            self.Checked_mu_High = last
                            bins = [str(("{:.3f}".format(x), "{:.3f}".format(y),)).replace("'", "") for x, y in
                                    zip(first, last)]
                        elif 'polar low [rad]' in df_KEYS and filter_name == 'PolarFilter':
                            first = [item[0] for item in Bins]
                            last = [item[1] for item in Bins]
                            self.Checked_polar_Low = first
                            self.Checked_polar_High = last
                            bins = [str(("{:.3f}".format(x), "{:.3f}".format(y),)).replace("'", "") for x, y in
                                    zip(first, last)]
                        elif 'azimuthal low [rad]' in df_KEYS and filter_name == 'AzimuthalFilter':
                            first = [item[0] for item in Bins]
                            last = [item[1] for item in Bins]
                            self.Checked_azimuthal_Low = first
                            self.Checked_azimuthal_High = last
                            bins = [str(("{:.3f}".format(x), "{:.3f}".format(y),)).replace("'", "") for x, y in
                                    zip(first, last)]
                        elif 'time low [s]' in df_KEYS and filter_name == 'TimeFilter':
                            first = [item[0] for item in Bins]
                            last = [item[1] for item in Bins]
                            self.Checked_time_Low = first
                            self.Checked_time_High = last
                            bins = [str(("{:.3f}".format(x), "{:.3f}".format(y),)).replace("'", "") for x, y in
                                    zip(first, last)]
                        else:
                            for KEY in df_KEYS:
                                if 'distribcell' in KEY[0] and filter_name == 'DistribcellFilter':
                                    bins = [str(item) for item in range(len(self.tally.mean))]
                                if KEY in ['cell', 'cellfrom', 'cellborn', 'surface', 'universe', 'material', 
                                            'collision', 'particle', 'legendre', 'spatiallegendre', 
                                            'sphericalharmonics', 'delayedgroup', 'zernike', 'zernikeradial']:
                                    self.Curve_title.setText(self.Tally_name_LE.text())
                                    bins = sorted([str(item) for item in Bins])
                        self.Tallies[tally_id][filter_id]['bins'] = bins
                        self.Bins_comboBox[idx].addItem('Select ' + self.Tallies[tally_id]['filter_names'][idx] + ' bins')
                        self.Bins_comboBox[idx].addItem('All bins')
                        self.Bins_comboBox[idx].model().item(0).setEnabled(False)
                        self.Bins_comboBox[idx].addItems(bins)
                        try:
                            if self.Tallies[tally_id][filter_id]['Checked_bins_indices']:
                                for j in self.Tallies[tally_id][filter_id]['Checked_bins_indices']: 
                                    self.Bins_comboBox[idx].setItemChecked(j, False)   # (j, True)
                            else:
                                for i in range(len(bins) + 1):
                                    self.Bins_comboBox[idx].setItemChecked(i, False)
                        except:
                            self.showDialog('Warning', 'Filter bins not checked!')
                    else:
                        self.idx = idx
                        self.filter_name = filter_name
                
                if 'MeshFilter' in self.Filter_names:
                    self.SelectFilterMesh()
                else:         
                    self.Mesh_xy_RB.hide()
                    self.Mesh_xz_RB.hide()
                    self.Mesh_yz_RB.hide()
                    self.spinBox.hide()
                    self.spinBox_2.hide()
                    self.Curve_title.clear()                     
                    self.xlabel.setText('xlabel')
                    self.ylabel.setText('ylabel')

        elif 'Keff' in self.Tally_id_comboBox.currentText():
            try:
                self.Bins_comboBox[0].clear()
            except:
                pass
            if self.Filters_comboBox.currentIndex() > 0:
                self.Bins_comboBox[0].addItem('Select batches')               
                self.Bins_comboBox[0].model().item(0).setEnabled(False)            
                self.Bins_comboBox[0].addItem('All bins')
                self.Bins_comboBox[0].addItems([str(i) for i in self.batches])
                self.Bins_comboBox[0].currentIndexChanged.connect(self.Activate_Plot_BT)
                for bt in self.buttons:
                    bt.setEnabled(True) 
                #self.score_plot_PB.setEnabled(True)
                self.Curve_title.setText(self.Tally_name_LE.text())
                self.Curve_xLabel.setText('batches')
                self.Curve_yLabel.setText('Keff')
                self.Graph_type_CB.setEnabled(True)
                self.Plot_by_CB.setEnabled(True)
                try:
                    if self.Checked_batches_bins:
                        for j in self.Checked_batches_bins: 
                            self.Bins_comboBox[0].setItemChecked(j, False)
                    else:
                        for i in range(len(self.batches) + 1):
                            self.Bins_comboBox[0].setItemChecked(i, False)
                except:
                    self.showDialog('Warning', 'Filter bins not checked!')
            else:
                self.Graph_type_CB.setEnabled(False)
                self.Plot_by_CB.setEnabled(False)
                self.score_plot_PB.setEnabled(False)
                try:
                    self.Bins_comboBox[0].clear()
                except:
                    pass
    
    def Activate_Plot_BT(self):
        if self.Bins_comboBox[0].checkedItems():
            self.score_plot_PB.setEnabled(True)
        else:
            self.score_plot_PB.setEnabled(False)

    def SelectFilterMesh(self):
        tally_id = self.tally_id
        tally = self.tally 
        idx = self.idx
        filter_name = self.filter_name
        filter_id = self.filter_ids[idx]   
        self.Mesh_xy_RB.show()
        self.Mesh_xz_RB.show()
        self.Mesh_yz_RB.show()
        self.spinBox.show()
        self.spinBox_2.show()
        self.Mesh_xy_RB.setChecked(True)
        mesh = tally.filters[idx].mesh
        self.mesh_id = mesh.id
        #self.mesh_type = str(mesh).split('\n')[0]
        self.mesh_type = type(mesh).__name__
        self.mesh_name = tally.name
        self.mesh_dimension = mesh.dimension
        self.mesh_n_dim = mesh.n_dimension 
        self.mesh_key = f'mesh {tally.filters[idx].mesh.id}'
        """if self.mesh_type == 'CylindricalMesh':
            self.Curve_xLabel.clear()
            self.Curve_yLabel.clear()
        else:
            self.Curve_xLabel.setText('x/cm')
            self.Curve_yLabel.setText('y/cm')  """      
        print('*******************************************************************************************')
        print('********************                           Mesh summary                             ******************')
        print('*******************************************************************************************\n')
        if self.mesh_type in ['RegularMesh', 'RectilinearMesh']:
            if self.mesh_type == 'RectilinearMesh':
                self.mesh_LL = tally.filters[idx].mesh.lower_left
                self.mesh_UR = tally.filters[idx].mesh.upper_right
                XX = tally.filters[idx].mesh.x_grid; dXX = np.diff(XX)
                YY = tally.filters[idx].mesh.y_grid; dYY = np.diff(YY)
                ZZ = tally.filters[idx].mesh.z_grid; dZZ = np.diff(ZZ)                        
                self.x = XX[:-1] + dXX * 0.5
                self.y = YY[:-1] + dYY * 0.5
                self.z = ZZ[:-1] + dZZ * 0.5
                print('id               :  ', self.mesh_id)
                print('name            :  ', self.mesh_name)
                print('type            :  ', self.mesh_type)
                print('dimension     :  ', self.mesh_n_dim)
                print('voxels          :  ', self.mesh_dimension)
                print('lower_left   :  ', self.mesh_LL)
                print('upper_right  :  ', self.mesh_UR, '\n')
                print('x grid      :  ', self.x.tolist())
                print('y grid      :  ', self.y.tolist())
                print('z grid      :  ', self.z.tolist(), '\n')
                print('Tally filters : \n', tally.filters, '\n')
                print('*******************************************************************************************\n')
                
                self.mesh_ids = tally.filters[idx].bins
                self.id_step = self.mesh_dimension[0] * self.mesh_dimension[1]
                ij_indices = [(self.mesh_ids[i][0], self.mesh_ids[i][1],) for i in range(self.id_step)]
                ik_indices = []
                for k in range(self.mesh_dimension[2]):
                    ik_indices += [(self.mesh_ids[i][0], self.mesh_ids[i][2],) for i in
                                range(k * self.id_step, (k * self.id_step + self.mesh_dimension[0]))]
                jk_indices = [(self.mesh_ids[i][1], self.mesh_ids[i][2],) for i in
                            range(0, len(self.mesh_ids), self.mesh_dimension[0])]
                self.Tallies[tally_id][filter_id]['ik_indices'] = ik_indices
                self.Tallies[tally_id][filter_id]['jk_indices'] = jk_indices
                self.Tallies[tally_id][filter_id]['ij_indices'] = ij_indices
                
                if self.Mesh_xy_RB.isChecked():
                    if len(tally.filters[idx].mesh._grids) == 3:
                        self.list_axis = ['slice at z = ' + str("{:.1E}cm".format(z_)) for z_ in self.z]
                    else:
                        self.list_axis = ['z axis integrated']
                elif self.Mesh_xz_RB.isChecked():
                    self.id_step1 = self.mesh_dimension[0] * self.mesh_dimension[2]
                    self.list_axis = ['slice at y = ' + str("{:.1E}cm".format(y_)) for y_ in self.y]
                elif self.Mesh_yz_RB.isChecked():
                    self.id_step2 = self.mesh_dimension[1] * self.mesh_dimension[2]
                    self.list_axis = ['slice at x = ' + str("{:.1E}cm".format(x_)) for x_ in self.x]
                bins = self.list_axis
                self.Tallies[tally_id][filter_id]['bins'] = bins
                self.label_4.setText('Select bins')
                filter_id = self.filter_ids[idx]
                self.Bins_comboBox[idx].addItem('Select ' + self.Tallies[tally_id]['filter_names'][idx] + ' bins')
                self.Bins_comboBox[idx].addItem('All bins')
                self.Bins_comboBox[idx].model().item(0).setEnabled(False)
                self.Bins_comboBox[idx].addItems(bins)
                if 'MeshFilter' in self.Filter_names and len(tally.filters[idx].mesh._grids) == 2:
                    self.Bins_comboBox[self.Filters_comboBox.currentIndex() - 1].setCurrentIndex(2)
                try:
                    if self.Tallies[tally_id][filter_id]['Checked_bins_indices']:
                        for j in self.Tallies[tally_id][filter_id]['Checked_bins_indices']: 
                            self.Bins_comboBox[idx].setItemChecked(j, False)   # (j, True)
                    else:
                        for i in range(len(bins) + 1):
                            self.Bins_comboBox[idx].setItemChecked(i, False)
                except:
                    self.showDialog('Warning', 'Filter bins not checked!')
            elif self.mesh_type == 'RegularMesh':
                mesh_width = tally.filters[idx].mesh.width
                self.mesh_LL = tally.filters[idx].mesh.lower_left
                self.mesh_UR = tally.filters[idx].mesh.upper_right
                self.mesh_ids = tally.filters[idx].bins
                mesh_grid = tally.filters[idx].mesh._grids
                if len(mesh_grid) == 3:
                    self.x = mesh_grid[0][:-1] + mesh_width[0] * 0.5
                    self.y = mesh_grid[1][:-1] + mesh_width[1] * 0.5
                    self.z = mesh_grid[2][:-1] + mesh_width[2] * 0.5  
                    self.Mesh_xz_RB.setEnabled(True) 
                    self.Mesh_yz_RB.setEnabled(True) 
                else:
                    self.x = mesh_grid[0][:-1] + mesh_width[0] * 0.5
                    self.y = mesh_grid[1][:-1] + mesh_width[1] * 0.5
                    self.z = ['z axis integrated']
                    self.mesh_dimension = np.append(self.mesh_dimension, 1)
                    self.Mesh_xz_RB.setEnabled(False) 
                    self.Mesh_yz_RB.setEnabled(False)   
                # ******************************************************************************                     
                print('id                :  ', self.mesh_id)
                print('name          :  ', self.mesh_name)
                print('type            :  ', self.mesh_type)
                print('dimension   :  ', self.mesh_n_dim)
                print('voxels         :  ', self.mesh_dimension)
                print('width          :  ', mesh_width)
                print('lower_left     :  ', self.mesh_LL)
                print('upper_right  :  ', self.mesh_UR, '\n')
                print('x grid      :  ', self.x)
                print('y grid      :  ', self.y)
                print('z grid      :  ', self.z, '\n')
                print('Tally filters : \n', tally.filters, '\n')
                print('*******************************************************************************************\n')

                self.Tallies[tally_id][filter_id]['slice_x'] = self.x
                self.Tallies[tally_id][filter_id]['slice_y'] = self.y
                self.Tallies[tally_id][filter_id]['slice_z'] = self.z
                self.id_step = self.mesh_dimension[0] * self.mesh_dimension[1]
                ij_indices = [(self.mesh_ids[i][0], self.mesh_ids[i][1],) for i in range(self.id_step)]
                if len(tally.filters[idx].mesh._grids) == 3:   
                    ik_indices = []
                    for k in range(self.mesh_dimension[2]):
                        ik_indices += [(self.mesh_ids[i][0], self.mesh_ids[i][2],) for i in
                                    range(k * self.id_step, (k * self.id_step + self.mesh_dimension[0]))]
                    jk_indices = [(self.mesh_ids[i][1], self.mesh_ids[i][2],) for i in
                                range(0, len(self.mesh_ids), self.mesh_dimension[0])]
                    self.Tallies[tally_id][filter_id]['ik_indices'] = ik_indices
                    self.Tallies[tally_id][filter_id]['jk_indices'] = jk_indices
                    
                self.Tallies[tally_id][filter_id]['ij_indices'] = ij_indices
                
                if self.Mesh_xy_RB.isChecked():
                    if len(tally.filters[idx].mesh._grids) == 3:
                        self.list_axis = ['slice at z = ' + str("{:.1E}cm".format(z_)) for z_ in self.z]
                    else:
                        self.list_axis = ['z axis integrated']
                elif self.Mesh_xz_RB.isChecked():
                    self.id_step1 = self.mesh_dimension[0] * self.mesh_dimension[2]
                    self.list_axis = ['slice at y = ' + str("{:.1E}cm".format(y_)) for y_ in self.y]
                elif self.Mesh_yz_RB.isChecked():
                    self.id_step2 = self.mesh_dimension[1] * self.mesh_dimension[2]
                    self.list_axis = ['slice at x = ' + str("{:.1E}cm".format(x_)) for x_ in self.x]
                bins = self.list_axis
                self.Tallies[tally_id][filter_id]['bins'] = bins
                self.label_4.setText('Select bins')
                filter_id = self.filter_ids[idx]
                self.Bins_comboBox[idx].addItem('Select ' + self.Tallies[tally_id]['filter_names'][idx] + ' bins')
                self.Bins_comboBox[idx].addItem('All bins')
                self.Bins_comboBox[idx].model().item(0).setEnabled(False)
                self.Bins_comboBox[idx].addItems(bins)
                if 'MeshFilter' in self.Filter_names and len(tally.filters[idx].mesh._grids) == 2:
                    self.Bins_comboBox[self.Filters_comboBox.currentIndex() - 1].setCurrentIndex(2)
                try:
                    if self.Tallies[tally_id][filter_id]['Checked_bins_indices']:
                        for j in self.Tallies[tally_id][filter_id]['Checked_bins_indices']: 
                            self.Bins_comboBox[idx].setItemChecked(j, False)   # (j, True)
                    else:
                        for i in range(len(bins) + 1):
                            self.Bins_comboBox[idx].setItemChecked(i, False)
                except:
                    self.showDialog('Warning', 'Filter bins not checked!')
        elif self.mesh_type == 'CylindricalMesh':
            self.mesh_LL = mesh.lower_left
            self.mesh_UR = mesh.upper_right 
            self.r = mesh.r_grid; dr = np.diff(self.r)
            self.phi = mesh.phi_grid; dphi = np.diff(self.phi)
            self.z = mesh.z_grid; dz = np.diff(self.z)  
            self.origin = mesh.origin    
            self.r_center = self.r[:-1] + dr * 0.5                  
            self.phi_center = self.phi[:-1] + dphi * 0.5                  
            self.phi_center = self.phi_center * 180. / np.pi                  
            self.z_center = self.z[:-1] + dz * 0.5   
            self.R_range = [str(self.r[i]) + ' < r < ' + str(self.r[i+1]) for i in range(len(self.r) - 1)]               
            self.Phi_range = [str("{:.1f}°".format(self.phi[i] * 180. / np.pi)) + ' < \u03F4 < ' + str("{:.1f}°".format(self.phi[i+1] * 180. / np.pi)) for i in range(len(self.phi) - 1)]               
            self.Z_range = [str("{:.1E}cm".format(self.z[i])) + ' < z < ' + str("{:.1E}cm".format(self.z[i+1])) for i in range(len(self.z) - 1)]               
            ##############################################################
            print('id               :  ', self.mesh_id)
            print('name            :  ', self.mesh_name)
            print('type            :  ', self.mesh_type)
            print('dimension     :  ', self.mesh_n_dim)
            print('voxels          :  ', self.mesh_dimension)
            print('lower_left   :  ', self.mesh_LL)
            print('upper_right  :  ', self.mesh_UR, '\n')
            print('r grid      :  ', self.r.tolist())
            print('phi grid      :  ', self.phi.tolist())
            print('z grid      :  ', self.z.tolist(), '\n')
            print('Tally filters : \n', tally.filters, '\n')
            print('*******************************************************************************************\n')
            
            self.mesh_ids = tally.filters[idx].bins
            self.id_step = self.mesh_dimension[0] * self.mesh_dimension[1]
            
            ij_indices = [(self.mesh_ids[i][0], self.mesh_ids[i][1],) for i in range(self.id_step)]
            ik_indices = []
            for k in range(self.mesh_dimension[2]):
                ik_indices += [(self.mesh_ids[i][0], self.mesh_ids[i][2],) for i in
                            range(k * self.id_step, (k * self.id_step + self.mesh_dimension[0]))]
            jk_indices = [(self.mesh_ids[i][1], self.mesh_ids[i][2],) for i in
                        range(0, len(self.mesh_ids), self.mesh_dimension[0])]
            self.Tallies[tally_id][filter_id]['ik_indices'] = ik_indices
            self.Tallies[tally_id][filter_id]['jk_indices'] = jk_indices
            self.Tallies[tally_id][filter_id]['ij_indices'] = ij_indices

            if self.Mesh_xy_RB.isChecked():
                if len(tally.filters[idx].mesh._grids) == 3:
                    #self.list_axis = ['slice at z = ' + str("{:.1E}".format(z_)) for z_ in self.z_center]
                    self.list_axis = ['slice at ' + Z for Z in self.Z_range]
                else:
                    self.list_axis = ['z axis integrated']
            elif self.Mesh_xz_RB.isChecked():
                self.id_step1 = self.mesh_dimension[0] * self.mesh_dimension[2]
                #self.list_axis = ['slice at \u03F4 = ' + str("{:.1f}".format(phi_)) for phi_ in self.phi_center]
                self.list_axis = ['slice at ' + Phi for Phi in self.Phi_range]
            """elif self.Mesh_yz_RB.isChecked():
                self.id_step2 = self.mesh_dimension[1] * self.mesh_dimension[2]
                self.list_axis = ['slice at r = ' + str("{:.1E}".format(r_)) for r_ in self.r_center]"""
            bins = self.list_axis
            self.Tallies[tally_id][filter_id]['bins'] = bins
            self.label_4.setText('Select bins')
            filter_id = self.filter_ids[idx]
            self.Bins_comboBox[idx].addItem('Select ' + self.Tallies[tally_id]['filter_names'][idx] + ' bins')
            self.Bins_comboBox[idx].addItem('All bins')
            self.Bins_comboBox[idx].model().item(0).setEnabled(False)
            self.Bins_comboBox[idx].addItems(bins)
            if 'MeshFilter' in self.Filter_names and len(tally.filters[idx].mesh._grids) == 2:
                self.Bins_comboBox[self.Filters_comboBox.currentIndex() - 1].setCurrentIndex(2)
            try:
                if self.Tallies[tally_id][filter_id]['Checked_bins_indices']:
                    for j in self.Tallies[tally_id][filter_id]['Checked_bins_indices']: 
                        self.Bins_comboBox[idx].setItemChecked(j, False)   # (j, True)
                else:
                    for i in range(len(bins) + 1):
                        self.Bins_comboBox[idx].setItemChecked(i, False)
            except:
                self.showDialog('Warning', 'Filter bins not checked!')
        
    def SelectBins(self):
        if self.Tally_id_comboBox.currentIndex() > 0 and 'Keff' not in self.Tally_id_comboBox.currentText():
            tally_id = int(self.Tally_id_comboBox.currentText())
            self.tally = sp.get_tally(id=tally_id)
            _f = h5py.File(self.sp_file, 'r')
            tallies_group = _f['tallies']
            group = tallies_group[f'tally {tally_id}']
            self.n_filters = group['n_filters'][()]
            tally = self.tally
            for idx in range(self.n_filters):   
                if self.Filters_comboBox.currentIndex() > 0:
                    filter_id = self.filter_ids[idx]
                    filter_name = self.Filter_names[idx]
                    self.Filter_Bins_Select(tally_id, filter_id)
                    self.Bins_comboBox[idx].setCurrentIndex(0)
        elif self.Tally_id_comboBox.currentIndex() > 0 and 'Keff' in self.Tally_id_comboBox.currentText():
            self.Filter_Bins_Select(0, 0)
            self.Bins_comboBox[0].setCurrentIndex(0)
            
    def Filter_Bins_Select(self, tally_id, filter_id):
        try:
            if tally_id == 0 and filter_id == 0:
                if self.Bins_comboBox[0].currentIndex() == 1:
                    if self.Bins_comboBox[0].checkedItems():
                        self.Checked_batches_bins = self.Bins_comboBox[0].checkedItems()
                    else:
                        self.Checked_batches_bins = []
                    if self.Checked_batches_bins:
                        self.Checked_batches_bins.pop(0)
                elif self.Bins_comboBox[0].currentIndex() > 1:
                    self.Checked_batches_bins = self.Bins_comboBox[0].checkedItems()
                self.Checked_batches = [elm for elm in self.batches if self.batches.index(elm) + 2 in self.Checked_batches_bins]
            else:
                idx = self.filter_ids.index(filter_id)
                filter_name = self.Tallies[tally_id]['filter_names'][idx]
                if self.Bins_comboBox[idx].currentIndex() == 1:
                    if self.Bins_comboBox[idx].checkedItems():
                        self.Tallies[tally_id][filter_id]['Checked_bins_indices'] = self.Bins_comboBox[idx].checkedItems()
                    else:
                        self.Tallies[tally_id][filter_id]['Checked_bins_indices'] = []
                        self.Tallies[tally_id][filter_id]['bin'] = []
                    if self.Tallies[tally_id][filter_id]['Checked_bins_indices']:
                        self.Tallies[tally_id][filter_id]['Checked_bins_indices'].pop(0)
                elif self.Bins_comboBox[idx].currentIndex() > 1:
                    self.Tallies[tally_id][filter_id]['Checked_bins_indices'] = self.Bins_comboBox[idx].checkedItems()
                indices = self.Tallies[tally_id][filter_id]['Checked_bins_indices']
                lst = self.Tallies[tally_id][filter_id]['bins']
                self.Tallies[tally_id][filter_id]['Checked_bins'] = [elm for elm in lst if lst.index(elm) + 2 in indices]

                if filter_name == 'MeshFilter':  
                    self.checked_bins_indices = self.Tallies[tally_id][filter_id]['Checked_bins_indices']
                    #self.checked_bins_indices = [i - 2 for i in self.Tallies[tally_id][filter_id]['Checked_bins_indices']]
                    self.Tallies[tally_id][filter_id]['ijk_indices'] = {}
                    if self.Mesh_xy_RB.isChecked():
                        for bin_id in range(len(self.checked_bins_indices)):
                            self.Tallies[tally_id][filter_id]['ijk_indices'][self.checked_bins_indices[bin_id]] = []
                            k = self.checked_bins_indices[bin_id]
                            ijk_indices = [item + (k,) for item in self.Tallies[tally_id][filter_id]['ij_indices']]
                            self.Tallies[tally_id][filter_id]['ijk_indices'][self.checked_bins_indices[bin_id]] = ijk_indices
                    elif self.Mesh_xz_RB.isChecked():
                        for bin_id in range(len(self.checked_bins_indices)):
                            self.Tallies[tally_id][filter_id]['ijk_indices'][self.checked_bins_indices[bin_id]] = []
                            j = self.checked_bins_indices[bin_id]
                            ijk_indices = [item[:1] + (j,) + item[1:] for item in self.Tallies[tally_id][filter_id]['ij_indices']]
                            self.Tallies[tally_id][filter_id]['ijk_indices'][self.checked_bins_indices[bin_id]] = ijk_indices
                    elif self.Mesh_yz_RB.isChecked():
                        for bin_id in range(len(self.checked_bins_indices)):
                            self.Tallies[tally_id][filter_id]['ijk_indices'][self.checked_bins_indices[bin_id]] = []
                            i = self.checked_bins_indices[bin_id]
                            ijk_indices = [(i,) + item for item in self.Tallies[tally_id][filter_id]['ij_indices']]
                            self.Tallies[tally_id][filter_id]['ijk_indices'][self.checked_bins_indices[bin_id]] = ijk_indices
                elif filter_name == 'CellFilter':
                    self.Checked_cells = self.Tallies[tally_id][filter_id]['Checked_bins']
                elif filter_name == 'CellFromFilter':
                    self.Checked_cellsfrom = self.Tallies[tally_id][filter_id]['Checked_bins']
                elif filter_name == 'CellBornFilter':
                    self.Checked_cellsborn = self.Tallies[tally_id][filter_id]['Checked_bins']
                elif filter_name == 'DistribcellFilter':
                    self.Checked_distribcell = self.Tallies[tally_id][filter_id]['Checked_bins'] 
                elif filter_name == 'SurfaceFilter':
                    self.Checked_surfaces = self.Tallies[tally_id][filter_id]['Checked_bins']
                elif filter_name == 'EnergyFilter':
                    self.Checked_energies_Low = self.Tallies[tally_id][filter_id]['Checked_bins']
                elif filter_name == 'EnergyoutFilter':
                    self.Checked_energiesout_Low = self.Tallies[tally_id][filter_id]['Checked_bins']
                elif filter_name == 'MuFilter':
                    self.Checked_mu_Low = self.Tallies[tally_id][filter_id]['Checked_bins']
                elif filter_name == 'UniverseFilter':
                    self.Checked_universes = self.Tallies[tally_id][filter_id]['Checked_bins']
                elif filter_name == 'MaterialFilter':
                    self.Checked_materials = self.Tallies[tally_id][filter_id]['Checked_bins']
                elif filter_name == 'CollisionFilter':
                    self.Checked_collisions = self.Tallies[tally_id][filter_id]['Checked_bins']
                elif filter_name == 'ParticleFilter':
                    self.Checked_particles = self.Tallies[tally_id][filter_id]['Checked_bins']
                elif filter_name == 'PolarFilter':
                    self.Checked_polar_Low = self.Tallies[tally_id][filter_id]['Checked_bins']
                elif filter_name == 'AzimuthalFilter':
                    self.Checked_azimuthal_Low = self.Tallies[tally_id][filter_id]['Checked_bins']
                elif filter_name == 'LegendreFilter':
                    self.Checked_legendre = self.Tallies[tally_id][filter_id]['Checked_bins']
                elif filter_name == 'SpatialLegendreFilter':
                    self.Checked_spatiallegendre = self.Tallies[tally_id][filter_id]['Checked_bins']
                elif filter_name == 'SphericalHarmonicsFilter':
                    self.Checked_sphericalharmonics = self.Tallies[tally_id][filter_id]['Checked_bins']
                elif filter_name == 'TimeFilter':
                    self.Checked_times = self.Tallies[tally_id][filter_id]['Checked_bins']
                elif filter_name == 'DelayedGroupFilter':
                    self.Checked_delayed = self.Tallies[tally_id][filter_id]['Checked_bins']
                elif filter_name == 'ZernikeFilter':
                    self.Checked_zernike = self.Tallies[tally_id][filter_id]['Checked_bins']
                elif filter_name == 'ZernikeRadialFilter':
                    self.Checked_zernikeradial = self.Tallies[tally_id][filter_id]['Checked_bins']
        except:
            return

    def Display_filters(self):
        self.tabWidget_2.setCurrentIndex(0)
        cursor = self.editor.textCursor()
        cursor.movePosition(cursor.End)
        #Checked_Bins_Indices = [i - 2 for i in self.checked_bins_indices]
        if os.path.isfile(self.sp_file):
            if self.Tally_id_comboBox.currentIndex() > 0 and 'Keff' not in self.Tally_id_comboBox.currentText():
                Checked_Bins_Indices = [i - 2 for i in self.checked_bins_indices]
                tally_id = int(self.Tally_id_comboBox.currentText())
                if self.Filters_comboBox.currentIndex() > 0:
                    for id in self.filter_ids:
                        Filter_Type = self.Tallies[tally_id]['filter_types'][self.filter_ids.index(id)]
                        filter_id = id  
                        idx = self.filter_ids.index(id)
                        self.Filter_Bins_Select(tally_id, filter_id)
                        cursor.insertText('\n************************************************************' +
                            '\nTally Id            : ' + str(tally_id) +
                            '\nFilter Id           : ' + str(filter_id) +
                            '\nFilter name         : ' + str(self.Filter_names[idx]) +
                            '\nFilter type         : ' + Filter_Type +    
                            '\nChecked bins        : ' + str(self.Tallies[tally_id][filter_id]['Checked_bins']).replace("'", "") +
                            '\nChecked bins indices: ' + str(Checked_Bins_Indices) +
                            '\n************************************************************')
            elif self.Tally_id_comboBox.currentIndex() > 0 and 'Keff' in self.Tally_id_comboBox.currentText():
                self.Filter_Bins_Select(0, 0)
                cursor.insertText('\n************************************************************' +
                    '\nKeff vs batches' +            
                    '\nChecked batches     : ' + str(self.Checked_batches) +
                    '\nChecked batches bins: ' + str(self.Checked_batches_bins) +
                    '\n************************************************************')
                self.Bins_comboBox[0].setCurrentIndex(0)  
                self.Plot_by_CB.setEnabled(True)
                #self.Graph_type_CB.setEnabled(True)
                self.score_plot_PB.setEnabled(True)
            else:
                self.showDialog('Warning', 'Select Tally first!')
        else:
            self.showDialog('Warning', 'Select your StatePoint file first !')

        self.editor.setTextCursor(cursor)

    def SelectScores(self):        
        if self.Tally_id_comboBox.currentIndex() > 0 and 'Keff' not in self.Tally_id_comboBox.currentText():
            tally_id = int(self.Tally_id_comboBox.currentText())
            if self.Scores_comboBox.currentIndex() > 0:
                if self.Scores_comboBox.currentText() == 'All scores':
                    selected_score = self.scores
                else:
                    selected_score = list(filter(None, self.Scores_List_LE.text().split(' ')))
                    selected_score.append(str(self.Scores_comboBox.currentText()))
                selected_score = sorted(selected_score)
                self.selected_scores = list(dict.fromkeys(selected_score))
                text = ' '.join(self.selected_scores)
                self.Scores_List_LE.clear()
                self.Scores_List_LE.setText(text)

    def SelectNuclides(self):
        if self.Tally_id_comboBox.currentIndex() > 0 and 'Keff' not in self.Tally_id_comboBox.currentText():
            tally_id = int(self.Tally_id_comboBox.currentText())
            if self.Nuclides_comboBox.currentIndex() > 0:
                if self.Nuclides_comboBox.currentText() == 'All nuclides':
                    selected_nuclides = self.nuclides
                    self.Nuclides_List_LE.setText(str([nuclide for nuclide in selected_nuclides]))
                else:
                    selected_nuclides = list(filter(None, self.Nuclides_List_LE.text().split(' ')))
                    selected_nuclides.append(str(self.Nuclides_comboBox.currentText()))
                selected_nuclides = sorted(selected_nuclides)
                self.selected_nuclides = list(dict.fromkeys(selected_nuclides))
                text = ' '.join(selected_nuclides)
                self.Nuclides_List_LE.clear()
                self.Nuclides_List_LE.setText(text)
                self.Tallies[tally_id]['selected_nuclides'] = selected_nuclides

    def Clear_nuclides(self):
        self.Nuclides_List_LE.clear()
        self.Nuclides_comboBox.setCurrentIndex(0)

    def Display_scores(self):
        self.Display = True
        self.Normalization = False
        self.Tally_Normalizing_CB.setChecked(False)
        self.Q_LE.setText('193.')
        self.Nu_LE.setText('2.45')
        self.Curve_title.clear()
        self.Curve_y2Label.clear()
        if not self.sp_file:
            self.showDialog('Warning', 'Select a valid StatePoint file first!')
            return
        if self.Tally_id_comboBox.currentIndex() == 0: 
            self.showDialog('Warning', "Select tally's id first !")
            return

        self.tally_id = int(self.Tally_id_comboBox.currentText())

        if self.n_filters == 0:                                   # scores are not filtered
            self.filter_ids = [0]
            self.filter_id = 0               
        else:                                 # scores are filtered 
            if self.Filters_comboBox.currentIndex() == 0: 
                self.showDialog('Warning', "Select filter's id first !")
                return            
            for id in self.filter_ids:
                self.filter_id = id
                if not self.Tallies[self.tally_id][self.filter_id]['Checked_bins_indices']:
                    self.showDialog('Warning', 'Check filter bins first !')
                    return
        
        if not self.Nuclides_List_LE.text().strip():
            self.showDialog('Warning', 'Select nuclides first!')
            return
        if not self.Scores_List_LE.text().strip():
            self.showDialog('Warning', 'Select score first!')
            return     

        self.tabWidget_2.setCurrentIndex(0)
        self.Graph_Layout_CB.setEnabled(True)
        self.Graph_Layout_CB.setCurrentIndex(0)
        self.Add_error_bars_CB.setChecked(False) 
               
        df = self.tally.get_pandas_dataframe(float_format = '{:.3e}')  #'{:.6f}')
        
        self.df = df.sort_values(by=df.keys().tolist()[:-2])  #[::-1])
        # list of selected nuclides
        self.selected_nuclides = list(filter(None, self.Nuclides_List_LE.text().split(' ')))
        self.selected_nuclides = sorted(self.selected_nuclides)
        self.selected_nuclides = list(dict.fromkeys(self.selected_nuclides))
        for elm in self.selected_nuclides:
            if elm not in self.nuclides:
                self.showDialog('Warning', 'nuclide : ' + str(elm) + ' not tallied for current tally!')
                return
        self.Tallies[self.tally_id]['selected_nuclides'] = self.selected_nuclides        
        # list of selected scores
        self.selected_scores = list(filter(None, self.Scores_List_LE.text().split(' ')))
        self.selected_scores = sorted(self.selected_scores)
        self.selected_scores = list(dict.fromkeys(self.selected_scores))
        for elm in self.selected_scores:
            if elm not in self.scores:
                self.showDialog('Warning', 'score : ' + str(elm) + ' not tallied for current tally!')
                return
        self.Tallies[self.tally_id]['selected_scores'] = self.selected_scores

        self.Plot_by_CB.clear()
        self.Plot_by_CB.addItem('select item')
        if self.n_filters == 0:                                   # scores are not filtered
            self.Unfiltered_Scores()
            self.Deactivate_Curve_Type()
            self.Curve_xLabel.setText('Nuclides')        
        elif self.n_filters >= 1:                                 # scores are filtered 
           self.Filtered_Scores()
        
        # add keys to Plot_by_CB combobox
        if 'distribcell' in self.df.keys():    #  to be revised
            self.Plot_by_CB.addItem('distribcell')   
            self.Graph_type_CB.addItem('mesh graph')
            # to be modified if ploting works
            index = self.Graph_type_CB.findText('mesh graph')
            self.Graph_type_CB.model().item(index).setEnabled(False)
                
        index = self.Graph_type_CB.findText('mesh graph')
        self.Graph_type_CB.removeItem(index)
        for item in self.df_Keys:
            if 'surface' in self.df_Keys:
                if 'high' in item:
                    self.Plot_by_CB.addItem(item.split(' ')[0] + ' center of bin')
                else:
                    if item != 'nuclide': self.Plot_by_CB.addItem(str(item)) 
            else:  
                if 'high' in item:
                    self.Plot_by_CB.addItem(item.split(' ')[0] + ' center of bin')
                else:
                    self.Plot_by_CB.addItem(str(item))
        if len(self.selected_nuclides) == 1 and self.selected_nuclides[0] != 'total':
            self.Curve_title.setText(self.Tally_name_LE.text() + ' - ' + self.selected_nuclides[0])
        else:
            self.Curve_title.setText(self.Tally_name_LE.text())

        if 'MeshFilter' in self.Filter_names:
            self.Omit_Blank_Graph_CB.setEnabled(True)
        else:
            self.Omit_Blank_Graph_CB.setEnabled(False)
        
        self.Omit_Blank_Graph_CB.setChecked(False)
            
        cursor = self.editor.textCursor()
        cursor.movePosition(cursor.End)

        cursor.insertText('\n' + '*'*27*len(df.keys()) + '\n')
        cursor.insertText(' '*87 + ' tally id : ' + str(self.tally_id))
        cursor.insertText('\n' + '*'*27*len(df.keys()))
        for idx in range(self.n_filters):
            if 'MeshFilter' in self.Filter_names[idx]:
                #Mesh_Filter_idx = self.filter_ids[idx]
                Mesh_Filter_idx = idx #self.filter_ids[idx]
            cursor.insertText('\nTally bins for filter id = ' + str(self.filter_ids[idx]) + ' : ' + str(self.Tallies[self.tally_id][self.filter_ids[idx]]['bins']).replace("'", ""))
            cursor.insertText('\nSelected bins for filter id = ' + str(self.filter_ids[idx]) + ' : ' + str(self.Tallies[self.tally_id][self.filter_ids[idx]]['Checked_bins']).replace("'", ""))
        cursor.insertText('\nTally nuclides : ' + str(self.tally.nuclides))
        cursor.insertText('\nSelected nuclides : ' + str(self.selected_nuclides))
        cursor.insertText('\nTally scores: ' + str(self.tally.scores))
        cursor.insertText('\nSelected scores : ' + str(self.selected_scores))  
        cursor.insertText('\n' + '*'*27*len(df.keys()) + '\n')
        
        self.editor.setTextCursor(cursor)

        self.df_filtered = self.df.loc[(self.df['nuclide'].isin(self.selected_nuclides)) & (self.df['score'].isin(self.selected_scores))]       
        if 'MeshFilter' in self.Filter_names: 
            tally = self.tally
            mesh = tally.filters[Mesh_Filter_idx].mesh
            if self.mesh_type in ['RegularMesh', 'RectilinearMesh']:
                if self.Mesh_xy_RB.isChecked():
                    plot_basis = 'xy'
                elif self.Mesh_xz_RB.isChecked():
                    plot_basis = 'xz'
                elif self.Mesh_yz_RB.isChecked():
                    plot_basis = 'yz'
                # Get voxels volume
                for Slice_index in range(len(self.checked_bins_indices)):
                    if len(tally.shape)  == 3:
                        if plot_basis == "xy":
                            self.slice_volumes = mesh.volumes[:, :, Slice_index].squeeze()
                        elif plot_basis == "xz":
                            self.slice_volumes = mesh.volumes[:, Slice_index, :].squeeze()
                        elif plot_basis == "yz":
                            self.slice_volumes = mesh.volumes[Slice_index, :, :].squeeze()
                    elif len(tally.shape)  == 2:
                        self.slice_volumes = mesh.volumes[:, :].squeeze()
                    slice = self.Tallies[self.tally_id][self.filter_ids[Mesh_Filter_idx]]['Checked_bins'][Slice_index].replace("'", "")
                    print('mesh volumes for ' + str(slice) + '\n' + str(self.slice_volumes))
            elif self.mesh_type in ['CylindricalMesh']:
                if self.Mesh_xy_RB.isChecked():
                    plot_basis = 'rphi'
                else:
                    plot_basis = 'rz'
                # Get voxels volume
                for Slice_index in range(len(self.checked_bins_indices)):
                    if len(tally.shape)  == 3:
                        if plot_basis == "rz":
                            self.slice_volumes = mesh.volumes[:, Slice_index, :].squeeze()
                        elif plot_basis == "rphi": 
                            self.slice_volumes = mesh.volumes[:, :, Slice_index].squeeze()
                    elif len(tally.shape)  == 2:
                        self.slice_volumes = mesh.volumes[:, :].squeeze()
                    slice = self.Tallies[self.tally_id][self.filter_ids[Mesh_Filter_idx]]['Checked_bins'][Slice_index].replace("'", "")
                    print('mesh volumes for ' + str(slice) + '\n' + str(self.slice_volumes))

            for index in range(len(self.df.keys()) - 4):
                key = self.df.keys()[index][0]
                if 'mesh' in key:
                    filter_name = key.split(' ')[0].capitalize() +'Filter'
                    idx = self.Filter_names.index(filter_name)                  
                    if self.Mesh_xy_RB.isChecked():
                        self.mesh_axis_key = (key, 'z',)
                    elif self.Mesh_xz_RB.isChecked():
                        self.mesh_axis_key = (key, 'y',)
                    elif self.Mesh_yz_RB.isChecked():
                        self.mesh_axis_key = (key, 'x',)
                    self.df_filtered = self.df_filtered.loc[self.df[self.mesh_axis_key].isin(self.Key_Selected_Bins[idx])].copy()
                elif 'low' in key:
                    filter_name = key.split(' ')[0].capitalize() +'Filter'
                    idx = self.Filter_names.index(filter_name) 
                    self.df_filtered = self.df_filtered.loc[self.df[key].isin(self.Key_Selected_Bins[idx])].copy()
                elif 'high' in key:
                    pass
                else:
                    filter_name = key.capitalize() +'Filter'
                    if 'from' in filter_name: filter_name = filter_name.replace('from', 'From')
                    idx = self.Filter_names.index(filter_name) 
                    self.df_filtered = self.df_filtered.loc[self.df[key].isin(self.Key_Selected_Bins[idx])].copy()
        else:
            if self.n_filters > 0:
                for idx in range(self.n_filters):
                    self.df_filtered = self.df_filtered.loc[self.df[self.Keys[idx]].isin(self.Key_Selected_Bins[idx])].copy()
        
        self.Print_Formated_df(self.df_filtered.copy(), self.tally_id, self.editor)
        self.Plot_by_CB.setCurrentIndex(1)
        self.Graph_Layout_CB.setCurrentIndex(1)
        self.Graph_type_CB.setCurrentIndex(1)
        if self.Graph_type_CB.currentText() in ['Bar', 'Stacked Bars', 'Stacked Area']:
            self.xLog_CB.setEnabled(False)
            if 'low' in self.Plot_By_Key or 'center' in self.Plot_By_Key: 
                if 'mu ' in self.Plot_By_Key:
                    self.Curve_xLabel.setText('$\mu$')
                else:
                    self.Curve_xLabel.setText(self.Plot_By_Key.replace('center', '').replace('low', '').replace('[', '/ ').replace(']', ''))

        if 'flux' in self.selected_scores and len(self.selected_scores) > 1:
            self.selected_scores.append(self.selected_scores.pop(self.selected_scores.index('flux')))

        self.Y2Label_CB.setChecked(False)
        self.YSecondary = False
        self.Scores_comboBox.setCurrentIndex(0)
        self.Set_Axis_Labels()
        self.Normalizing_Settings()

    def Set_Axis_Labels(self):
        if 'MeshFilter' not in self.Filter_names:   
            if len(self.selected_scores) == 1: 
                score = self.selected_scores[0]
                if score  == 'flux':
                    yText = score + self.FlUX_UNIT
                elif score in self.REACTION_SCORES:
                    yText = score + self.REACTION_UNIT
                elif score in self.MISCELLANEOUS_SCORES:
                    if score != 'events':
                        yText = score + self.MISCELLANEOUS_UNIT[self.MISCELLANEOUS_SCORES.index(score)]
                    else: 
                        yText = self.MISCELLANEOUS_UNIT[self.MISCELLANEOUS_SCORES.index(score)]
                elif score in self.ENERGY_SCORES:
                    yText = score + self.ENERGY_SCORES_UNIT
            else:
                if all(score in self.REACTION_SCORES for score in self.selected_scores):
                    yText = 'Reactions per source particle'
                elif all(score in self.ENERGY_SCORES for score in self.selected_scores):
                    yText = 'Tallies eV per source particle'
                else: 
                    if len(self.selected_scores) == 2 and 'flux' in self.selected_scores:
                        if self.YSecondary:
                            score = [score for score in self.selected_scores if score != 'flux'][0]
                            if score in self.ENERGY_SCORES:
                                yText = score + self.ENERGY_SCORES_UNIT
                            elif score in self.MISCELLANEOUS_SCORES:
                                if score != 'events':
                                    yText = score + self.MISCELLANEOUS_UNIT[self.MISCELLANEOUS_SCORES.index(score)]
                                else:
                                    yText = self.MISCELLANEOUS_UNIT[self.MISCELLANEOUS_SCORES.index(score)]
                            elif score in self.REACTION_SCORES:
                                yText = score + self.REACTION_UNIT
                            self.Curve_y2Label.setText('flux' + self.FlUX_UNIT)
                        else:
                            yText = 'Tallies per source particle'
                            self.Curve_y2Label.clear()
                    else:
                        if 'flux' in self.selected_scores:
                            self.remaining_scores = [score for score in self.selected_scores if score != 'flux']

                            if self.YSecondary:
                                if all(score in self.REACTION_SCORES for score in self.remaining_scores):
                                    yText = 'Reactions per source particle'
                                elif all(score in self.ENERGY_SCORES for score in self.remaining_scores):
                                    yText = 'Tallies eV per source particle'
                                else:
                                    yText = 'Tallies per source particle'
                                self.Curve_y2Label.setText('flux' + self.FlUX_UNIT)
                            else:
                                yText = 'Tallies per source particle'
                                self.Curve_y2Label.clear()
                        else:
                            yText = 'Tallies per source particle'
            self.Curve_yLabel.setText(yText)
        else:
            yText = 'Tallies per source particle'
            self.Curve_title.setText(yText)
        
    def Y2Label(self, checked):
        if self.Tally_id_comboBox.currentIndex() > 0 and 'Keff' not in self.Tally_id_comboBox.currentText():
            if checked:
                self.YSecondary = True
                self.Curve_y2Label.setEnabled(True)
            else:
                self.YSecondary = False
                self.y2Grid_CB.setEnabled(False)
                self.Curve_y2Label.setEnabled(False)
            
            self.Set_Axis_Labels()
            # Normalize to power
            if self.Norm_to_Power_CB.isChecked() or self.Norm_to_Heating_CB.isChecked():
                self.Normalize_to_Power_Units()
            # Normalize to source strength
            elif self.Norm_to_SStrength_CB.isChecked():
                self.Normalize_to_SStrength_Units()
            # Normalize to cells volume
            if self.Norm_to_Vol_CB.isChecked():   
                self.Normalize_to_Volume_Units(checked)
            # Normalize to variable bin width
            if self.Norm_to_BW_CB.isChecked():
                self.Normalize_to_Bin_Width_Units(checked)
            # Normalize to unit of lethargy
            elif self.Norm_to_UnitLethargy_CB.isChecked():
                self.Normalize_to_Unit_of_Lethargy_Units(checked)
            #self.Normalizing_Settings()

    def Filtered_Scores(self):
        self.DATA = {}
        if 'MeshFilter' in self.Filter_names:                    # MeshFilter
            for elm in self.buttons:
                elm.setEnabled(False)
            self.Graph_Layout_CB.setCurrentIndex(0)             
            self.Graph_type_CB.setCurrentIndex(0)             
            self.Plot_by_CB.setCurrentIndex(0)             
            self.Graph_Layout_CB.setEnabled(True)
            #self.Graph_type_CB.setEnabled(False)
            self.Plot_by_CB.setEnabled(False)
            self.score_plot_PB.setEnabled(True)
            self.label.setEnabled(False)
            self.Mesh_Spec()
        else:
            self.Plot_by_CB.setEnabled(True)

        self.Keys = [''] * len(self.filter_ids)
        self.Key_Selected_Bins = [''] * len(self.filter_ids)
        self.Key_Selected_Bins_High = [''] * len(self.filter_ids)
        self.Key_Selected_Bins_Center = [''] * len(self.filter_ids)
        self.Bins_For_Title = [''] * len(self.filter_ids)
        self.BIN = [''] * len(self.filter_ids)
        self.UNIT = [''] * len(self.filter_ids)
        for idx in range(self.n_filters):
            self.DATA[idx] = {}
            self.filter_id = self.filter_ids[idx] 
            self.filter_name = self.Tallies[self.tally_id]['filter_names'][idx]
            if self.filter_name == 'CellFilter':
                self.Keys[idx] = 'cell'
                self.Checked_cells = self.Select_Bins(idx)
                self.Key_Selected_Bins[idx] = self.Checked_cells
                self.BIN[idx] = ' in cell '
            elif self.filter_name == 'CellFromFilter':
                self.Keys[idx] = 'cellfrom'
                self.Checked_cellsfrom = self.Select_Bins(idx)
                self.Key_Selected_Bins[idx] = self.Checked_cellsfrom
                self.BIN[idx] = ' from '
            elif self.filter_name == 'CellBornFilter':
                self.Keys[idx] = 'cellborn'
                self.Checked_cellsborn = self.Select_Bins(idx)
                self.Key_Selected_Bins[idx] = self.Checked_cellsborn
                self.BIN[idx] = ' born in '
            elif self.filter_name == 'SurfaceFilter':
                self.Keys[idx] = 'surface'
                self.Checked_surfaces = self.Select_Bins(idx)
                self.Key_Selected_Bins[idx] = self.Checked_surfaces
                self.BIN[idx] = ' at surface '
            elif self.filter_name == 'UniverseFilter':
                self.Keys[idx] = 'universe'
                self.Checked_universes = self.Select_Bins(idx)
                self.Key_Selected_Bins[idx] = self.Checked_universes
                self.BIN[idx] = ' in universe '
            elif self.filter_name == 'MaterialFilter':
                self.Keys[idx] = 'material'
                self.Checked_materials = self.Select_Bins(idx)
                self.Key_Selected_Bins[idx] = self.Checked_materials
                self.BIN[idx] = ' for material '
            elif self.filter_name == 'CollisionFilter':
                self.Keys[idx] = 'collision'
                self.Checked_collisions = self.Select_Bins(idx)
                self.Key_Selected_Bins[idx] = self.Checked_collisions
                self.BIN[idx] = ' at collision '
            elif self.filter_name == 'ParticleFilter':
                self.Keys[idx] = 'particle'
                self.Checked_particles = self.Select_Bins(idx)
                self.Key_Selected_Bins[idx] = [item for item in self.Checked_particles]
                self.BIN[idx] = ' for '
            elif self.filter_name == 'EnergyFilter':
                self.Keys[idx] = 'energy low [eV]'
                self.Checked_energies_Low, self.Checked_energies_High, self.Checked_energies_Center, self.Checked_Energy_Bins = self.Select_Bins_Energy_Angle_Time(idx)
                self.Key_Selected_Bins[idx] = self.Checked_energies_Low
                self.Key_Selected_Bins_High[idx] = self.Checked_energies_High
                self.Key_Selected_Bins_Center[idx] = self.Checked_energies_Center
                self.Checked_energies = self.Checked_energies_Low
                if any((ele < 0.01 or ele > 100) and ele != 0. for ele in self.Key_Selected_Bins[idx]):    
                    Format = "{:.1E}"
                else:
                    Format = "{:.2f}"
                Low = [xx for xx in self.Key_Selected_Bins[idx]]
                if any((ele < 0.01 or ele > 100) and ele != 0. for ele in self.Key_Selected_Bins_High[idx]):    
                    Format = "{:.1E}"
                else:
                    Format = "{:.2f}"
                High = [xx for xx in self.Key_Selected_Bins_High[idx]]
                self.Bins_For_Title[idx] = [str((Format.format(x), Format.format(y),)).replace("'", "") for x, y in
                                    zip(Low, High)]
                self.BIN[idx] = ' at energy '
                self.UNIT[idx] = ' eV'
            elif self.filter_name == 'EnergyoutFilter':
                self.Keys[idx] = 'energyout low [eV]'
                self.Checked_energiesout_Low, self.Checked_energiesout_High, self.Checked_energiesout_Center, self.Checked_Energyout_Bins = self.Select_Bins_Energy_Angle_Time(idx)
                self.Key_Selected_Bins[idx] = self.Checked_energiesout_Low
                self.Key_Selected_Bins_High[idx] = self.Checked_energiesout_High
                self.Key_Selected_Bins_Center[idx] = self.Checked_energiesout_Center
                self.Checked_energiesout = self.Checked_energiesout_Low
                if any((ele < 0.01 or ele > 100) and ele != 0. for ele in self.Key_Selected_Bins[idx]):    
                    Format = "{:.1E}"
                else:
                    Format = "{:.2f}"
                Low = [xx for xx in self.Key_Selected_Bins[idx]]
                if any((ele < 0.01 or ele > 100) and ele != 0. for ele in self.Key_Selected_Bins_High[idx]):    
                    Format = "{:.1E}"
                else:
                    Format = "{:.2f}"
                High = [xx for xx in self.Key_Selected_Bins_High[idx]]
                self.Bins_For_Title[idx] = [str((Format.format(x), Format.format(y),)).replace("'", "") for x, y in
                                    zip(Low, High)]                
                self.BIN[idx] = ' at energyout '
                self.UNIT[idx] = ' eV'
            elif self.filter_name == 'MuFilter':
                self.Keys[idx] = 'mu low'
                self.Checked_mu_Low, self.Checked_mu_High, self.Checked_mu_Center, self.Checked_Mu_Bins = self.Select_Bins_Energy_Angle_Time(idx)
                self.Key_Selected_Bins[idx] = self.Checked_mu_Low
                self.Key_Selected_Bins_High[idx] = self.Checked_mu_High
                self.Key_Selected_Bins_Center[idx] = self.Checked_mu_Center
                self.Checked_mu = self.Checked_mu_Low
                if any(np.abs(ele) < 0.01 and ele != 0. for ele in self.Key_Selected_Bins[idx]):    
                    Format = "{:.1E}"
                else:
                    Format = "{:.2f}"
                Low = [xx for xx in self.Key_Selected_Bins[idx]]
                if any(np.abs(ele) < 0.01 and ele != 0. for ele in self.Key_Selected_Bins_High[idx]):    
                    Format = "{:.1E}"
                else:
                    Format = "{:.2f}"
                High = [xx for xx in self.Key_Selected_Bins_High[idx]]
                self.Bins_For_Title[idx] = [str((Format.format(x), Format.format(y),)).replace("'", "") for x, y in
                                    zip(Low, High)]
                self.BIN[idx] = " at $\mu$ "
            elif self.filter_name == 'PolarFilter':
                self.Keys[idx] = 'polar low [rad]'
                self.Checked_polar_Low, self.Checked_polar_High, self.Checked_polar_Center, self.Checked_Polar_Bins = self.Select_Bins_Energy_Angle_Time(idx)
                self.Key_Selected_Bins[idx] = self.Checked_polar_Low
                self.Key_Selected_Bins_High[idx] = self.Checked_polar_High
                self.Key_Selected_Bins_Center[idx] = self.Checked_polar_Center
                self.Checked_polar = self.Checked_polar_Low
                if any(np.abs(ele) < 0.01 and ele != 0. for ele in self.Key_Selected_Bins[idx]):    
                    Format = "{:.1E}"
                else:
                    Format = "{:.2f}"
                Low = [xx for xx in self.Key_Selected_Bins[idx]]
                if any(np.abs(ele) < 0.01 and ele != 0. for ele in self.Key_Selected_Bins_High[idx]):    
                    Format = "{:.1E}"
                else:
                    Format = "{:.2f}"
                High = [xx for xx in self.Key_Selected_Bins_High[idx]]
                self.Bins_For_Title[idx] = [str((Format.format(x), Format.format(y),)).replace("'", "") for x, y in
                                    zip(Low, High)]
                self.BIN[idx] = " at polar "
                self.UNIT[idx] = ' rad'
            elif self.filter_name == 'AzimuthalFilter':
                self.Keys[idx] = 'azimuthal low [rad]'
                self.Checked_azimuthal_Low, self.Checked_azimuthal_High, self.Checked_azimuthal_Center, self.Checked_Azimuthal_Bins = self.Select_Bins_Energy_Angle_Time(idx)
                self.Key_Selected_Bins[idx] = self.Checked_azimuthal_Low
                self.Key_Selected_Bins_High[idx] = self.Checked_azimuthal_High
                self.Key_Selected_Bins_Center[idx] = self.Checked_azimuthal_Center
                self.Checked_azimuthal = self.Checked_azimuthal_Low
                if any(np.abs(ele) < 0.01 and ele != 0. for ele in self.Key_Selected_Bins[idx]):    
                    Format = "{:.1E}"
                else:
                    Format = "{:.2f}"
                Low = [xx for xx in self.Key_Selected_Bins[idx]]
                if any(np.abs(ele) < 0.01 and ele != 0. for ele in self.Key_Selected_Bins_High[idx]):    
                    Format = "{:.1E}"
                else:
                    Format = "{:.2f}"
                High = [xx for xx in self.Key_Selected_Bins_High[idx]]
                self.Bins_For_Title[idx] = [str((Format.format(x), Format.format(y),)).replace("'", "") for x, y in
                                    zip(Low, High)]
                self.BIN[idx] = " at azimuthal "
                self.UNIT[idx] = ' rad'
            elif self.filter_name == 'TimeFilter':
                self.Keys[idx] = 'time low [s]'
                self.Checked_time_Low, self.Checked_time_High, self.Checked_time_Center, self.Checked_Time_Bins = self.Select_Bins_Energy_Angle_Time(idx)
                self.Key_Selected_Bins[idx] = self.Checked_time_Low
                self.Key_Selected_Bins_High[idx] = self.Checked_time_High
                self.Key_Selected_Bins_Center[idx] = self.Checked_time_Center
                self.Checked_time = self.Checked_time_Low
                if any(np.abs(ele) < 0.01 and ele != 0. for ele in self.Key_Selected_Bins[idx]):    
                    Format = "{:.1E}"
                else:
                    Format = "{:.2f}"
                Low = [xx for xx in self.Key_Selected_Bins[idx]]
                if any(np.abs(ele) < 0.01 and ele != 0. for ele in self.Key_Selected_Bins_High[idx]):    
                    Format = "{:.1E}"
                else:
                    Format = "{:.2f}"
                High = [xx for xx in self.Key_Selected_Bins_High[idx]]
                self.Bins_For_Title[idx] = [str((Format.format(x), Format.format(y),)).replace("'", "") for x, y in
                                    zip(Low, High)]
                self.BIN[idx] = " at time "
                self.UNIT[idx] = ' s'
            elif self.filter_name == 'LegendreFilter':
                self.Keys[idx] = 'legendre'
                self.Checked_legendres = self.Select_Bins(idx)
                self.Key_Selected_Bins[idx] = self.Checked_legendres
                self.BIN[idx] = " Legendre "
            elif self.filter_name == 'SpatialLegendreFilter':
                self.Keys[idx] = 'spatiallegendre'
                self.Checked_spatiallegendres = self.Select_Bins(idx)
                self.Key_Selected_Bins[idx] = self.Checked_spatiallegendres  
                self.BIN[idx] = " spatial Legendre "    
            elif self.filter_name == 'SphericalHarmonicsFilter':
                self.Keys[idx] = 'sphericalharmonics'
                self.Checked_sphericalharmonics = self.Select_Bins(idx)
                self.Key_Selected_Bins[idx] = self.Checked_sphericalharmonics  
                self.BIN[idx] = " spherical Harmonics "
            elif self.filter_name == 'DelayedGroupFilter':
                self.Keys[idx] = 'delayedgroup'
                self.Checked_delayedgroup = self.Select_Bins(idx)
                self.Key_Selected_Bins[idx] = self.Checked_delayedgroup  
                self.BIN[idx] = " delayedgroup "
            elif self.filter_name == 'ZernikeFilter':
                self.Keys[idx] = 'zernike'
                self.Checked_zernike = self.Select_Bins(idx)
                self.Key_Selected_Bins[idx] = self.Checked_zernike  
                self.BIN[idx] = " zernike "
            elif self.filter_name == 'ZernikeRadialFilter':
                self.Keys[idx] = 'zernikeradial'
                self.Checked_zernikeradial = self.Select_Bins(idx)
                self.Key_Selected_Bins[idx] = self.Checked_zernikeradial  
                self.BIN[idx] = " zernikeradial "
            elif self.filter_name == 'MeshFilter':
                self.Keys[idx] = 'mesh ' + str(self.mesh_id)
                self.Checked_meshes = self.Select_Bins(idx)
                self.Key_Selected_Bins[idx] = [i - 1 for i in self.Tallies[self.tally_id][self.filter_id]['Checked_bins_indices']]
                self.BIN[idx] = " mesh "            
            else:
                for KEY in self.df_Keys:
                    if 'distribcell' in KEY[0]:           
                        self.Keys[idx] = 'distribcell'
                        self.Checked_distribcells = self.Select_Bins(idx)
                        self.Key_Selected_Bins[idx] = self.Checked_distribcells
                        self.BIN[idx] = " Distrib cell "

            if not self.Bins_For_Title[idx]:
                self.Bins_For_Title[idx] = self.Key_Selected_Bins[idx]   

            # fill dic to plot data            
            self.DATA[idx]['Filter_name'] = self.filter_name
            self.DATA[idx]['KEY'] = self.Keys[idx]
            self.DATA[idx]['Checked_bins'] = self.Key_Selected_Bins[idx]
            self.DATA[idx]['Checked_bins_high'] = self.Key_Selected_Bins_High[idx]
            self.DATA[idx]['Checked_bins_center'] = self.Key_Selected_Bins_Center[idx]
            self.DATA[idx]['BIN'] = self.BIN[idx]
            self.DATA[idx]['BINforTitle'] = self.Bins_For_Title[idx]
            self.DATA[idx]['UNIT'] = self.UNIT[idx]       
            if self.filter_name == 'ParticleFilter':
                self.DATA[idx]['BINforTitle'] = [item + 's' for item in self.DATA[idx]['BINforTitle']]
  
    def Select_Bins(self, Filter_Index):
        Checked_elems = []
        filter_id = self.filter_ids[Filter_Index]
        indices = self.Tallies[self.tally_id][filter_id]['Checked_bins_indices']
        for index in indices:
            Checked_bin = self.Tallies[self.tally_id][filter_id]['bins'][index - 2]
            if Checked_bin.isdigit():   
                Checked_elems.append(eval(Checked_bin))
            else: 
                Checked_elems.append(Checked_bin)   
        return Checked_elems 
 
    def Select_Bins_Energy_Angle_Time(self, Filter_Index):
        filter_id = self.filter_ids[Filter_Index]
        Low = []
        High = []
        Center = []
        Bins = []
        indices = self.Tallies[self.tally_id][filter_id]['Checked_bins_indices']
        for index in indices:
            Low.append(self.tally.filters[Filter_Index].bins[:, 0][index - 2])
            High.append(self.tally.filters[Filter_Index].bins[:, 1][index - 2])
            Bins.append(self.tally.filters[Filter_Index].bins[:][index - 2])
        Center = (np.array(Low) + (np.array(High) - np.array(Low)) * np.array([0.5]*len(Low))).tolist()
        return Low, High, Center, Bins

    def Unfiltered_Scores(self):
        df = self.df
        self.mean = {}
        self.std = {}
        self.DATA = {}
        self.Checked_cells = ['root']
        self.mean['root'] = {}
        self.std['root'] = {}
        self.DATA['root'] = {}
        self.DATA['root']['Checked_bins'] = self.Checked_cells
        if len(self.selected_nuclides) == 0:
            self.showDialog('Warning', 'No nuclide selected !')
            return
        for nuclide in self.selected_nuclides:    # maybe unusfull
            if nuclide != '': 
                self.mean['root'][nuclide] = {}
                self.std['root'][nuclide] = {} 
                for score in self.selected_scores:
                    if score != '':
                        Score = df[df['nuclide'] == nuclide]
                        Score = Score[Score['score'] == score]
                        #Score1 = Score[Score['score'] == score]
                        index = self.selected_scores.index(score)
                        self.mean['root'][nuclide][index] = []
                        self.std['root'][nuclide][index] = []
                        return
                        
    def Plot(self):
        if 'MeshFilter' in self.Filter_names:  
            self.Normalization = False
            if self.Tally_Normalizing_CB.isChecked():
                self.Normalizing() 
            if self.Normalization:
                df = self.df_filtered_normalized
            else:
                df = self.df_filtered
            if self.n_filters == 1:
                if self.Graph_Layout_CB.currentText() == 'Multiple curves':        # Multiple curves
                    self.Plot_Mesh(df) 
                elif self.Graph_Layout_CB.currentText() == 'Stacking subplots':    # Stacking subplots
                    self.Stack_Plot_Mesh(df)      
            else:    
                key = [''] * int(self.n_filters)
                Checked_bins = [''] * int(self.n_filters)
                self.Bins_For_Title = [''] * int(self.n_filters)
                self.BIN = [''] * int(self.n_filters)
                self.UNIT = [''] * int(self.n_filters)
                i = 1
                for filter in self.Filter_names:
                    if filter != 'MeshFilter':
                        idx = self.Filter_names.index(filter)
                        Checked_bins[i] = self.DATA[idx]['Checked_bins']
                        key[i] = self.DATA[idx]['KEY']
                        self.Bins_For_Title[i] = self.DATA[idx]['BINforTitle']
                        self.BIN[i] = self.DATA[idx]['BIN']
                        self.UNIT[i] = self.DATA[idx]['UNIT']
                        i += 1
                if self.Graph_Layout_CB.currentText() == 'Multiple curves':        # Multiple curves
                    self.Plot_Mesh(df)
                elif self.Graph_Layout_CB.currentText() == 'Stacking subplots':    # Stacking subplots
                    self.Stack_Plot_Mesh(df)      

        elif 'DistribcellFilter' in self.Filter_names: 
            self.showDialog('Warning', 'Under development!')
            return
            #self.Plot_Distribcell()
        elif 'Keff' in self.Tally_id_comboBox.currentText():
            self.Plot_Keff()
        else:
            if self.Plot_by_CB.currentIndex() == 0:
                self.showDialog('Warning', 'Nothing will be ploted. Select Plot_By option first!')
                return
            self.Plot_Score()

    def Plot_Keff(self):
        self.Plot_By_Key = self.Plot_by_CB.currentText()
        if not self.Checked_batches:
            self.showDialog('Warning', 'Check batches to plot first!')
            return
        if self.Graph_type_CB.currentIndex() == 0:
            self.showDialog('Warning', 'Select graph type first!')
            return
        if self.Plot_by_CB.currentIndex() == 0:
            self.showDialog('Warning', 'Select what to plot first!')
            return

        from matplotlib.ticker import MaxNLocator
        Graph_type = self.Graph_type_CB.currentText()
        fig, ax = plt.subplots()
        x = self.Checked_batches
        """if self.Plot_By_Key == 0:
            self.showDialog('Warning', 'Select data to plot!')
            plt.close()
            return"""
        if self.Plot_By_Key == 'Keff':
            y = [self.Keff_List[i-1] for i in x]
            if Graph_type == 'Lin-Lin':
                ax.plot(x, y, label='keff', color='b')
            elif Graph_type == 'Scatter':
                ax.scatter(x, y, marker='^')
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))
            plt.title(self.Curve_title.text())
            plt.xlabel(self.Curve_xLabel.text())
            plt.ylabel(self.Curve_yLabel.text(), color='b')
            try:
                ax.errorbar(x, y, np.array(y_error), ecolor='black')
            except:
                pass
        elif self.Plot_By_Key == 'Keff & Shannon entropy':
            y = [self.Keff_List[i-1] for i in x]
            if Graph_type == 'Lin-Lin':
                ax.plot(x, y, label='keff', color='b')
            elif Graph_type == 'Scatter':
                ax.scatter(x, y, marker='^')
            plt.title(self.Curve_title.text())
            plt.xlabel(self.Curve_xLabel.text())
            plt.ylabel(self.Curve_yLabel.text(), color='b') 
            
            try:
                H = [self.H[i-1] for i in x]
                ax2 = ax.twinx()
                if Graph_type == 'Lin-Lin':
                    ax2.plot(x, H, label='entropy', color='g')
                elif Graph_type == 'Scatter':
                    ax2.scatter(x, H, marker='^', color='g')
                plt.ylabel(self.Curve_y2Label.text(), color='g', fontsize=int(self.yFont_CB.currentText()))
                ax2.yaxis.set_tick_params(labelsize=int(self.yFont_CB.currentText())*0.75)
                self.Change_Scales(ax2, Graph_type)
                if self.y2grid:
                    ax2.yaxis.grid(self.y2grid, which=self.which_grid, color='olive', linestyle='--', linewidth=0.7) 
            except:
                self.showDialog('Warning', 'Shannon entropy was not specified in simulation settings!')
            try:
                ax.errorbar(x, y, np.array(y_error), ecolor='black')
            except:
                pass
        elif self.Plot_By_Key == 'Shannon entropy':
            try:
                H = [self.H[i-1] for i in x]
                if Graph_type == 'Lin-Lin':
                    ax.plot(x, H, label='entropy', color='g')
                elif Graph_type == 'Scatter':
                    ax.scatter(x, H, marker='^', color='g')
                plt.ylabel('Shannon entropy', color='g')
            except:
                self.showDialog('Warning', 'Shannon entropy was not specified in simulation settings!')

        if self.xgrid:
            ax.xaxis.grid(self.xgrid, which=self.which_grid, color='gray', linestyle='-', linewidth=0.5)
        if self.ygrid:
            ax.yaxis.grid(self.ygrid, which=self.which_grid, color='gray', linestyle='-', linewidth=0.5)
        
        
        self.Change_Scales(ax, Graph_type)
        self.Labels_Font(ax, plt)            
        fig.show()
                   
    def Plot_Score(self):
        #Plot tallies
        self.Plot_By_Key = self.Plot_by_CB.currentText()
        self.Stack_Plot = False
        if self.Graph_Layout_CB.currentText() != 'BoxPlot' and self.Graph_type_CB.currentIndex() == 0:
            self.showDialog('Warning', 'Select graph type first!')
            return

        if self.Graph_Layout_CB.currentIndex() == 0:
            self.showDialog('Warning', 'Select graph layout first !')
            return
        
        self.Normalization = False
        if self.Tally_Normalizing_CB.isChecked():
            self.Normalizing() 

        if self.Normalization:
            df = self.df_filtered_normalized
        else:
            df = self.df_filtered

        if self.Graph_Layout_CB.currentText() == 'Multiple curves':        # Multiple curves
            self.Multiple_Curves(df)
            self.Stack_Plot = False
        elif self.Graph_Layout_CB.currentText() == 'Stacking subplots':    # Stacking subplots
            if self.filter_id == 0:
                self.Stack_Plot = False
                self.Multiple_Curves(df)                    
            else:
                self.Stack_Plot = True
                self.Stacking_plot_Curves(df)
        elif self.Graph_Layout_CB.currentText() == 'BoxPlot':               # Box Plots
            self.box_plot()
            self.Stack_Plot = False
   
    def set_Graph_stack(self):  
        if self.Graph_Layout_CB.currentIndex() == 2:
            self.TitleFont_CB.setCurrentIndex(6)
            self.xFont_CB.setCurrentIndex(6)
            self.yFont_CB.setCurrentIndex(6)
        else:
            self.TitleFont_CB.setCurrentIndex(8)
            self.xFont_CB.setCurrentIndex(6)
            self.yFont_CB.setCurrentIndex(6)

        if 'Keff' not in self.Tally_id_comboBox.currentText():
            if self.Graph_Layout_CB.currentIndex() in [0, 3]:
                for elm in self.buttons:
                    elm.setEnabled(False)
                for elm in self.buttons_Stack: 
                    elm.setEnabled(False)
                #self.Graph_type_CB.setEnabled(False)
                self.Graph_type_CB.setCurrentIndex(0)
                if self.Graph_Layout_CB.currentIndex() == 0:
                    self.score_plot_PB.setEnabled(False)
                elif self.Graph_Layout_CB.currentIndex() == 3:
                    self.score_plot_PB.setText('plot Box Plot')
                    self.score_plot_PB.setEnabled(True)
                for CB in [self.xLog_CB, self.yLog_CB, self.Add_error_bars_CB, self.xGrid_CB, self.yGrid_CB, self.y2Grid_CB, self.MinorGrid_CB]:
                    CB.setChecked(False)
            else:
                for elm in self.buttons:
                    elm.setEnabled(True)         
                self.score_plot_PB.setEnabled(True)
                if 'MeshFilter' in self.Filter_names:
                    self.score_plot_PB.setText('plot mesh')
                    self.yLog_CB.setEnabled(True)
                    self.xLog_CB.setText('Interpolation')
                    self.yLog_CB.setText('LogNorm')
                    self.Add_error_bars_CB.setText('Plot Errors')
                    self.xGrid_CB.setEnabled(False)
                    self.yGrid_CB.setEnabled(False)
                    self.y2Grid_CB.setEnabled(False)
                    self.MinorGrid_CB.setEnabled(False)
                    self.Graph_Layout_CB.model().item(3).setEnabled(False)
                else:
                    self.score_plot_PB.setText('plot score')
                    self.xLog_CB.setText('xLog')
                    self.yLog_CB.setText('yLog')
                    self.Add_error_bars_CB.setText('Error bars')
                    self.Graph_Layout_CB.model().item(3).setEnabled(True)
                if self.Graph_Layout_CB.currentIndex() == 1:
                    for elm in self.buttons_Stack: 
                        elm.setEnabled(False)
                    self.row_SB.setEnabled(False)
                    self.col_SB.setEnabled(False)
                    self.label_5.setEnabled(False)
                    self.label_6.setEnabled(False)
                    self.label_7.setEnabled(False)
                elif self.Graph_Layout_CB.currentIndex() == 2:
                    for elm in self.buttons_Stack: 
                        elm.setEnabled(True)
                    self.row_SB.setValue(2)
                    self.col_SB.setValue(1)       
                self.set_Scales()

            if 'MeshFilter' not in self.Filters_comboBox.currentText():
                self.Plot_By_Key = self.Plot_by_CB.currentText()
                if self.Plot_By_Key in ['nuclide', 'score', 'cell', 'cellfrom', 'cellborn', 'distribcell', 
                                        'surface', 'universe', 'material', 'particle', 'collision',
                                        'legendre', 'spatiallegendre', 'sphericalharmonics', 'zernike', 'zernikeradial']:
                    self.Deactivate_Curve_Type()
                    if self.Graph_type_CB.currentIndex() in [3, 5]:     #xxxxx
                        self.Graph_type_CB.setCurrentIndex(1)
                else:
                    self.Activate_Curve_Type()

            try:     # try is needed because this will be executed before calculating self.Key
                # determine stack size
                if 'MeshFilter' in self.Filter_names:
                    self.N_Fig = len(self.selected_nuclides) * len(self.selected_scores) #* len(self.checked_bins_indices) 
                    for idx in range(len(self.filter_ids)):
                        self.N_Fig = self.N_Fig * len(self.Key_Selected_Bins[idx])
                else:
                    self.N_Fig = 1
                    if self.Plot_By_Key not in ['nuclide', 'score']:
                        self.N_Fig = len(self.selected_nuclides)
                    if self.n_filters > 0:
                        for idx in range(len(self.filter_ids)):
                            self.N_Fig = self.N_Fig * len(self.Key_Selected_Bins[idx])
                        for idx in range(len(self.filter_ids)):
                            if self.Plot_By_Key == self.Keys[idx]:
                                self.N_Fig = int(self.N_Fig / len(self.Key_Selected_Bins[idx]))
                        if 'center' in self.Plot_By_Key:
                            index = self.Plot_by_CB.currentIndex() - 1
                            idx = self.Keys.index(self.Plot_by_CB.itemText(index))
                            self.N_Fig = int(self.N_Fig / len(self.Key_Selected_Bins[idx]))
                
                self.row_SB.setValue(int(np.sqrt(self.N_Fig) + 0.5))
                col = self.N_Fig / self.row_SB.value()
                if col.is_integer():
                    self.col_SB.setValue(int(col)) 
                else:      
                    self.col_SB.setValue(int(col + 1.))       
                if self.row_SB.value() == 1 and self.col_SB.value() > 3:
                    self.row_SB.setValue(int(self.col_SB.value() * 0.5 + 0.5) )
                    self.col_SB.setValue(int(self.col_SB.value() / self.row_SB.value() + 0.5))
                elif self.col_SB.value() == 1 and self.row_SB.value() > 3:
                    self.col_SB.setValue(int(self.row_SB.value() * 0.5 + 0.5))
                    self.row_SB.setValue(int(self.row_SB.value() / self.col_SB.value() + 0.5))
            except:
                pass
        else:
            self.Add_error_bars_CB.setEnabled(False)
            for PB in self.buttons:
                PB.setEnabled(True)
            if self.Plot_by_CB.currentIndex() == 2:
                self.Y2Label_CB.setEnabled(False)
                self.Y2Label_CB.setChecked(True)
                self.Curve_y2Label.setEnabled(True)
                self.Curve_y2Label.setText('Shannon entropy')
                self.YSecondary = True
            else:
                self.Y2Label_CB.setEnabled(False)
                self.Y2Label_CB.setChecked(False)
                self.Curve_y2Label.setEnabled(False)
                self.Curve_y2Label.clear()

    def Multiple_Curves(self, df):
        if self.row_SB.value()*self.col_SB.value() > 20:
                qm = QMessageBox
                ret = qm.question(self, 'Warning',' More than 20 figures (' + str(self.N_Fig) + ') have been opened! \n This may consume too much memory.'+
                                  '\n continue ploting ?', qm.Yes | qm.No)
            
                if ret == qm.Yes:
                    pass 
                elif ret == qm.No:
                    self.WillPlot = False
                    return

        self.WillPlot = True
        if self.n_filters == 0:
            ax = ['']    
        else:
            ax = [''] * self.N_Fig
  
        if self.Plot_By_Key in ['nuclide', 'score']:  
            self.Plot_By_Nuclide_Score(df, ax)
        else:
            self.Plot_By_Filter(df, ax)
        if self.No_Plot:
            return
    
    def Stacking_plot_Curves(self, df):
        self.WillPlot = True
        self.Plot_By_Key = self.Plot_by_CB.currentText()
        Stack_Size = self.row_SB.value() * self.col_SB.value()
        if Stack_Size == 1:
            self.showDialog('Warning', 'Stacking plots need more rows and/or columns !')
            self.row_SB.setValue(2)
        if self.N_Fig == 1:
            self.Stack_Plot = False
            self.Multiple_Curves(df) 
            return        
        if Stack_Size < self.N_Fig:
            qm = QMessageBox
            ret = qm.question(self, 'Warning',' Stack size : ' + str(Stack_Size) + ' less than total available plots : ' + 
                                     str(self.N_Fig) + '\nLast plots will be removed! Continue ploting ?', qm.Yes | qm.No)
            if ret == qm.Yes:
                pass 
            elif ret == qm.No:
                self.WillPlot = False
                return
        
        fig, axs = plt.subplots(self.row_SB.value(), self.col_SB.value(), layout="constrained")   #, sharex=True)

        if self.N_Fig < Stack_Size:
            ax = [None] * Stack_Size
        else:    
            ax = [None] * self.N_Fig            
        
        for i, ax_ in enumerate(axs.flat):
            ax[i] = ax_

        if self.Plot_By_Key in ['nuclide', 'score']:  
            self.Plot_By_Nuclide_Score(df, ax)
        else:
            self.Plot_By_Filter(df, ax)

        if Stack_Size > self.N_Fig:
            for i in range(self.N_Fig, Stack_Size):
                ax[i].set_visible(False)        # to remove empty plots
        if self.WillPlot:
            #fig.tight_layout()
            fig.show()               

    def Plot_By_Nuclide_Score(self, df, ax): 
        # up to 6 filters
        prop_cycle_color = ['#FB1304', '#008000', '#0751FC', '#C107FC', '#FBCE02',
                    '#00FFFF', '#F9F923', '#00FF00', '#800000', '#808000', 
                    '#FFFF00', '#000080', '#FF00FF', '#808080', '#000000', 
                    '#CD5C5C', '#BF5A31', '#31BFBD', '#FFA07A', '#70D38F',
                    '#AE31F0', '#F08080']
        Graph_type = self.Graph_type_CB.currentText()
        Width = 0.15    
        if self.Plot_By_Key == 'nuclide':
            KEY0 = 'nuclide'
            KEY01 = 'score'
            Checked_bins0 = self.selected_nuclides
            Checked_bins01 = self.selected_scores
        elif self.Plot_By_Key == 'score':
            KEY0 = 'score'
            KEY01 = 'nuclide'
            Checked_bins0 = self.selected_scores
            Checked_bins01 = self.selected_nuclides

        X_Shift = Width * 0.5 * (len(Checked_bins01) - 1)
        X_ = np.arange(len(Checked_bins0))
        if Graph_type == 'Stacked Area':
            if len(X_) < 2:
                self.showDialog('Warning', 'Not enough data to plot Stacked Area!')
                self.No_Plot = True
                return
        Stack_Size = self.row_SB.value() * self.col_SB.value()
        Checked_bins = [''] * self.n_filters
        Bins_For_Title = [''] * self.n_filters
        BIN = [''] * self.n_filters
        UNIT = [''] * self.n_filters
        key = [''] * self.n_filters
        key1 = ['']; BIN1 = ['']; UNIT1 = ['']; Checked_bins1 = ['']; Bins_For_Title1 = ['']
        key2 = ['']; BIN2 = ['']; UNIT2 = ['']; Checked_bins2 = ['']; Bins_For_Title2 = ['']
        key3 = ['']; BIN3 = ['']; UNIT3 = ['']; Checked_bins3 = ['']; Bins_For_Title3 = ['']
        key4 = ['']; BIN4 = ['']; UNIT4 = ['']; Checked_bins4 = ['']; Bins_For_Title4 = ['']
        key5 = ['']; BIN5 = ['']; UNIT5 = ['']; Checked_bins5 = ['']; Bins_For_Title5 = ['']
        key6 = ['']; BIN6 = ['']; UNIT6 = ['']; Checked_bins6 = ['']; Bins_For_Title6 = ['']

        if self.n_filters >= 1:
            i = 0
            for filter in self.Filter_names:
                idx = self.Filter_names.index(filter)
                Checked_bins[i] = self.DATA[idx]['Checked_bins']
                key[i] = self.DATA[idx]['KEY']
                Bins_For_Title[i] = self.DATA[idx]['BINforTitle']
                BIN[i] = self.DATA[idx]['BIN']
                UNIT[i] = self.DATA[idx]['UNIT']
                i += 1

            key1 = key[0]; BIN1 = BIN[0]; UNIT1 = UNIT[0]; Checked_bins1 = Checked_bins[0]; Bins_For_Title1 = Bins_For_Title[0]
            if self.n_filters >= 2:    
                key2 = key[1]; BIN2 = BIN[1]; UNIT2 = UNIT[1]; Checked_bins2 = Checked_bins[1]; Bins_For_Title2 = Bins_For_Title[1]
                if self.n_filters >= 3:
                    key3 = key[2]; BIN3 = BIN[2]; UNIT3 = UNIT[2]; Checked_bins3 = Checked_bins[2]; Bins_For_Title3 = Bins_For_Title[2]
                    if self.n_filters >= 4:
                        key4 = key[3]; BIN4 = BIN[3]; UNIT4 = UNIT[3]; Checked_bins4 = Checked_bins[3]; Bins_For_Title4 = Bins_For_Title[3]
                        if self.n_filters >= 5:
                            key5 = key[4]; BIN5 = BIN[4]; UNIT5 = UNIT[4]; Checked_bins5 = Checked_bins[4]; Bins_For_Title5 = Bins_For_Title[4]
                            if self.n_filters >= 6:
                                key6 = key[5]; BIN6 = BIN[5]; UNIT6 = UNIT[5]; Checked_bins6 = Checked_bins[5]; Bins_For_Title6 = Bins_For_Title[5]

        self.No_Plot = False
        i = 0
        Delete_AX = False
        for bin6 in Checked_bins6:
            j6 = Checked_bins6.index(bin6)
            for bin5 in Checked_bins5:
                j5 = Checked_bins5.index(bin5)
                for bin4 in Checked_bins4:                                  # loop on Filter4
                    j4 = Checked_bins4.index(bin4)    
                    for bin3 in Checked_bins3:                              # loop on Filter3
                        j3 = Checked_bins3.index(bin3)
                        for bin2 in Checked_bins2:                          # loop on Filter2
                            j2 = Checked_bins2.index(bin2)
                            for bin1 in Checked_bins1:                      # loop on Filter1
                                j1 = Checked_bins1.index(bin1)
                                
                                if not self.Stack_Plot:
                                    fig, ax[i] = plt.subplots()
                                else:
                                    if i + 1 > Stack_Size:
                                        break

                                xx_bar = []; xs_ = []; y_ = {}; y_err = {}  
                                for bin01 in Checked_bins01:
                                    y_[bin01] = []; y_err[bin01] = []
                                for bin0 in Checked_bins0: 
                                    bin0_idx = Checked_bins0.index(bin0)
                                    y_error = []; ys_ = []; ys_err = []
                                    X = bin0_idx   
                                    x_bar = []
                                    multiplier = 0
                                    xs_.append(X)                
                                    for bin01 in Checked_bins01:
                                        index = Checked_bins01.index(bin01)
                                        if Graph_type == 'Bar':
                                            offset = Width * multiplier
                                            X += offset
                                        x = X 
                                        x_bar.append(x)
                                        multiplier = 1  
                                        
                                        y = df[df[KEY0] == bin0]
                                        y = y[y[KEY01] == bin01]['mean']
                                        y_error = df[df[KEY0] == bin0]
                                        y_error = y_error[y_error[KEY01] == bin01]['std. dev.']
                                        if self.n_filters >= 1: 
                                            y = y[df[key1] == bin1]
                                            y_error = y_error[df[key1] == bin1]
                                            if self.n_filters >= 2:
                                                y = y[df[key2] == bin2]
                                                y_error = y_error[df[key2] == bin2]
                                                if self.n_filters >= 3:
                                                    y = y[df[key3] == bin3]
                                                    y_error = y_error[df[key3] == bin3]
                                                    if self.n_filters >= 4:
                                                        y = y[df[key4] == bin4]
                                                        y_error = y_error[df[key4] == bin4]
                                                        if self.n_filters >= 5:
                                                            y = y[df[key5] == bin5]
                                                            y_error = y_error[df[key5] == bin5]
                                                            if self.n_filters >= 6:
                                                                y = y[df[key6] == bin6]
                                                                y_error = y_error[df[key6] == bin6]

                                        y = y.tolist()[0]   
                                        y_error = y_error.tolist()[0]    
                                        y_[bin01].append(y)             
                                        y_err[bin01].append(y_error)    
                                        ys_.append(y_[bin01])
                                        ys_err.append(y_err[bin01]) 
                                    
                                    ax[i].set_prop_cycle(None)
                                    
                                    xx_bar.append(x_bar)
                                XX = [list(group) for group in zip(*xx_bar)]
                                    
                                if Graph_type == 'Bar':
                                    for bin01 in Checked_bins01:
                                        #Label = bin01 if bin0_idx == 0 else None
                                        index = Checked_bins01.index(bin01)
                                        if self.Add_error_bars_CB.isChecked():
                                            Y_Err = ys_err[index]
                                        else:
                                            Y_Err = None
                                        if self.YSecondary and bin01 == 'flux': 
                                            ax2 = ax[i].twinx()
                                            ax2.bar(XX[index], ys_[index], width=Width, yerr=Y_Err, label=bin01, color=prop_cycle_color[index])
                                            lines2, labels2 = ax2.get_legend_handles_labels()
                                        else:
                                            ax[i].bar(XX[index], ys_[index], width=Width, yerr=Y_Err, label=bin01, color=prop_cycle_color[index])
                                        lines1, labels1 = ax[i].get_legend_handles_labels()

                                elif Graph_type == 'Scatter':
                                    for bin01 in Checked_bins01:        
                                        index = Checked_bins01.index(bin01)
                                        if self.Add_error_bars_CB.isChecked():
                                            Y_Err = ys_err[index]
                                        else:
                                            Y_Err = None
                                        if self.YSecondary and bin01 == 'flux': 
                                            ax2 = ax[i].twinx()
                                            ax2.errorbar(xs_, ys_[index], fmt='^', yerr=Y_Err, label=bin01, color=prop_cycle_color[index])
                                            lines2, labels2 = ax2.get_legend_handles_labels()
                                        else:
                                            ax[i].errorbar(xs_, ys_[index], fmt='^', yerr=Y_Err, label=bin01, color=prop_cycle_color[index])
                                        lines1, labels1 = ax[i].get_legend_handles_labels()
                                            

                                elif Graph_type == 'Stacked Bars':
                                    Bottom = np.zeros(len(Checked_bins0))
                                    for bin01 in Checked_bins01:
                                        Label = bin01 if len(Checked_bins01) > 1 else None
                                        k = Checked_bins01.index(bin01)
                                        if self.Add_error_bars_CB.isChecked():
                                            ax[i].bar(np.array(xs_) + X_Shift, ys_[k], yerr = np.array(ys_err[k]), bottom = Bottom, label = Label, color=prop_cycle_color[k])
                                        else:
                                            ax[i].bar(np.array(xs_) + X_Shift, ys_[k], bottom = Bottom, label = Label, color=prop_cycle_color[k])
                                        Bottom += ys_[k]
                                elif Graph_type == 'Stacked Area':
                                    ax[i].stackplot(np.array(xs_) + X_Shift, ys_[:len(Checked_bins01)], labels = Checked_bins01, colors=prop_cycle_color)
                                    if self.Add_error_bars_CB.isChecked():
                                        Bottom = np.zeros(len(Checked_bins0))
                                        for k in range(len(Checked_bins01)):
                                            ax[i].errorbar(np.array(xs_) + X_Shift, ys_[k] + Bottom, np.array(ys_err[k]), fmt = '|', ecolor='black')
                                            Bottom += ys_[k]     
                                
                                if len(Checked_bins01) > 1: 
                                    ax[i].legend()

                                ax[i].set_xlabel(self.Curve_xLabel.text())
                                  

                                ax[i].set_ylabel(self.Curve_yLabel.text())
                                ax[i].yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
                                ax[i].ticklabel_format(axis='y', style='scientific', scilimits=(0, 0))  # Force scientific notation

                                if self.YSecondary and self.Plot_By_Key == 'nuclide': 
                                    ax2.set_ylabel(self.Curve_y2Label.text())
                                    ax2.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
                                    ax2.ticklabel_format(axis='y', style='scientific', scilimits=(0, 0))  # Force scientific notation

                                if Graph_type in ['Stacked Area', 'Stacked Bars', 'Bar']:  
                                    ax[i].set_xticks(X_ + X_Shift, Checked_bins0)  
                                else:
                                    ax[i].set_xticks(X_, Checked_bins0) 

                                Title = self.Curve_title.text()  
                                if len(self.selected_nuclides) == 1 and self.Plot_By_Key == 'nuclide':
                                    Title = Title.replace(bin0, '').replace(' - ', '')
                                
                                if self.n_filters >= 1: 
                                    Title = Title + BIN1 + str(Bins_For_Title1[j1]).replace("'", "") + UNIT1
                                    if self.n_filters >= 2:
                                        Title = Title + ' - ' + BIN2 + str(Bins_For_Title2[j2]).replace("'","") + UNIT2
                                        if self.n_filters >= 3:
                                            Title = Title + '\n' + BIN3 + str(Bins_For_Title3[j3]).replace("'","") + UNIT3
                                            if self.n_filters >= 4:
                                                Title = Title + ' - ' + BIN4 + str(Bins_For_Title4[j4]).replace("'","") + UNIT4
                                                if self.n_filters >= 5:
                                                    Title = Title + ' - ' + BIN5 + str(Bins_For_Title5[j5]).replace("'","") + UNIT5
                                                    if self.n_filters >= 6:
                                                        Title = Title + ' - ' + BIN6 + str(Bins_For_Title6[j6]).replace("'","") + UNIT6
                                
                                ax[i].set_title(Title)

                                self.Labels_Font(ax[i], plt)
                                self.Change_Scales(ax[i], Graph_type)

                                if self.YSecondary and self.Plot_By_Key == 'nuclide':
                                    self.Change_Scales(ax2, Graph_type)
                                    ax2.yaxis.label.set_size(int(self.yFont_CB.currentText()))
                   
                                # Add legends
                                if len(Checked_bins01) > 1: 
                                    if Graph_type in ['Scatter', 'Bar']:
                                        if self.YSecondary and self.Plot_By_Key == 'nuclide':
                                            ax[i].legend(lines1 + lines2, labels1 + labels2) #, prop = { "size": LegendeFontSize }, loc="upper left")
                                        else:
                                            ax[i].legend(lines1, labels1) #, prop = { "size": LegendeFontSize }, loc="upper left")
                                    else:
                                        ax[i].legend()

                                # Add grids
                                if self.xgrid:
                                    ax[i].xaxis.grid(self.xgrid, which=self.which_grid, color='gray', linestyle='-', linewidth=0.5)
                                if self.ygrid:
                                    ax[i].yaxis.grid(self.ygrid, which=self.which_grid, color='gray', linestyle='-', linewidth=0.5)
                                if self.y2grid:
                                    if self.YSecondary and bin01 == 'flux' and self.Plot_By_Key == 'nuclide':
                                        ax2.yaxis.grid(self.y2grid, which=self.which_grid, color='olive', linestyle='--', linewidth=0.5) 

                                i += 1
                                if not self.Stack_Plot:
                                    fig.show()
                                    fig.tight_layout()
                                
    def Plot_By_Filter(self, df, ax):
        Checked_bins = [''] * self.n_filters
        Bins_For_Title = [''] * self.n_filters
        Checked_bins_Low = ['']
        Checked_bins_High = ['']
        BIN = [''] * self.n_filters
        UNIT = [''] * self.n_filters
        key = [''] * self.n_filters
   
        if self.n_filters == 1:
            # filter1
            idx = 0
            if self.filter_name in self.ENERGY_ANGLE_FILTER:
                if 'low' in self.Plot_By_Key:
                    Checked_bins[0] = self.DATA[idx]['Checked_bins']
                elif 'center' in self.Plot_By_Key:
                    Checked_bins[0] = self.DATA[idx]['Checked_bins_center']
                Checked_bins_Low = self.DATA[idx]['Checked_bins']
                Checked_bins_High = self.DATA[idx]['Checked_bins_high']
            else:
                Checked_bins[0] = self.DATA[idx]['Checked_bins']
            key[0] = self.DATA[idx]['KEY']
            Bins_For_Title[0] = self.DATA[idx]['BINforTitle']
            BIN[0] = self.DATA[idx]['BIN']
            UNIT[0] = self.DATA[idx]['UNIT']
        
        elif self.n_filters >= 2:
            FILTERS = [filter for filter in self.Filter_names]            
            for filter in self.Filter_names:
                if 'low' in self.Plot_By_Key:
                    index = self.Plot_by_CB.currentIndex()
                    idx = self.Keys.index(self.Plot_by_CB.itemText(index))
                    Checked_bins[0] = self.DATA[idx]['Checked_bins']
                    Checked_bins_Low = self.DATA[idx]['Checked_bins']
                    Checked_bins_High = self.DATA[idx]['Checked_bins_high']
                elif 'center' in self.Plot_By_Key:
                    index = self.Plot_by_CB.currentIndex() - 1
                    idx = self.Keys.index(self.Plot_by_CB.itemText(index))
                    Checked_bins[0] = self.DATA[idx]['Checked_bins_center']
                    Checked_bins_Low = self.DATA[idx]['Checked_bins']
                    Checked_bins_High = self.DATA[idx]['Checked_bins_high']
                else:
                    index = self.Plot_by_CB.currentIndex()
                    idx = self.Keys.index(self.Plot_by_CB.itemText(index))
                    Checked_bins[0] = self.DATA[idx]['Checked_bins']

                key[0] = self.DATA[idx]['KEY']
                Bins_For_Title[0] = self.DATA[idx]['BINforTitle']
                BIN[0] = self.DATA[idx]['BIN']
                UNIT[0] = self.DATA[idx]['UNIT']
                idx_to_remove = idx
                break

            FILTERS.remove(self.Filter_names[idx_to_remove])
            i = 1
            for filter in FILTERS:
                idx = self.Filter_names.index(filter)
                Checked_bins[i] = self.DATA[idx]['Checked_bins']
                key[i] = self.DATA[idx]['KEY']
                Bins_For_Title[i] = self.DATA[idx]['BINforTitle']
                BIN[i] = self.DATA[idx]['BIN']
                UNIT[i] = self.DATA[idx]['UNIT']
                i += 1
        
        self.Plot_by_All_Filters(df, ax, Checked_bins, Checked_bins_Low, Checked_bins_High, key, Bins_For_Title, BIN, UNIT)

    def Plot_by_All_Filters(self, df, ax, Checked_bins, Checked_bins_Low, Checked_bins_High, key, Bins_For_Title, BIN, UNIT):
        # up to 6 filters
        Graph_type = self.Graph_type_CB.currentText()
        Width = 0.15 
        X_Shift = Width * 0.5 * (len(self.selected_scores) - 1)
        Stack_Size = self.row_SB.value()*self.col_SB.value()
        X_ = np.arange(len(Checked_bins[0]))
        self.No_Plot = False
        Keys = self.df.keys()
        if 'mean' not in Keys:
            self.showDialog('Warning', 'Cannot find data to plot!')
            return
        if 'std. dev.' not in Keys:
            self.add_errors = False
        else:
            self.add_errors = True
        if Graph_type == 'Stacked Area':
            if len(X_) < 2:
                self.showDialog('Warning', 'Not enough data to plot Stacked Area!')
                self.No_Plot = True
                return
        x_Lin = Checked_bins[0]
        key2 = ['']; BIN2 = ['']; UNIT2 = ['']; Checked_bins2 = ['']; Bins_For_Title2 = ['']
        key3 = ['']; BIN3 = ['']; UNIT3 = ['']; Checked_bins3 = ['']; Bins_For_Title3 = ['']
        key4 = ['']; BIN4 = ['']; UNIT4 = ['']; Checked_bins4 = ['']; Bins_For_Title4 = ['']
        key5 = ['']; BIN5 = ['']; UNIT5 = ['']; Checked_bins5 = ['']; Bins_For_Title5 = ['']
        key6 = ['']; BIN6 = ['']; UNIT6 = ['']; Checked_bins6 = ['']; Bins_For_Title6 = ['']

        prop_cycle_color = ['#FB1304', '#008000', '#0751FC', '#C107FC', '#FBCE02',
                            '#00FFFF', '#F9F923', '#00FF00', '#800000', '#808000', 
                            '#FFFF00', '#000080', '#FF00FF', '#808080', '#000000', 
                            '#CD5C5C', '#BF5A31', '#31BFBD', '#FFA07A', '#70D38F',
                            '#AE31F0', '#F08080']  
        if Checked_bins_Low == ['']:
            Checked_bins_Low = Checked_bins[0]
        if Graph_type == 'Stairs':
            edges = [Checked_bins_Low[0]]
            edges.extend(Checked_bins_High)
            midpoints = 0.5 * (np.array(edges[:-1]) + np.array(edges[1:]))

        if self.n_filters >= 1:
            key1 = key[0]; BIN1 = BIN[0]; UNIT1 = UNIT[0]
            if self.n_filters >= 2:    
                key2 = key[1]; BIN2 = BIN[1]; UNIT2 = UNIT[1]; Checked_bins2 = Checked_bins[1]; Bins_For_Title2 = Bins_For_Title[1]
                if self.n_filters >= 3:
                    key3 = key[2]; BIN3 = BIN[2]; UNIT3 = UNIT[2]; Checked_bins3 = Checked_bins[2]; Bins_For_Title3 = Bins_For_Title[2]
                    if self.n_filters >= 4:
                        key4 = key[3]; BIN4 = BIN[3]; UNIT4 = UNIT[3]; Checked_bins4 = Checked_bins[3]; Bins_For_Title4 = Bins_For_Title[3]
                        if self.n_filters >= 5:
                            key5 = key[4]; BIN5 = BIN[4]; UNIT5 = UNIT[4]; Checked_bins5 = Checked_bins[4]; Bins_For_Title5 = Bins_For_Title[4]
                            if self.n_filters >= 6:
                                key6 = key[5]; BIN6 = BIN[5]; UNIT6 = UNIT[5]; Checked_bins6 = Checked_bins[5]; Bins_For_Title6 = Bins_For_Title[5]

        i = 0
        for bin6 in Checked_bins6:                        # loop on Filter6
            j6 = Checked_bins6.index(bin6)
            for bin5 in Checked_bins5:                        # loop on Filter5
                j5 = Checked_bins5.index(bin5)
                for bin4 in Checked_bins4:                           # loop on Filter4
                    j4 = Checked_bins4.index(bin4)
                    for bin3 in Checked_bins3:                           # loop on Filter3
                        j3 = Checked_bins3.index(bin3)
                        for bin2 in Checked_bins2:                          # loop on Filter2
                            j2 = Checked_bins2.index(bin2)
                            for nuclide in self.selected_nuclides:               # loop on nuclides                                
                                if not self.Stack_Plot:
                                    #if i < len(self.selected_scores) or len(self.selected_scores) == 1:   
                                    fig, ax[i] = plt.subplots()
                                else:
                                    if i + 1 > Stack_Size:
                                        break
                                                                    
                                xx_bar = []; xs_ = []; y_ = {}; y_err = {}  
                                for score in self.selected_scores:
                                    y_[score] = []; y_err[score] = []

                                for bin in Checked_bins_Low: 
                                    bin_idx = Checked_bins_Low.index(bin)
                                    y_error = []; ys_ = []; ys_err = []
                                    X = Checked_bins_Low.index(bin) 
                                    x_bar = []   
                                    multiplier = 0
                                    xs_.append(X)
                                    for score in self.selected_scores:
                                        index = self.selected_scores.index(score)
                                        if Graph_type == 'Bar':
                                            offset = Width * multiplier 
                                            X += offset
                                        x = X 
                                        x_bar.append(x)
                                        multiplier = 1   

                                        y = df[df[key1] == bin]
                                        y = y[y.nuclide == nuclide]
                                        y = y[y.score == score]['mean'] 
                                        y_error = df[df[key1]  == bin]
                                        y_error = y_error[y_error.nuclide == nuclide]
                                        if self.add_errors:    
                                            y_error = y_error[y_error.score == score]['std. dev.']
                                        if self.n_filters >= 2:
                                            y = y[df[key2] == bin2]
                                            y_error = y_error[df[key2] == bin2]
                                            if self.n_filters >= 3:
                                                y = y[df[key3] == bin3]  
                                                y_error = y_error[df[key3] == bin3]   
                                                if self.n_filters >= 4:
                                                    y = y[df[key4] == bin4]  
                                                    y_error = y_error[df[key4] == bin4]   
                                                    if self.n_filters >= 5:
                                                        y = y[df[key5] == bin5]
                                                        y_error = y_error[df[key5] == bin5]
                                                        if self.n_filters >= 6:
                                                            y = y[df[key6] == bin6]
                                                            y_error = y_error[df[key6] == bin6]   

                                        y = y.tolist()[0]          
                                        y_[score].append(y)   
                                        ys_.append(y_[score])
                                        if self.add_errors:
                                            y_error = y_error.tolist()[0]          
                                            y_err[score].append(y_error)   
                                            ys_err.append(y_err[score])                    
                                                             
                                    xx_bar.append(x_bar)
                                XX = [list(group) for group in zip(*xx_bar)]

                                if Graph_type == 'Bar':
                                    for score in self.selected_scores:    
                                        index = self.selected_scores.index(score)
                                        if self.Add_error_bars_CB.isChecked() and self.add_errors:
                                            Y_Err = ys_err[index]
                                        else:
                                            Y_Err = None
                                        if self.YSecondary and score == 'flux': 
                                            ax2 = ax[i].twinx()
                                            ax2.bar(XX[index], ys_[index], width=Width, yerr=Y_Err, label=score, color=prop_cycle_color[index])
                                            lines2, labels2 = ax2.get_legend_handles_labels()
                                        else:
                                            ax[i].bar(XX[index], ys_[index], width=Width, yerr=Y_Err, label=score, color=prop_cycle_color[index])
                                        lines1, labels1 = ax[i].get_legend_handles_labels()
                                elif Graph_type in ['Lin-Lin', 'Scatter', 'Stairs']:
                                    for score in self.selected_scores:
                                        Label = score if len(self.selected_scores) > 1 else None
                                        k = self.selected_scores.index(score)
                                        if Graph_type == 'Lin-Lin':
                                            if self.YSecondary and score == 'flux': 
                                                ax2 = ax[i].twinx()
                                                #ax2.plot(x_Lin, ys_[k], label = Label, drawstyle='steps-mid', color=prop_cycle_color[k])
                                                if len(x_Lin) == 1:
                                                    ax2.scatter(x_Lin, ys_[k], marker='^', label=Label, color=prop_cycle_color[k])
                                                else:
                                                    ax2.plot(x_Lin, ys_[k], label=Label, color=prop_cycle_color[k])
                                                lines2, labels2 = ax2.get_legend_handles_labels()
                                            else:
                                                if len(x_Lin) == 1:
                                                    ax[i].scatter(x_Lin, ys_[k], marker='^', label = Label, color=prop_cycle_color[k])
                                                else:
                                                    ax[i].plot(x_Lin, ys_[k], label=Label, color=prop_cycle_color[k])
                                            lines1, labels1 = ax[i].get_legend_handles_labels()                                                
                                        elif Graph_type == 'Scatter':
                                            if self.YSecondary and score == 'flux': 
                                                ax2 = ax[i].twinx()
                                                if 'low' in self.Plot_By_Key or 'center' in self.Plot_By_Key:
                                                    ax2.scatter(x_Lin, ys_[k], marker='^', label = Label, color=prop_cycle_color[k])
                                                else:
                                                    ax2.scatter(X_, ys_[k], marker='^', label = Label, color=prop_cycle_color[k])
                                                lines2, labels2 = ax2.get_legend_handles_labels()
                                            else:    
                                                if 'low' in self.Plot_By_Key or 'center' in self.Plot_By_Key:
                                                    ax[i].scatter(x_Lin, ys_[k], marker='^', label = Label, color=prop_cycle_color[k])
                                                else:
                                                    ax[i].scatter(X_, ys_[k], marker='^', label = Label, color=prop_cycle_color[k])
                                                    ax[i].set_xticks(X_, Bins_For_Title[0])
                                            lines1, labels1 = ax[i].get_legend_handles_labels()
                                        elif Graph_type == 'Stairs':
                                            if self.YSecondary and score == 'flux': 
                                                ax2 = ax[i].twinx()
                                                ax2.stairs(ys_[k], edges, label = Label, color=prop_cycle_color[k])
                                                lines2, labels2 = ax2.get_legend_handles_labels()
                                            else: 
                                                ax[i].stairs(ys_[k], edges, label = Label, color=prop_cycle_color[k])
                                            lines1, labels1 = ax[i].get_legend_handles_labels()                                                
                                                
                                        if self.Add_error_bars_CB.isChecked() and self.add_errors:
                                            if Graph_type == 'Stairs':
                                                if self.YSecondary  and score == 'flux':
                                                    if 'low' in self.Plot_By_Key or 'center' in self.Plot_By_Key:
                                                        ax2.errorbar(midpoints, ys_[k], ys_err[k], fmt='|', ecolor='black')
                                                else:
                                                    if 'low' in self.Plot_By_Key or 'center' in self.Plot_By_Key:
                                                        ax[i].errorbar(midpoints, ys_[k], ys_err[k], fmt='|', ecolor='black')
                                            else:
                                                if self.YSecondary  and score == 'flux':
                                                    if 'low' in self.Plot_By_Key or 'center' in self.Plot_By_Key:
                                                        ax2.errorbar(x_Lin, ys_[k], ys_err[k], fmt='|', ecolor='black')
                                                    else:
                                                        ax2.errorbar(X_, ys_[k], ys_err[k], fmt='|', ecolor='black')
                                                else:
                                                    if 'low' in self.Plot_By_Key or 'center' in self.Plot_By_Key:
                                                        ax[i].errorbar(x_Lin, ys_[k], ys_err[k], fmt='|', ecolor='black')
                                                    else:
                                                        ax[i].errorbar(X_, ys_[k], ys_err[k], fmt='|', ecolor='black')
                                elif Graph_type == 'Stacked Bars':
                                    Bottom = np.zeros(len(Checked_bins[0]))
                                    for score in self.selected_scores:
                                        Label = score if len(self.selected_scores) > 1 else None           
                                        k = self.selected_scores.index(score)
                                        if self.Add_error_bars_CB.isChecked() and self.add_errors:
                                            ax[i].bar(np.array(xs_) + X_Shift, ys_[k], yerr=np.array(ys_err[k]), bottom=Bottom, label=Label, color=prop_cycle_color[k])
                                        else:
                                            ax[i].bar(np.array(xs_) + X_Shift, ys_[k], bottom = Bottom, label = Label, color=prop_cycle_color[k])
                                        Bottom += ys_[k]            
                                elif Graph_type == 'Stacked Area':
                                    ax[i].stackplot(np.array(xs_) + X_Shift, ys_[:len(self.selected_scores)], labels = self.selected_scores, colors=prop_cycle_color)
                                    if self.Add_error_bars_CB.isChecked() and self.add_errors:
                                        Bottom = np.zeros(len(Checked_bins[0]))
                                        for k in range(len(self.selected_scores)):
                                            ax[i].errorbar(np.array(xs_) + X_Shift, ys_[k] + Bottom, np.array(ys_err[k]), fmt = '|', ecolor='black')
                                            Bottom += ys_[k]

                                ax[i].set_xlabel(self.Curve_xLabel.text())
                                if 'low' in self.Plot_By_Key or 'center' in self.Plot_By_Key:
                                    if self.x_Format_CB.currentIndex() > 0:
                                        ax[i].xaxis.set_major_formatter(FuncFormatter(self.scientific_notation_formatter))
                                ax[i].set_ylabel(self.Curve_yLabel.text())
                                ax[i].yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
                                ax[i].ticklabel_format(axis='y', style='scientific', scilimits=(0, 0))  # Force scientific notation

                                if self.YSecondary: # and Graph_type not in ['Stacked Area', 'Stacked Bars']: #, 'Bar']:
                                    ax2.set_ylabel(self.Curve_y2Label.text())
                                    ax2.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
                                    ax2.ticklabel_format(axis='y', style='scientific', scilimits=(0, 0))  # Force scientific notation

                                if Graph_type in ['Stacked Area', 'Stacked Bars', 'Bar']:  
                                    ax[i].set_xticks(X_ + X_Shift, Bins_For_Title[0])           

                                if score in ['flux', 'current']:
                                    Subtitle = ''
                                else:
                                    if len(self.selected_nuclides) == 1 and nuclide == 'total':
                                        Subtitle = ''
                                    else:  
                                        Subtitle = '\nnuclide ' + str(nuclide)

                                Title = self.Curve_title.text()
                                if self.n_filters >= 2:
                                    Title = Title + ' - ' + BIN2 + str(Bins_For_Title2[j2]).replace("'","") + UNIT2
                                    if self.n_filters >= 3:
                                        Title = Title + BIN3 + str(Bins_For_Title3[j3]).replace("'","") + UNIT3
                                        if self.n_filters >= 4:
                                            Title = Title + '\n' + BIN4 + str(Bins_For_Title4[j4]).replace("'","") + UNIT4
                                            if self.n_filters >= 5:
                                                Title = Title + ' - ' + BIN5 + str(Bins_For_Title5[j5]).replace("'","") + UNIT5
                                                if self.n_filters >= 6:
                                                    Title = Title + ' - ' + BIN6 + str(Bins_For_Title6[j6]).replace("'","") + UNIT6
                                
                                if 'in cell' in Title: 
                                    Cell_id = int(Title.split('in cell')[1].lstrip()[0])
                                    if Cell_id in self.Cells_id:
                                        name = self.Cells[self.Cells_id.index(Cell_id)]
                                        Title = Title.replace('in cell ' + str(Cell_id), 'in ' + name + ' cell').replace('  ', ' ')
                                if 'born in' in Title: 
                                    Cell_id = int(Title.split('born in')[1].lstrip()[0])
                                    if Cell_id in self.Cells_id:
                                        name = self.Cells[self.Cells_id.index(Cell_id)]
                                        Title = Title.replace('born in ' + str(Cell_id), 'born in ' + name).replace('  ', ' ')
                                if 'from' in Title: 
                                    Cell_id = int(Title.split('from')[1].lstrip()[0])
                                    if Cell_id in self.Cells_id:
                                        name = self.Cells[self.Cells_id.index(Cell_id)]
                                        Title = Title.replace('from ' + str(Cell_id), 'from ' + name).replace('  ', ' ')
                                    
                                ax[i].set_title(Title + Subtitle)
                                self.Labels_Font(ax[i], plt)
                                self.Change_Scales(ax[i], Graph_type)
                                if self.YSecondary and score == 'flux' and Graph_type not in ['Stacked Area', 'Stacked Bars']: #, 'Bar']:
                                    self.Change_Scales(ax2, Graph_type)
                                    ax2.yaxis.label.set_size(int(self.yFont_CB.currentText()))
                                                    
                                

                                # Add legends
                                if len(self.selected_scores) > 1: 
                                    #if Graph_type in ['Lin-Lin', 'Scatter', 'Stairs']:
                                    if Graph_type in ['Lin-Lin', 'Scatter', 'Stairs', 'Bar']:
                                        if self.YSecondary:
                                            ax[i].legend(lines1 + lines2, labels1 + labels2) #, prop = { "size": LegendeFontSize }, loc="upper left")
                                        else:
                                            ax[i].legend(lines1, labels1) #, prop = { "size": LegendeFontSize }, loc="upper left")
                                    else:
                                        ax[i].legend(self.selected_scores)

                                # Add grids
                                if self.xgrid:
                                    ax[i].xaxis.grid(self.xgrid, which=self.which_grid, color='gray', linestyle='-', linewidth=0.5)
                                if self.ygrid:
                                    ax[i].yaxis.grid(self.ygrid, which=self.which_grid, color='gray', linestyle='-', linewidth=0.5)
                                if self.y2grid:
                                    if self.YSecondary and score == 'flux' and Graph_type not in ['Stacked Area', 'Stacked Bars']:  #, 'Bar']:
                                        ax2.yaxis.grid(self.y2grid, which=self.which_grid, color='olive', linestyle='--', linewidth=0.5) 

                                i += 1   # increment curves number

                                if not self.Stack_Plot:
                                    fig.show()
                                    fig.tight_layout()

    def scientific_notation_formatter(self, val, pos):
        # Define a custom formatter function
        if val == 0:
            return "0"  # Handle the case for zero
        exponent = int(np.floor(np.log10(abs(val))))
        base = val / (10**exponent)
        if base == 1:
            if exponent in [0, 1]:
                return f"{base * 10**exponent:.1f}"
            else:
                return f"$10^{{{exponent}}}$"
        if exponent in [-1, 0, 1]:
            return f"{base * 10**exponent:.1f}"
        if self.x_Format_CB.currentIndex() == 1:
            return f"${base:.1f} \\ 10^{{{exponent}}}$"  # Format with LaTeX
        elif self.x_Format_CB.currentIndex() == 2:
            return f"${base:.2f} \\ 10^{{{exponent}}}$"
        elif self.x_Format_CB.currentIndex() == 3:
            return f"${base:.3f} \\ 10^{{{exponent}}}$"

    def Enable_Tally_Normalizing(self, checked):
        #self.Checked_Keys_Norm = []
        self.Norm_Bins_comboBox.model().dataChanged.connect(self.Deactivate_Norm_BW)
        if checked:
            self.Normalizing_GB.show()
        else:
            self.Normalizing_GB.hide()
            self.Norm_to_BW_CB.setChecked(False)
            self.Norm_to_Vol_CB.setChecked(False)
            self.Norm_to_Power_CB.setChecked(False)
            self.Norm_to_Heating_CB.setChecked(False)
            self.Norm_to_UnitLethargy_CB.setChecked(False)
            self.Norm_to_SStrength_CB.setChecked(False)

    def Verify_Q_Nu_Value(self, LE):
        if LE == 'self.Q_LE':
            if LE.text() == '' or LE.text() == '0':
                self.showDialog('Invalid Q value!')
                return
        elif LE == 'self.Nu_LE':
            if LE.text() == '' or LE.text() == '0':
                self.showDialog('Invalid \u03BD value!')
                return

        if self.Norm_to_Power_CB.isChecked():
            self.Normalize_to_Power()

    def Normalizing_Settings(self):    # called by Display_scores
        # Set normalizing parameters 
        self.Q_LE.textChanged.connect(lambda:self.Verify_Q_Nu_Value(self.Q_LE))
        self.Nu_LE.textChanged.connect(lambda:self.Verify_Q_Nu_Value(self.Nu_LE))
        self.ENERGY_ANGLE_FILTER = ['EnergyFilter', 'EnergyoutFilter', 'MuFilter', 'PolarFilter', 'AzimuthalFilter', 'TimeFilter']
        self.Norm_Keys = ['energy', 'mu', 'polar', 'azimuthal', 'time']
        self.Norm_Available_Keys = [key.split()[0] for key in self.df_Keys if 'low' in key]
        Norm_CBox = [self.Norm_to_Power_CB, self.Norm_to_Heating_CB, self.Norm_to_UnitLethargy_CB, self.Norm_to_Vol_CB, 
                    self.Norm_to_BW_CB]
        Norm_LE = [self.Nu_LE, self.Heating_LE, self.Q_LE, self.Power_LE, self.Factor_LE, self.Keff_LE, self.S_Strength_LE]
        validator_positif = QRegExpValidator(QRegExp("((\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?)"))   
        for LE in Norm_LE:
            LE.setValidator(validator_positif)
        self.Norm_Bins_comboBox.clear()
        self.Norm_Bins_comboBox.addItem('Check item')      
        self.Norm_Bins_comboBox.addItems(self.Norm_Available_Keys)
        self.Norm_Bins_comboBox.model().item(0).setEnabled(False)

        if self.run_mode == 'eigenvalue': 
            for item in power_items:
                item.setEnabled(True)
            self.Keff_LE.setEnabled(False)
            self.Norm_to_SStrength_CB.setEnabled(False)
            self.S_Strength_LE.setEnabled(False)
            self.Norm_to_Heating_CB.stateChanged.connect(self.onStateChange)
            self.Norm_to_Power_CB.stateChanged.connect(self.onStateChange)
            self.Norm_to_Heating_CB.toggled.connect(self.Normalize_to_Power)
            self.Norm_to_Power_CB.toggled.connect(self.Normalize_to_Power)
            self.Power_LE.textChanged.connect(self.Normalize_to_Power)
            self.Heating_LE.textChanged.connect(self.Normalize_to_Power)
        else:
            for item in power_items:
                item.setEnabled(False)
            self.Norm_to_SStrength_CB.setEnabled(True)
        for item in Norm_Other:
            item.setEnabled(True)
        for item in Norm_CBox:
            item.setChecked(False)
        if any(any(element2 in element1 for element2 in self.Norm_Keys) for element1 in self.df_Keys):
            self.Norm_to_BW_CB.setEnabled(True)
            self.label_37.setEnabled(True)
            self.Norm_Bins_comboBox.setEnabled(True)
        else:
            self.Norm_to_BW_CB.setEnabled(False)
            self.label_37.setEnabled(False)
            self.Norm_Bins_comboBox.setEnabled(False)
        if any('energy' in item for item in self.df_Keys):
            self.Norm_to_UnitLethargy_CB.setEnabled(True)
        else:
            self.Norm_to_UnitLethargy_CB.setEnabled(False)

    def Normalizing(self):             # called by Plot_Scores
        if self.Norm_to_BW_CB.isChecked() or self.Norm_to_UnitLethargy_CB.isChecked() or self.Norm_to_Vol_CB.isChecked() \
                                        or self.Norm_to_Power_CB.isChecked() or self.Norm_to_SStrength_CB.isChecked() \
                                        or self.Norm_to_Heating_CB.isChecked():
            self.Normalization = True 
        else:
            self.Normalization = False
            return
        if self.Norm_to_BW_CB.isChecked() and self.Norm_to_UnitLethargy_CB.isChecked() and len(self.Checked_Keys_Norm) == 1:
            self.showDialog('Warning', "Couldn't combine both energy bin widh and unit of lethargy in normalizing data! " )
            return
        
        df = self.df_filtered.copy()
        count_row = df.shape[0]
        self.Normalizing_Factor = np.ones(count_row)
        Checked_bins = [''] * self.n_filters
        key = [''] * self.n_filters        
        for idx in range(self.n_filters):
            Checked_bins[idx] = self.DATA[idx]['Checked_bins']
            key[idx] = self.DATA[idx]['KEY']  

        # Normalize to power
        if self.Norm_to_Power_CB.isChecked() or self.Norm_to_Heating_CB.isChecked():
            self.Normalizing_Factor *= np.array(self.Power_Factor)
        # Normalize to source strength
        elif self.Norm_to_SStrength_CB.isChecked():
            self.Normalizing_Factor *= np.array(self.Strength_Factor)
        # Normalize to cells volume
        if self.Norm_to_Vol_CB.isChecked() and 'MeshFilter' not in self.Filter_names: 
            self.Normalizing_Factor *= self.Volume_Factor 
        # Normalize to variable bin width
        if self.Norm_to_BW_CB.isChecked():
            self.Normalizing_Factor *= self.Bin_Factor
        # Normalize to unit of lethargy
        elif self.Norm_to_UnitLethargy_CB.isChecked():
            self.Normalizing_Factor *= self.Lethargy_Factor
    
        # multiply scores and std. dev. by Normalizing_Factor
        #if self.add_errors:
        df.loc[:,['mean', 'std. dev.']] *= np.array(self.Normalizing_Factor[:, None])  # to be verified
        #else:
        #    df.loc[:,['mean']] *= np.array(self.Normalizing_Factor[:, None])  # to be verified

        df['multiplier'] = self.Normalizing_Factor.tolist()

        self.df_filtered_normalized = df
        self.Print_Formated_df(self.df_filtered_normalized.copy(), self.tally_id, self.editor)

    @pyqtSlot(int)
    def onStateChange(self, state):
        if state == Qt.Checked:
            if self.sender() == self.Norm_to_Power_CB:
                self.Norm_to_Heating_CB.setChecked(False)
            elif self.sender() == self.Norm_to_Heating_CB:
                self.Norm_to_Power_CB.setChecked(False)

    def Normalize_to_Bin_Width(self, checked):
        if self.Norm_Bins_comboBox.checkedItems():
            self.Checked_Keys_Norm = [self.Norm_Bins_comboBox.itemText(i) for i in self.Norm_Bins_comboBox.checkedItems()]
        else:
            self.Checked_Keys_Norm = []
        if checked:
            self.Norm_to_UnitLethargy_CB.setEnabled(False)
            if len(self.Checked_Keys_Norm) == 0:
                self.showDialog('Warning', 'Check item first for bin width normalization!')
                self.Norm_to_BW_CB.setChecked(False)
                return
            else:
                df = self.df_filtered.copy()
                count_row = df.shape[0]                
                self.Bin_Factor = [''] * self.n_filters
                self.Bin_Factor = np.ones(count_row)
                HIGH_Keys = [key for key in self.df_Keys if 'high' in key]
                
                for i in range(self.n_filters): 
                    if i < len(self.Checked_Keys_Norm):
                        elem = self.Checked_Keys_Norm[i]
                        for key in self.Keys:
                            if elem in key and 'low' in key:
                                idx = self.Keys.index(key)
                                Low = df[key].values[:]
                                High = df[HIGH_Keys[idx - 1]].values[:]
                                self.Bin_Factor *= [1. / (y - x) for x,y in zip(Low, High)]
        else:
            if 'energy' in self.Norm_Available_Keys:
                self.Norm_to_UnitLethargy_CB.setEnabled(True)
            for i in range(len(self.Norm_Available_Keys) + 1):
                self.Norm_Bins_comboBox.setItemChecked(i, False)
            self.Norm_Bins_comboBox.setCurrentIndex(0)
        
        self.Normalize_to_Bin_Width_Units(checked)
        
    def Normalize_to_Bin_Width_Units(self, checked):
        if 'MeshFilter' not in self.Filter_names:    # plot scores
            if checked:
                yText = self.Curve_yLabel.text()
                if self.YSecondary:
                    y2Text = self.Curve_y2Label.text()
                for elem in self.Checked_Keys_Norm:
                    i = [i for i, item in enumerate(self.Filter_names) if elem in item.replace('Filter', '').lower()][0]
                    if self.UNIT[i] == '':
                        unit = ''
                    elif self.UNIT[i] == ' eV' and 'eV' in yText and " eV\u207B\u00B9" not in yText:
                        unit = ''
                        self.Curve_yLabel.setText(yText.replace(' eV', ''))
                    else:
                        unit = f" {self.UNIT[i]}\u207B\u00B9"
                        if unit not in yText:
                            self.Curve_yLabel.setText(yText + unit)
                        else:
                            self.Curve_yLabel.setText(yText)
                    
                    if self.YSecondary:
                        unit = f" {self.UNIT[i]}\u207B\u00B9"
                        if unit not in y2Text:
                            self.Curve_y2Label.setText(y2Text + unit)
                        else:
                            self.Curve_y2Label.setText(y2Text)
            else:
                for elem in self.Norm_Available_Keys:
                    if len(self.selected_scores): 
                        score = self.selected_scores[0]
                        if score in self.ENERGY_SCORES:
                            yText = score + self.ENERGY_SCORES_UNIT
                            self.Curve_yLabel.setText(yText.replace('  ', ' '))
                        else:    
                            i = [i for i, item in enumerate(self.Filter_names) if elem in item.replace('Filter', '').lower()][0]
                            if self.UNIT[i] != '':
                                unit = f"{self.UNIT[i]}\u207B\u00B9"
                                yText = self.Curve_yLabel.text().replace(unit, '')
                                self.Curve_yLabel.setText(yText.replace('  ', ' '))
                            else:
                                yText = self.Curve_yLabel.text()
                    
                    if self.YSecondary:
                        if self.UNIT[i] != '':
                            unit = f"{self.UNIT[i]}\u207B\u00B9"
                            y2Text = self.Curve_y2Label.text().replace(unit, '')
                        else:
                            y2Text = self.Curve_y2Label.text()
                        self.Curve_y2Label.setText(y2Text.replace('  ', ' '))

                #self.Curve_yLabel.setText(yText.replace('  ', ' '))
        else:
            if checked:
                Title = self.Curve_title.text()
                for elem in self.Checked_Keys_Norm:
                    i = self.Checked_Keys_Norm.index(elem)
                    if self.UNIT[i] == '':
                        unit = ''
                    else:
                        unit = f"{self.UNIT[i]}\u207B\u00B9"
                    if unit not in Title:
                        self.Curve_title.setText(Title + unit)
                    else:
                        self.Curve_title.setText(Title)
            else:
                for elem in self.Norm_Available_Keys:
                    i = self.Norm_Available_Keys.index(elem)
                    unit = f"{self.UNIT[i]}\u207B\u00B9"
                    Title = self.Curve_title.text().replace(unit, '')
                self.Curve_title.setText(Title)

    def Deactivate_Norm_BW(self):
        try:
            Checked_Keys = self.Checked_Keys_Norm
            self.Norm_to_BW_CB.setChecked(False)
            #for i in range(1, len(self.Norm_Available_Keys)):
            for i,item in enumerate(self.Norm_Available_Keys):
                #item = self.Norm_Bins_comboBox.model().item(i)
                if item.checkState() == Qt.Checked:
                    if item not in Checked_Keys:
                        Checked_Keys.append(item)  
                else:
                    if item in Checked_Keys:
                        Checked_Keys.pop(Checked_Keys.index(item))  
            for i,item in enumerate(self.Norm_Available_Keys):
                if item in Checked_Keys:
                    self.Norm_Bins_comboBox.model().item(i).setCheckState(Qt.Checked)

            self.Normalize_to_Bin_Width(True)
        except:
            pass

    def Normalize_to_SourceStrength(self):
        self.Norm_to_Heating_CB.setChecked(False)
        self.Norm_to_Heating_CB.setEnabled(False)
        self.Norm_to_Power_CB.setChecked(False)
        self.Norm_to_Power_CB.setEnabled(False)
        if self.S_Strength_LE.text():
            if list(self.S_Strength_LE.text())[-1] not in ['E', 'e', '+', '-']:
                self.Strength_Factor = float(self.S_Strength_LE.text())                  # MW = J/s
            else:
                return
        else:
            self.showDialog('Warning', 'Enter source strength first!')
            return
        
        self.Normalize_to_SStrength_Units()
        
    def Normalize_to_SStrength_Units(self):
        if 'MeshFilter' not in self.Filter_names:
            yText = self.Curve_yLabel.text()
            if self.Norm_to_SStrength_CB.isChecked():
                if 's\u207B\u00B9' not in yText:
                    yText = yText.replace('per source particle', '') + ' s\u207B\u00B9 '
                else:
                    yText = yText.replace('s\u207B\u00B9', '') + ' s\u207B\u00B9 '
                if self.YSecondary:
                    y2Text = self.Curve_y2Label.text()
                    if 's\u207B\u00B9' not in y2Text:
                        y2Text = y2Text.replace('per source particle', '').replace('  ', ' ') + ' s\u207B\u00B9 '
                    else:
                        y2Text = y2Text.replace('s\u207B\u00B9', '') + ' s\u207B\u00B9 '
                    self.Curve_y2Label.setText(y2Text.replace('  ', ' '))
            else:
                if self.YSecondary:
                    y2Text = self.Curve_y2Label.text()
                    self.Curve_y2Label.setText(y2Text.replace('s\u207B\u00B9', '') + ' per source particle ')
                yText = yText.replace('s\u207B\u00B9', '') + ' per source particle '
            self.Curve_yLabel.setText(yText.replace('  ', ' '))
        else:
            Title = self.Curve_title.text()
            if self.Norm_to_SStrength_CB.isChecked():
                if 's\u207B\u00B9' not in Title:
                    Title = Title + ' s\u207B\u00B9 '
                else:
                    Title = Title.replace('s\u207B\u00B9', '') + ' s\u207B\u00B9 '
            else:
                Title = Title.replace('s\u207B\u00B9', '')
            self.Curve_title.setText(Title.replace('  ', ' '))

    def Normalize_to_Power(self):
        self.Norm_to_SStrength_CB.setChecked(False)
        self.Norm_to_SStrength_CB.setEnabled(False)
        self.Factor_LE.clear()
        if self.Power_LE.text():
            if list(self.Power_LE.text())[-1] not in ['E', 'e', '+', '-']:
                Power = float(self.Power_LE.text())                  # W = J/s
            else:
                return
        else:
            self.showDialog('Warning', 'Enter reactor power first!')
            return
        if self.Norm_to_Power_CB.isChecked():
            self.Keff_LE.setText(str("{:.5f}".format(self.keff)))
            if self.Power_LE.text():
                if self.Nu_LE.text() not in ['', '0']:
                    if 'E' in self.Nu_LE.text():
                        if self.Nu_LE.text().split('E')[1] in ['', '+', '-']:
                            return
                    Nu = float(self.Nu_LE.text())
                else:
                    Nu = 2.45
                    self.showDialog('Warning', 'Invalid \u03BD value! Default \u03BD = 2.45 will be used!')
                    self.Nu_LE.setText('2.45')

                if self.Q_LE.text() not in ['', '0']:
                    if 'E' in self.Q_LE.text():
                        if self.Q_LE.text().split('E')[1] in ['', '+', '-']:
                            return
                    Q = float(self.Q_LE.text()) * 1.6022E-13       # MeV * J/eV = J
                else:
                    Q = 193. * 1.6022E-13
                    self.showDialog('Warning', 'Invalid Q value! Default Q = 193. MeV will be used!')
                    self.Q_LE.setText('193.')
                
                Keff = self.keff
                Factor = Power * Nu / Q / Keff      # 1/s 
            else:
                Factor = 1.
        elif self.Norm_to_Heating_CB.isChecked():
            if self.Heating_LE.text():
                if list(self.Heating_LE.text())[-1] not in ['E', 'e', '+', '-']:
                    H = float(self.Heating_LE.text())                  # MW = J/s
                else:
                    return
                H = float(self.Heating_LE.text()) * 1.6022E-19   # eV * J/eV  = J
                if H != 0:
                    Factor = Power / H                  # 1/s
                else:
                    Factor = 1.
            else:
                Factor = 1.         
        else:
            Factor = 1.
        self.Power_Factor = Factor
        self.Factor_LE.setText(str(self.Power_Factor))
        self.Normalize_to_Power_Units()

    def Normalize_to_Power_Units(self):
        if 'MeshFilter' not in self.Filter_names:
            yText = self.Curve_yLabel.text()
            if self.Norm_to_Power_CB.isChecked() or self.Norm_to_Heating_CB.isChecked(): # or self.Norm_to_SStrength_CB.isChecked():
                if 's\u207B\u00B9' not in yText:
                    if 'per source particle' in yText:
                        yText = yText.replace('per source particle', '') + ' s\u207B\u00B9 '
                    else:
                        yText = yText + ' s\u207B\u00B9 '
                else:
                    yText = yText.replace('s\u207B\u00B9', '') + ' s\u207B\u00B9 '
                
                self.Curve_yLabel.setText(yText.replace('  ', ' '))

                if self.YSecondary:
                    y2Text = self.Curve_y2Label.text()
                    if 's\u207B\u00B9' not in y2Text:
                        if 'per source particle' in y2Text:
                            y2Text = y2Text.replace('per source particle', '') + ' s\u207B\u00B9 '
                        else:
                            y2Text = y2Text + ' s\u207B\u00B9 '
                    else:
                        y2Text = y2Text.replace('s\u207B\u00B9', '') + ' s\u207B\u00B9 '

                    self.Curve_y2Label.setText(y2Text.replace('  ', ' '))
            else:
                yText = yText.replace('s\u207B\u00B9', '') + ' per source particle '
                self.Curve_yLabel.setText(yText.replace('  ', ' '))

                if self.YSecondary:
                    y2Text = self.Curve_y2Label.text()
                    y2Text = y2Text.replace('s\u207B\u00B9', '') + ' per source particle '
                    self.Curve_y2Label.setText(y2Text.replace('  ', ' '))
        else:
            Title = self.Curve_title.text()
            if self.Norm_to_Power_CB.isChecked() or self.Norm_to_Heating_CB.isChecked(): # or self.Norm_to_SStrength_CB.isChecked():
                if 's\u207B\u00B9' not in Title:
                    if 'per source particle' in Title:
                        Title = Title.replace('per source particle', '') + ' s\u207B\u00B9 '
                    else:
                        Title = Title + ' s\u207B\u00B9 '
                else:
                    Title = Title.replace('s\u207B\u00B9', '') + ' s\u207B\u00B9 '
            else:
                Title = Title.replace('s\u207B\u00B9', '') + ' per source particle '
            self.Curve_title.setText(Title.replace('  ', ' '))

    def Normalize_to_Unit_of_Lethargy(self, checked):
        import math
        df = self.df_filtered.copy()
        count_row = df.shape[0]
        # Obtain the width of Lethargy Energy
        self.Lethargy_Factor = np.ones(count_row)
        if checked: 
            key = 'energy low [eV]'   
            if key in self.df_Keys:    
                idx = self.df_Keys.index(key)
                Low = df[key].values[:]
                High = df[self.df_Keys[idx+1]].values[:]
            self.Lethargy_Factor *= [1. / math.log(y / x) for x,y in zip(Low, High)]
            self.Norm_to_BW_CB.setEnabled(False)
        else:
            self.Norm_to_BW_CB.setEnabled(True)
        self.Normalize_to_Unit_of_Lethargy_Units(checked)

    def Normalize_to_Unit_of_Lethargy_Units(self, checked):
        if 'MeshFilter' not in self.Filter_names:
            if checked:    
                yText = self.Curve_yLabel.text()
                if 'per unit lethargy' not in yText:
                    self.Curve_yLabel.setText(yText + ' per unit lethargy ')
                else:
                    self.Curve_yLabel.setText(yText.replace('per unit lethargy', '') + ' per unit lethargy ')

                if self.YSecondary:
                    y2Text = self.Curve_y2Label.text()
                    if 'per unit lethargy' not in y2Text:
                        self.Curve_y2Label.setText(y2Text + ' per unit lethargy ')
                    else:
                        self.Curve_y2Label.setText(yText.replace('per unit lethargy', '').replace('  ', ' ') + ' per unit lethargy ')
            else:
                yText = self.Curve_yLabel.text()
                self.Curve_yLabel.setText(yText.replace(' per unit lethargy ', '').replace('  ', ' '))
                
                if self.YSecondary:
                    y2Text = self.Curve_y2Label.text()
                    self.Curve_y2Label.setText(y2Text.replace(' per unit lethargy ', '').replace('  ', ' '))
        else:
            if checked:    
                Title = self.Curve_title.text()
                if 'per unit lethargy' not in Title:
                    self.Curve_title.setText(Title + ' per unit lethargy ')
                else:
                    self.Curve_title.setText(Title.replace('per unit lethargy', '') + ' per unit lethargy ')
            else:
                Title = self.Curve_title.text()
                self.Curve_title.setText(Title.replace(' per unit lethargy ', '').replace('  ', ' '))

    def Normalize_to_Volume(self, checked):
        # Obtain the width of Lethargy Energy
        if checked: 
            if 'MeshFilter' not in self.Filter_names:
                self.Volumes = self.LE_to_List(self.Vol_List_LE)
                n_bins = 0
                if self.n_filters > 0:
                    if 'cell' in self.df_Keys:
                        idx = self.Keys.index('cell')
                        Checked_Cells = self.DATA[idx]['Checked_bins']
                        n_bins = len(Checked_Cells)
                    else:
                        n_bins = 1
                    if len(self.Volumes) != n_bins:
                        self.showDialog('Warning', "Numbers of checked cells and entered volumes don't match!\n")
                        self.Norm_to_Vol_CB.setChecked(False)
                        return
                else:
                    n_bins = 1
                    if len(self.Volumes) > n_bins:
                        self.showDialog('Warning', 'Only first value of volumes list will be affected to root cell!')
                        self.Volumes = [self.Volumes[0]]
                        self.Vol_List_LE.setText(str(self.Volumes[0]))
                        Checked_Cells = self.DATA['root']['Checked_bins']
                    elif len(self.Volumes) == 0:
                        self.showDialog('Warning', 'Enter volume of the root cell!')
                        self.Norm_to_Vol_CB.setChecked(False)
                        return

                df = self.df_filtered.copy()
                count_row = df.shape[0]                
                self.All_Volumes = np.ones(count_row)

                if 'cell' in self.df_Keys:
                    for key in self.Keys:
                        if key == 'cell':
                            idx = self.Keys.index(key)
                            cells = df[key].values[:]
                            for i in range(count_row):
                                j = Checked_Cells.index(cells[i])
                                self.All_Volumes[i] = self.Volumes[j]
                else:
                    for i in range(count_row):
                        self.All_Volumes[i] = self.Volumes[0]

                self.Volume_Factor = np.reciprocal(self.All_Volumes).tolist()

        self.Normalize_to_Volume_Units(checked)

    def Normalize_to_Volume_Units(self, checked):
        if 'MeshFilter' not in self.Filter_names:        
            yText = self.Curve_yLabel.text()   
            if checked: 
                if len(self.selected_scores) == 1:
                    if 'flux' in yText:
                        if '-cm' in yText:
                            yText = yText.replace('-cm ', " cm\u207B\u00B2 ")
                        else:
                            if "cm\u207B\u00B2" not in yText:
                                yText = yText + " cm\u207B\u00B2 "
                    else:
                        if 'cm\u00b3' in yText:
                            yText = yText.replace('cm\u00b3', '')
                        else:
                            yText = yText + " cm\u207B\u00B3 "
                else:
                    if 'cm\u00b3' in yText:
                        yText = yText.replace('cm\u00b3', '')
                    else:
                        if "cm\u207B\u00B3" not in yText:
                            yText = yText + " cm\u207B\u00B3 "                  
                    
                    if self.YSecondary: 
                        y2Text = self.Curve_y2Label.text()
                        if '-cm' in y2Text:
                            y2Text = y2Text.replace('-cm ', " cm\u207B\u00B2 ")
                        else:
                            if "cm\u207B\u00B2" not in y2Text:
                                y2Text = y2Text + " cm\u207B\u00B2 "
                            
                        self.Curve_y2Label.setText(y2Text)
            else:
                if 'flux' in yText:
                    yText = yText.replace(" cm\u207B\u00B2 ", '-cm ')
                else:
                    if "cm\u207B\u00B3" in yText:
                        yText = yText.replace(" cm\u207B\u00B3 ", '')
                    else:
                        yText = yText + ' cm\u00b3 '

                if self.YSecondary:
                    y2Text = self.Curve_y2Label.text()
                    if "cm\u207B\u00B2" in y2Text:
                        y2Text = y2Text.replace(" cm\u207B\u00B2 ", '-cm ')
                        if 'per source particle' in y2Text:
                            y2Text = y2Text.replace('per source particle', '') + ' per source particle '
                    self.Curve_y2Label.setText(y2Text.replace('  ', ' '))
            
            if 'per source particle' in yText:
                yText = yText.replace('per source particle', '') + ' per source particle '
            self.Curve_yLabel.setText(yText.replace('  ', ' '))
        else:
            if checked:
                Title = self.Curve_title.text()
                if 'flux' in Title:
                    if '-cm ' in Title:
                        Title = Title.replace('-cm ', " cm\u207B\u00B2 ")
                    else:
                        Title = Title + " cm\u207B\u00B2 "
                else:
                    if "cm\u207B\u00B3" not in Title:
                        Title = Title + " cm\u207B\u00B3 "
            else:
                Title = self.Curve_title.text()
                if 'flux' in Title:
                    Title = self.Curve_title.text().replace(" cm\u207B\u00B2 ", '-cm ')
                else:
                    Title = self.Curve_title.text().replace(" cm\u207B\u00B3 ", '')
            if ' per source particle ' in Title:
                Title = Title.replace(' per source particle ', '') + ' per source particle '
            self.Curve_title.setText(Title)

    def LE_to_List(self, LineEdit):
        text = LineEdit.text().replace('(', '').replace(')', '')
        if '*' in text: 
            text = text.replace('*', ' * ')
        for separator in [',', ';', ':', ' ']:
            if separator in text:
                text = str(' '.join(text.replace(separator, ' ').split()))
        List = text.split()
        while '*' in List:    
            index = List.index('*')
            n = int(List[index + 1]) - 1
            List.pop(index + 1)
            List.pop(index)
            insert_list = [List[index - 1] + ' '] * n
            List = self.insert_list_at_index(List, insert_list, index)
        Volumes = [float(item) for item in List]
        return Volumes

    def insert_list_at_index(self, main_list, insert_list, index):
        # Copy the main_list to avoid modifying it in given place
        result_list = main_list.copy()
        
        # Insert each element of insert_list into result_list at the specified index
        for element in insert_list:
            result_list.insert(index, element.strip())
            index += 1
        
        return result_list

    def Labels_Font(self, ax, PLT):
        titleFontSize = int(self.TitleFont_CB.currentText())
        xFontSize = int(self.xFont_CB.currentText())
        yFontSize = int(self.yFont_CB.currentText())
        xRotation = int(self.xLabelRot_CB.currentText())
        LegendeFontSize = int(self.Legende_CB.currentText())
        ax.title.set_size(titleFontSize)
        ax.xaxis.set_tick_params(labelsize=xFontSize*0.75, rotation=xRotation)
        ax.yaxis.set_tick_params(labelsize=yFontSize*0.75)
        ax.xaxis.label.set_size(xFontSize)
        ax.yaxis.label.set_size(yFontSize)
        if xRotation != 0:
            PLT.setp(ax.get_xticklabels(), ha="right", rotation_mode="anchor")
        PLT.rc('legend',fontsize=LegendeFontSize)
 
    def Change_Scales(self, PLT, Graph_type):
        if 'Keff' not in self.Tally_id_comboBox.currentText():
            if Graph_type in ['Lin-Lin','Scatter', 'Stairs']:  #'Stacked Area'
                if self.xLog_CB.isChecked():
                    if self.Plot_By_Key not in ['cell', 'surface', 'nuclide', 'score', 'material', 'universe']:
                        PLT.set_xscale('log')
        elif 'Keff' in self.Tally_id_comboBox.currentText():
            if self.xLog_CB.isChecked():
                PLT.set_xscale('log')
        if self.yLog_CB.isChecked():    
            PLT.set_yscale('log')

    def set_Scales(self): 
        if self.Graph_type_CB.currentIndex() == 0 and 'MeshFilter' not in self.Filter_names:
            for elm in self.buttons:
                elm.setEnabled(False)        
        else:
            if 'MeshFilter' in self.Filter_names:
                #self.Graph_type_CB.setCurrentIndex(0)
                #self.Graph_type_CB.setEnabled(False)
                self.Plot_by_CB.clear()            
            else:
                if 'Keff' not in self.Tally_id_comboBox.currentText():
                    self.Plot_By_Key = self.Plot_by_CB.currentText()
                    if self.Plot_By_Key in ['mu low', 'mu center of bin']:
                        self.Curve_xLabel.setText('$\mu$')
                    elif 'energy' in self.Plot_By_Key:
                        self.Curve_xLabel.setText(self.Plot_By_Key.split(' ')[0] + ' / eV')
                    elif 'polar' in self.Plot_By_Key or 'azimuthal' in self.Plot_By_Key:
                        self.Curve_xLabel.setText(self.Plot_By_Key.split(' ')[0] + ' / rad')
                    elif 'cell' in self.Plot_By_Key and len(self.Plot_By_Key) > 4:
                        self.Curve_xLabel.setText(self.Plot_By_Key.replace('cell', 'cell '))
                    else:
                        self.Curve_xLabel.setText(self.Plot_By_Key)
                    for elm in self.buttons:
                        elm.setEnabled(True)
                    if self.Graph_type_CB.currentText() in ['Stacked Bars', 'Stacked Area']:
                        self.xLog_CB.setEnabled(False)
                        self.Y2Label_CB.setChecked(False)
                        self.Y2Label_CB.setEnabled(False)
                        self.Curve_y2Label.setEnabled(False)
                    else:
                        if self.Graph_type_CB.currentText() == 'Bar':
                            self.xLog_CB.setEnabled(False)
                        elif self.Graph_type_CB.currentText() in ['Lin-Lin', 'Scatter', 'Stairs']:
                            if self.Plot_By_Key in ['cell', 'cellfrom', 'cellborn', 'distribcell', 'material', 
                                                    'universe', 'surface', 'particle' ,'collision', 'nuclide', 'score']:
                                self.xLog_CB.setEnabled(False)  
                            else:
                                self.xLog_CB.setEnabled(True)
                        if len(self.selected_scores) > 1 and 'flux' in self.selected_scores:
                            self.Y2Label_CB.setEnabled(True)
                            #self.Y2Label_CB.setChecked(True)
                            self.Curve_y2Label.setEnabled(True)
                        else:
                            self.Y2Label_CB.setEnabled(False)
                            self.Y2Label_CB.setChecked(False)
                            self.Curve_y2Label.setEnabled(False)
          
    def plot_grid_settings(self):
        self.xgrid = False; self.ygrid = False; self.y2grid = False
        if self.MinorGrid_CB.isChecked():
            self.which_grid = 'both'
        else:
            self.which_grid = 'major'
        if self.xGrid_CB.isChecked(): 
            self.xgrid = True
        else:
            self.xgrid = False
        if self.yGrid_CB.isChecked():
            self.ygrid = True
        else:
            self.ygrid = False
        if self.YSecondary:
            if self.y2Grid_CB.isChecked():
                self.y2grid = True
            else:
                self.y2grid = False

    def Activate_Curve_Type(self):
        try:
            if 'Keff' not in self.Tally_id_comboBox.currentText():
                for i in range(1,6):
                    self.Graph_type_CB.model().item(i).setEnabled(True)
        except:
            return

    def Deactivate_Curve_Type(self):
        try:
            for i in [3, 5]:
                self.Graph_type_CB.model().item(i).setEnabled(False)
        except:
            return

    def Mesh_settings(self, enabled):
        if not os.path.isfile(self.sp_file):
            self.showDialog('Warning', 'Select valid statepoint file!')
            return
        
        self.score_plot_PB.setEnabled(False)
        for filter in self.Filter_names:
            if filter == 'MeshFilter':
                idx = self.Filter_names.index(filter)
                self.Bins_comboBox[idx].clear()
                tally_id = int(self.Tally_id_comboBox.currentText())
                filter_id = self.filter_ids[idx]
                self.Bins_comboBox[idx].addItems(['Select bin', 'All bins'])
                self.Bins_comboBox[idx].model().item(0).setEnabled(False)
                if self.Mesh_xy_RB.isChecked():
                    self.xlabel.setText('xlabel')
                    self.ylabel.setText('ylabel')
                    if self.mesh_type == 'CylindricalMesh':
                        self.list_axis = ['slice at ' + Z for Z in self.Z_range]
                        self.Curve_xLabel.clear()
                        self.Curve_yLabel.clear()
                    else:
                        self.list_axis = ['slice at z = ' + str("{:.1E}cm".format(z_)) for z_ in self.z]
                        self.Curve_xLabel.setText('x/cm')
                        self.Curve_yLabel.setText('y/cm')
                        
                    self.spinBox.setValue(1)
                    self.spinBox_2.setValue(1)
                    self.spinBox.setMinimum(1)
                    self.spinBox.setMaximum(self.mesh_dimension[0])
                    self.spinBox_2.setMinimum(1)
                    self.spinBox_2.setMaximum(self.mesh_dimension[1])
                elif self.Mesh_xz_RB.isChecked():
                    if self.mesh_type == 'CylindricalMesh':
                        #self.list_axis = ['slice at \u03F4 = ' + str("{:.1f}".format(y_)) + ' °' for y_ in self.phi_center]
                        self.list_axis = ['slice at ' + Phi for Phi in self.Phi_range]
                        self.Curve_xLabel.setText('r/cm')
                    else:
                        self.list_axis = ['slice at y = ' + str("{:.1E}cm".format(y_)) for y_ in self.y]
                        self.Curve_xLabel.setText('x/cm')
                    self.Curve_yLabel.setText('z/cm')
                    self.xlabel.setText('xlabel')
                    self.ylabel.setText('zlabel')
                    self.spinBox.setValue(1)
                    self.spinBox_2.setValue(1)
                    self.spinBox.setMinimum(1)
                    self.spinBox.setMaximum(self.mesh_dimension[0])
                    self.spinBox_2.setMaximum(self.mesh_dimension[2])
                elif self.Mesh_yz_RB.isChecked():
                    self.list_axis = ['slice at x = ' + str("{:.1E}cm".format(x_)) for x_ in self.x]
                    self.xlabel.setText('ylabel')
                    self.ylabel.setText('zlabel')
                    self.Curve_xLabel.setText('y/cm')
                    self.Curve_yLabel.setText('z/cm')
                    self.spinBox.setValue(1)
                    self.spinBox_2.setValue(1)
                    self.spinBox_2.setMinimum(1)
                    self.spinBox.setMaximum(self.mesh_dimension[1])
                    self.spinBox_2.setMaximum(self.mesh_dimension[2])

                bins = self.list_axis
                self.Tallies[tally_id][filter_id]['bins'] = bins
                self.Bins_comboBox[idx].addItems(bins)
                for i in range(len(bins) + 1):
                    self.Bins_comboBox[idx].setItemChecked(i, False)
                self.Tallies[tally_id][filter_id]['Checked_bins_indices'].clear()

    def Mesh_Spec(self):
        if self.Mesh_xy_RB.isChecked():
            self.dim1 = self.mesh_dimension[0]
            self.dim2 = self.mesh_dimension[1]
            self.LL1 = self.mesh_LL[0]
            self.LL2 = self.mesh_LL[1]
            self.UR1 = self.mesh_UR[0]
            self.UR2 = self.mesh_UR[1]
        elif self.Mesh_xz_RB.isChecked():
            self.dim1 = self.mesh_dimension[0]
            self.dim2 = self.mesh_dimension[2]
            self.LL1 = self.mesh_LL[0]
            self.LL2 = self.mesh_LL[2]
            self.UR1 = self.mesh_UR[0]
            self.UR2 = self.mesh_UR[2]
        elif self.Mesh_yz_RB.isChecked():
            self.dim1 = self.mesh_dimension[1]
            self.dim2 = self.mesh_dimension[2]
            self.LL1 = self.mesh_LL[1]
            self.LL2 = self.mesh_LL[2]
            self.UR1 = self.mesh_UR[1]
            self.UR2 = self.mesh_UR[2]

    def Stack_Plot_Mesh(self, df):
        Stack_Size = self.row_SB.value() * self.col_SB.value()
        self.WillPlot = True

        if Stack_Size == 1:
            self.showDialog('Warning', 'Stacking plots need more rows and/or columns !')
            self.row_SB.setValue(2)
        if self.N_Fig == 1:
            self.Stack_Plot = False
            self.Plot_Mesh(df) 
            return        
        if Stack_Size < self.N_Fig:
            qm = QMessageBox
            ret = qm.question(self, 'Warning',' Stack size : ' + str(Stack_Size) + ' less than total available plots : ' + 
                                     str(self.N_Fig) + '\nLast plots will be removed! Continue ploting ?', qm.Yes | qm.No)
            if ret == qm.Yes:
                pass 
            elif ret == qm.No:
                self.WillPlot = False
                return

        if self.mesh_type in ['RegularMesh', 'RectilinearMesh']:
            fig, axs = plt.subplots(self.row_SB.value(), self.col_SB.value(), figsize=(8, 6),)  #, layout="constrained")   #, sharex=True)
        elif self.mesh_type == 'CylindricalMesh':
            if self.Mesh_xy_RB.isChecked():
                plot_basis = 'rphi'
                fig, axs = plt.subplots(self.row_SB.value(), self.col_SB.value(), figsize=(8, 6),subplot_kw={'projection': 'polar'})
            else:
                fig, axs = plt.subplots(self.row_SB.value(), self.col_SB.value(), figsize=(8, 6),)  #, layout="constrained")   #, sharex=True)

        if self.N_Fig < Stack_Size:
            ax = [None] * Stack_Size
        else:    
            ax = [None] * self.N_Fig            
        
        for i, ax_ in enumerate(axs.flat):
            ax[i] = ax_
        
        self.i_omitted = 0
        self.Plot_Mesh_Stack(df, fig, ax)

        if Stack_Size > self.N_Fig - self.i_omitted:
            for i in range(self.N_Fig - self.i_omitted, Stack_Size):
                if ax[i]:
                    ax[i].set_visible(False)        # to remove empty plots
        
        if self.WillPlot:
            fig.subplots_adjust(left=0.18, right=0.98, top=0.92, bottom=0.12)
            fig.show()
            fig.tight_layout()

    def Plot_Mesh(self, dff):
        df = dff.copy()
        key = self.mesh_axis_key
        Graph_Type = self.Graph_type_CB.currentText()

        if self.mesh_type == 'CylindricalMesh':
            if self.Mesh_xy_RB.isChecked():
                plot_basis = 'rphi'
            else:
                plot_basis = 'rz'
        elif self.mesh_type in ['RegularMesh', 'RectilinearMesh']:
            if self.Mesh_xy_RB.isChecked():
                plot_basis = 'xy'
            elif self.Mesh_xz_RB.isChecked():
                plot_basis = 'xz'
            elif self.Mesh_yz_RB.isChecked():
                plot_basis = 'yz'

        if self.xLog_CB.isChecked():                 # Interpolation to smooth data
            if self.mesh_type == 'RegularMesh':
                Interpolation = 'spline36'
            elif self.mesh_type == 'RectilinearMesh':
                Interpolation = 'gouraud'
            elif self.mesh_type == 'CylindricalMesh':
                Interpolation = 'gouraud'
        else:
            Interpolation = None

        if self.Norm_to_Vol_CB.isChecked():
            Volume_normalization = True
        else:
            Volume_normalization = False

        Filter_Names = [filter for filter in self.Filter_names if filter != 'MeshFilter' ]
        Keys_Loop = [key[0] for key in self.df.keys()[:-4] if 'mesh' not in key[0] and 'high' not in key[0]]
        mesh_idx = self.Filter_names.index('MeshFilter')
        N_Bins = 1
        idx_s = []
        Key_BINS = [''] * len(Keys_Loop)
        key1 = ''; BIN1 = ''; UNIT1 = ''; Checked_bins1 = ['']; Bins_For_Title1 = ['']
        key2 = ''; BIN2 = ''; UNIT2 = ''; Checked_bins2 = ['']; Bins_For_Title2 = ['']
        key3 = ''; BIN3 = ''; UNIT3 = ''; Checked_bins3 = ['']; Bins_For_Title3 = ['']
        key4 = ''; BIN4 = ''; UNIT4 = ''; Checked_bins4 = ['']; Bins_For_Title4 = ['']
        key5 = ''; BIN5 = ''; UNIT5 = ''; Checked_bins5 = ['']; Bins_For_Title5 = ['']
        i = 0
        for key1 in Keys_Loop:
            filter_name = key1.split(' ')[0].capitalize() +'Filter'
            if 'from' in filter_name: filter_name = filter_name.replace('from', 'From')
            idx = self.Filter_names.index(filter_name)
            idx_s.append(idx)
            N_Bins = N_Bins * len(self.Key_Selected_Bins[idx])
            Key_BINS[i] = self.Key_Selected_Bins[idx]
            i += 1
        if len(Keys_Loop) >= 1:
            Checked_bins1 = Key_BINS[0]; key1 = Keys_Loop[0]; BIN1 = self.BIN[1]; UNIT1 = self.UNIT[1]; Bins_For_Title1 = self.Bins_For_Title[1]
            if len(Keys_Loop) >= 2:
                Checked_bins2 = Key_BINS[1]; key2 = Keys_Loop[1]; BIN2 = self.BIN[2]; UNIT2 = self.UNIT[2]; Bins_For_Title2 = self.Bins_For_Title[2]
                if len(Keys_Loop) >= 3:
                    Checked_bins3 = Key_BINS[2]; key3 = Keys_Loop[2]; BIN3 = self.BIN[3]; UNIT3 = self.UNIT[3]; Bins_For_Title3 = self.Bins_For_Title[3]
                    if len(Keys_Loop) >= 4:
                        Checked_bins4 = Key_BINS[3]; key4 = Keys_Loop[3]; BIN4 = self.BIN[4]; UNIT4 = self.UNIT[4]; Bins_For_Title4 = self.Bins_For_Title[4]
                        if len(Keys_Loop) >= 5:
                            Checked_bins5 = Key_BINS[4]; key5 = Keys_Loop[4]; BIN5 = self.BIN[5]; UNIT5 = self.UNIT[5]; Bins_For_Title5 = self.Bins_For_Title[5] 

        Stack_Size = self.row_SB.value() * self.col_SB.value()
        if Stack_Size <= self.N_Fig:
            N_Figs = Stack_Size
        else:
            N_Figs = self.N_Fig
        if N_Figs > 20:
            qm = QMessageBox
            ret = qm.question(self, 'Warning',' More than 20 figures (' + str(N_Figs) + ') have been opened! \n This may consume too much memory.'+
                                '\n continue ploting ?', qm.Yes | qm.No)
            if ret == qm.Yes:
                pass 
            elif ret == qm.No:
                self.WillPlot = False
                return
        msg = 'Cannot plot in Log scale scores that are all null!\n'
        msg1 = ''
        msg2 = ''
        i_fig = 1

        for score in self.selected_scores:
            if score != '':
                Suptitle1 = ''
                for nuclide in self.selected_nuclides:
                    if nuclide != '':
                        for bin in self.checked_bins_indices:
                            Suptitle2 = 'score at '                            
                            if len(self.tally.filters[mesh_idx].mesh._grids) == 3:
                                Suptitle2 = Suptitle2 + str(self.Tallies[self.tally_id][self.filter_ids[mesh_idx]]['bins'][bin-2]).replace('slice at', '')
                            else:
                                if self.Mesh_xy_RB.isChecked():
                                    Suptitle2 = Suptitle2.replace('at ', '') + ' integrated on z axis'
                                elif self.Mesh_xz_RB.isChecked():
                                    if self.mesh_type == 'CylindricalMesh':
                                        Suptitle2 = Suptitle2.replace('at ', '') + ' integrated on \u03F4 axis'
                                    else:
                                        Suptitle2 = Suptitle2.replace('at ', '') + ' integrated on y axis'
                                elif self.Mesh_yz_RB.isChecked():
                                    Suptitle2 = Suptitle2.replace('at ', '') + ' integrated on x axis'
                            if self.Add_error_bars_CB.isChecked():
                                Suptitle2 = Suptitle2.replace('score', 'errors on score')
                            
                            for bin1 in Checked_bins1: 
                                i_bin1 = Checked_bins1.index(bin1)
                                for bin2 in Checked_bins2: 
                                    i_bin2 = Checked_bins2.index(bin2)
                                    for bin3 in Checked_bins3: 
                                        i_bin3 = Checked_bins3.index(bin3)
                                        for bin4 in Checked_bins4: 
                                            i_bin4 = Checked_bins4.index(bin4)
                                            for bin5 in Checked_bins5: 
                                                i_bin5 = Checked_bins5.index(bin5)
                                                yy = df[df.nuclide == nuclide]
                                                yy = yy[yy.score == score]
                                                yy = yy[yy[key] == bin - 1] 
                                                if len(Keys_Loop) >= 1:
                                                    yy = yy[df[key1] == bin1]
                                                    if len(Keys_Loop) >= 2:
                                                        yy = yy[df[key2] == bin2]
                                                        if len(Keys_Loop) >= 3:
                                                            yy = yy[df[key3] == bin3]
                                                            if len(Keys_Loop) >= 4:
                                                                yy = yy[df[key4] == bin4]
                                                                if len(Keys_Loop) >= 5:
                                                                    yy = yy[df[key5] == bin5]
                                                self.Print_Formated_df(yy.copy(), self.tally_id, self.editor)
                                                mean = np.transpose(np.array(yy['mean'].tolist()).reshape((self.dim1, self.dim2)))
                                                errors = np.transpose(np.array(yy['std. dev.'].tolist()).reshape((self.dim1, self.dim2)))
                                                if self.Add_error_bars_CB.isChecked():
                                                    mean = errors
                                                
                                                if self.yLog_CB.isChecked():
                                                    if np.count_nonzero(mean) == 0:
                                                        Norm = None
                                                        msg1 += 'Figure ' + str(i_fig) + ': ' + score + ' on ' + nuclide + '\n'
                                                    else:
                                                        Min = mean.min()
                                                        if Min == 0:
                                                            Min = 1E-12
                                                        Norm = colors.LogNorm(vmin=Min, vmax=mean.max())
                                                else:
                                                    Norm = None
                                                
                                                if self.Omit_Blank_Graph_CB.isChecked() and np.count_nonzero(mean) == 0:
                                                    msg2 += '\nFigure for ' + ': ' + score + ' on ' + nuclide + \
                                                                    str(BIN1) + str(Bins_For_Title1[i_bin1]).replace("'","") + UNIT1 + ' - ' + \
                                                                    str(BIN2) + str(Bins_For_Title2[i_bin2]).replace("'","") + UNIT2 + ' - ' + \
                                                                    str(BIN3) + str(Bins_For_Title3[i_bin3]).replace("'","") + UNIT3 + ' - ' + \
                                                                    str(BIN4) + str(Bins_For_Title4[i_bin4]).replace("'","") + UNIT4 + ' - ' + \
                                                                    str(BIN5) + str(Bins_For_Title5[i_bin5]).replace("'","") + UNIT5 + \
                                                            ' is empty and has been omitted.\n'
                                                    break
                                                else:
                                                    fig, ax = plt.subplots()
                                                    if self.mesh_type in ['RegularMesh', 'RectilinearMesh']:
                                                        im = self.Plot_Reg_Rect_Mesh(ax, mean, self.slice_volumes, Norm, Interpolation, Volume_normalization, Graph_Type, plot_basis)
                                                    elif self.mesh_type == 'CylindricalMesh':
                                                        if plot_basis == 'rphi':    
                                                            fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
                                                        im = self.Plot_CylindricalMesh(ax, mean, self.slice_volumes, Norm, Interpolation, Volume_normalization, Graph_Type, plot_basis)
                                                    fig.show()
                                                    
                                                if score == 'flux':
                                                    if self.Norm_to_Vol_CB.isChecked():
                                                        Suptitle1 = score + self.FlUX_UNIT.replace('-cm', ' / cm\u00b2')
                                                    else:
                                                        Suptitle1 = score + self.FlUX_UNIT
                                                else:
                                                    if score in self.REACTION_SCORES:
                                                        Suptitle1 = score + self.REACTION_UNIT 
                                                    elif score in self.MISCELLANEOUS_SCORES:
                                                        if score != 'events':
                                                            Suptitle1 = score + self.MISCELLANEOUS_UNIT[self.MISCELLANEOUS_SCORES.index(score)]
                                                        else:
                                                            Suptitle1 = self.MISCELLANEOUS_UNIT[self.MISCELLANEOUS_SCORES.index(score)]
                                                    elif score in self.ENERGY_SCORES:
                                                        Suptitle1 = score + self.ENERGY_SCORES_UNIT

                                                    if self.Norm_to_Vol_CB.isChecked():
                                                        Suptitle1 = Suptitle1 + ' / cm\u00b3'

                                                if self.Norm_to_Power_CB.isChecked() or self.Norm_to_SStrength_CB.isChecked():
                                                    if 's/cm' in Suptitle1:
                                                        Suptitle1 = Suptitle1.replace('s/cm', '1/cm')
                                                    else:
                                                        Suptitle1 = Suptitle1.replace('per source particle', ' /s')
                                                if self.Norm_to_BW_CB.isChecked():
                                                    if 'eV ' in Suptitle1:
                                                        Suptitle1 = Suptitle1.replace('eV ', '')
                                                    else:
                                                        Suptitle1 = Suptitle1 + ' / eV'
                                                elif self.Norm_to_UnitLethargy_CB.isChecked():
                                                    Suptitle1 = Suptitle1 + ' per unit lethargy'                      
                                                
                                                if self.Add_error_bars_CB.isChecked():
                                                    Suptitle1 = Suptitle1.replace(score, 'errors on ' + score)

                                                if len(Keys_Loop) == 0:
                                                    Suptitle3 = Suptitle2
                                                elif len(Keys_Loop) >= 1:
                                                    Suptitle3 = Suptitle2 + ' - ' + str(BIN1) + str(Bins_For_Title1[i_bin1]).replace("'","") + UNIT1
                                                    if len(Keys_Loop) >= 2:
                                                        Suptitle3 = Suptitle3 + '\n' + str(BIN2) + str(Bins_For_Title2[i_bin2]).replace("'","") + UNIT2
                                                        if len(Keys_Loop) >= 3:
                                                            Suptitle3 = Suptitle3 + ' - ' + str(BIN3) + str(Bins_For_Title3[i_bin3]).replace("'","") + UNIT3
                                                            if len(Keys_Loop) >= 4:
                                                                Suptitle3 = Suptitle3 + '\n' + str(BIN4) + str(Bins_For_Title4[i_bin4]).replace("'","") + UNIT4
                                                                if len(Keys_Loop) >= 5:
                                                                    Suptitle3 = Suptitle3 + ' - ' + str(BIN5) + str(Bins_For_Title5[i_bin5]).replace("'","") + UNIT5
                                                else:
                                                    self.showDialog('Warning', 'More than 6 filters not supported yet!')
                                                
                                                cbar = fig.colorbar(im, ax=ax, aspect=20, pad=0.06, shrink=0.8)  # Match the aspect ratio
                                                cbar.set_label(Suptitle1, rotation=270, labelpad=20)                                                

                                                # Format the colorbar labels in scientific notation
                                                formatter = ScalarFormatter(useMathText=True)  # Use scientific notation
                                                formatter.set_powerlimits((-2, 2))  # Show scientific notation for values outside the range 10^-2 to 10^2
                                                cbar.ax.yaxis.set_major_formatter(formatter)
                                                # Add the exponent notation to the colorbar
                                                cbar.ax.yaxis.offsetText.set_visible(True)  # Ensure the offset text (e.g., 1e-3) is visible

                                                if nuclide != 'total':
                                                    plt.title(Suptitle3 + '\nNuclide : ' + nuclide, fontsize=int(self.TitleFont_CB.currentText()))   #, horizontalalignment='center')
                                                else:    
                                                    plt.title(Suptitle3, fontsize=int(self.TitleFont_CB.currentText()))   #, horizontalalignment='center')

                                                cbar.ax.tick_params(labelsize=int(self.xFont_CB.currentText())*0.75)
                                                plt.xlabel(self.Curve_xLabel.text(), fontsize=int(self.xFont_CB.currentText()))
                                                plt.ylabel(self.Curve_yLabel.text(), fontsize=int(self.yFont_CB.currentText()))
                                                plt.xticks(fontsize=int(self.xFont_CB.currentText())*0.75, rotation=int(self.xLabelRot_CB.currentText()))
                                                plt.yticks(fontsize=int(self.yFont_CB.currentText())*0.75)  
                                                plt.tight_layout()
                                                #plt.subplots_adjust(left=0.131, right=0.939, top=0.962, bottom=0.048, hspace=0.2, wspace=0.2)
                                                i_fig += 1
        if msg1 != '':
            self.showDialog('Warning', msg + msg1)
        if msg2 != '':
            print(msg2)
            
    def Plot_CylindricalMesh(self, ax, mean, slice_volumes, Norm, Interpolation, Volume_normalization, Graph_Type, Plot_Basis):
        from scipy.interpolate import RectBivariateSpline
        # Get mesh grids
        theta = np.linspace(self.phi[0], self.phi[-1], len(self.phi) - 1)
        r = np.linspace(self.r[0], self.r[-1], len(self.r) - 1)        
        z = np.linspace(self.z[0], self.z[-1], len(self.z) - 1)        
        tally_data = mean.T.squeeze()
        if Plot_Basis == 'rphi':
            x_bins = np.array(r)  # Radial bins
            y_bins = np.array(theta)  # Angular bins (in radians)
            extent = [self.r[0], self.r[-1], self.phi[0], self.phi[-1],]
        elif Plot_Basis == 'rz':
            x_bins = np.array(r)  # Radial bins
            y_bins = np.array(z)
            extent = [self.r[0], self.r[-1], self.origin[2] + self.z[0],self.origin[2] + self.z[-1],]
        x_min, x_max, y_min, y_max = [i for i in extent]
        
        if len(tally_data.shape) == 1:
            data = tally_data[:].reshape(len(x_bins), len(y_bins))
            slice_volumes = slice_volumes[:].reshape(len(x_bins), len(y_bins))
        elif len(tally_data.shape) == 2:
            data = tally_data[:, :]
        else:
            raise NotImplementedError("Mesh is not 3d or 2d, can't plot")

        if Volume_normalization:
            tally_data = data / slice_volumes
        else:
            tally_data = data

        # reshaping data if column array is 1D
        if tally_data.shape[0] == 1:      # Shape (1, 9)
            Z = np.vstack([tally_data, tally_data]) # Shape becomes (2, 9)
            tally_data = Z
            x_bins = [x_min, x_max]
        # reshaping data if row array is 1D
        if tally_data.shape[1] == 1:      # Shape (9, 1)
            Z = np.hstack([tally_data, tally_data]) # Shape becomes (9, 2)
            tally_data = Z
            y_bins = [y_min, y_max]
        """if tally_data.shape[1] == 2 and Plot_Basis == 'rphi':
                y_bins = [y_min, (y_min + y_max) * 0.5, y_max]
                Z = np.hstack([tally_data, data]) # Shape becomes (9, 2)
                tally_data = Z"""
        
        # Generate fine mesh on the same grid for interpolation
        if Interpolation:
            if len(y_bins) < 3 or len(x_bins) < 3:
                self.showDialog('Warning', 'Not enough data to perform interpolation !')
                Interpolation = False
                y_mesh, x_mesh = np.meshgrid(y_bins, x_bins)
            else:
                spline = RectBivariateSpline(x_bins, y_bins, tally_data)
                # Create a spline interpolator
                x_fine = np.linspace(x_bins.min(), x_bins.max(), len(x_bins) * 2)
                y_fine = np.linspace(y_bins.min(), y_bins.max(), len(y_bins) * 2)
                # interpolate 
                tally_data = spline(x_fine, y_fine)
                y_mesh, x_mesh = np.meshgrid(y_fine, x_fine)
        else:
            y_mesh, x_mesh = np.meshgrid(y_bins, x_bins)
                            
        if Graph_Type == 'mesh plot': 
            if Plot_Basis == 'rz':
                im = ax.imshow(tally_data.T,  extent=extent, cmap=cm.rainbow)
            else: 
                if tally_data.shape[1] < 3:
                    self.showDialog('Warning', 'Plot could not be plotted properly due to few data along polar axis !\n Try contourf.')
                im = ax.pcolormesh(y_mesh, x_mesh, tally_data, norm=Norm, shading=Interpolation, cmap=cm.rainbow)
        elif Graph_Type == 'contourf':
            if Plot_Basis == 'rz':
                im = ax.contourf(x_mesh, y_mesh, tally_data, norm=Norm, shading=Interpolation, extent=extent, cmap=cm.rainbow)
            else:
                im = ax.contourf(y_mesh, x_mesh, tally_data, norm=Norm, shading=Interpolation, extent=extent, cmap=cm.rainbow) 
        elif Graph_Type == 'contour':
            if Plot_Basis == 'rz':
                im = ax.contour(x_mesh, y_mesh, tally_data, norm=Norm, cmap=cm.rainbow, extent=extent)
            else:
                im = ax.contour(y_mesh, x_mesh, tally_data, norm=Norm, cmap=cm.rainbow, extent=extent)

        return im

    def Plot_Reg_Rect_Mesh(self, ax, mean, slice_volumes, Norm, Interpolation, Volume_normalization, Graph_Type, Plot_basis):
        tally_data = mean.squeeze()
        #tally_data = mean.T.squeeze()
        if Plot_basis == 'xy':
            x = self.x
            y = self.y
        elif Plot_basis == 'xz':
            x = self.x
            y = self.z
        elif Plot_basis == 'yz':
            x = self.y
            y = self.z
        if tally_data.shape != (len(x), len(y)):
            tally_data = tally_data.T  # Transpose if dimensions are swapped
        if slice_volumes.shape != (len(x), len(y)):
            slice_volumes = slice_volumes.T  # Transpose if dimensions are swapped
        if len(tally_data.shape)  == 2:
            data = tally_data[:, :]
        else:
            raise NotImplementedError("Mesh is not 3d or 2d, can't plot")

        if Volume_normalization:
            tally_data = data / slice_volumes
        else:
            tally_data = data

        y_mesh, x_mesh = np.meshgrid(y, x)
        if Graph_Type == 'mesh plot':    
            im = ax.pcolormesh(x_mesh, y_mesh, tally_data, norm=Norm, shading=Interpolation, cmap=cm.rainbow)
        elif Graph_Type == 'contourf':
            im = ax.contourf(x_mesh, y_mesh, tally_data, norm=Norm, shading=Interpolation, cmap=cm.rainbow, extent=(0, 100, 0, 50))
        elif Graph_Type == 'contour':
            im = ax.contour(x_mesh, y_mesh, tally_data, cmap=cm.rainbow)

        return im

    def Plot_Mesh_Stack(self, dff, fig, ax):
        df = dff.copy()
        key = self.mesh_axis_key
        x = np.linspace(self.LL1, self.UR1, num=self.dim1 + 1)
        y = np.linspace(self.LL2, self.UR2, num=self.dim2 + 1)
        #
        Graph_Type = self.Graph_type_CB.currentText()

        if self.mesh_type == 'CylindricalMesh':
            if self.Mesh_xy_RB.isChecked():
                plot_basis = 'rphi'
            else:
                plot_basis = 'rz'
        elif self.mesh_type in ['RegularMesh', 'RectilinearMesh']:
            if self.Mesh_xy_RB.isChecked():
                plot_basis = 'xy'
            elif self.Mesh_xz_RB.isChecked():
                plot_basis = 'xz'
            elif self.Mesh_yz_RB.isChecked():
                plot_basis = 'yz'

        if self.xLog_CB.isChecked():                 # Interpolation to smooth data
            if self.mesh_type == 'RegularMesh':
                Interpolation = 'spline36'
            elif self.mesh_type == 'RectilinearMesh':
                Interpolation = 'gouraud'
            elif self.mesh_type == 'CylindricalMesh':
                Interpolation = 'gouraud'
        else:
            Interpolation = None

        if self.Norm_to_Vol_CB.isChecked():
            Volume_normalization = True
        else:
            Volume_normalization = False

        #
        Filter_Names = [filter for filter in self.Filter_names if filter != 'MeshFilter' ]
        Keys_Loop = [key[0] for key in self.df.keys()[:-4] if 'mesh' not in key[0] and 'high' not in key[0]]
        mesh_idx = self.Filter_names.index('MeshFilter')
        N_Bins = 1
        idx_s = []
        Key_BINS = [''] * len(Keys_Loop)
        key1 = ''; BIN1 = ''; UNIT1 = ''; Checked_bins1 = ['']; Bins_For_Title1 = ['']
        key2 = ''; BIN2 = ''; UNIT2 = ''; Checked_bins2 = ['']; Bins_For_Title2 = ['']
        key3 = ''; BIN3 = ''; UNIT3 = ''; Checked_bins3 = ['']; Bins_For_Title3 = ['']
        key4 = ''; BIN4 = ''; UNIT4 = ''; Checked_bins4 = ['']; Bins_For_Title4 = ['']
        key5 = ''; BIN5 = ''; UNIT5 = ''; Checked_bins5 = ['']; Bins_For_Title5 = ['']
        i = 0
        for key1 in Keys_Loop:
            filter_name = key1.split(' ')[0].capitalize() +'Filter'
            if 'from' in filter_name: filter_name = filter_name.replace('from', 'From')
            idx = self.Filter_names.index(filter_name)
            idx_s.append(idx)
            N_Bins = N_Bins * len(self.Key_Selected_Bins[idx])
            Key_BINS[i] = self.Key_Selected_Bins[idx]
            i += 1
        if len(Keys_Loop) >= 1:
            Checked_bins1 = Key_BINS[0]; key1 = Keys_Loop[0]; BIN1 = self.BIN[1]; UNIT1 = self.UNIT[1]; Bins_For_Title1 = self.Bins_For_Title[1]
            if len(Keys_Loop) >= 2:
                Checked_bins2 = Key_BINS[1]; key2 = Keys_Loop[1]; BIN2 = self.BIN[2]; UNIT2 = self.UNIT[2]; Bins_For_Title2 = self.Bins_For_Title[2]
                if len(Keys_Loop) >= 3:
                    Checked_bins3 = Key_BINS[2]; key3 = Keys_Loop[2]; BIN3 = self.BIN[3]; UNIT3 = self.UNIT[3]; Bins_For_Title3 = self.Bins_For_Title[3]
                    if len(Keys_Loop) >= 4:
                        Checked_bins4 = Key_BINS[3]; key4 = Keys_Loop[3]; BIN4 = self.BIN[4]; UNIT4 = self.UNIT[4]; Bins_For_Title4 = self.Bins_For_Title[4]
                        if len(Keys_Loop) >= 5:
                            Checked_bins5 = Key_BINS[4]; key5 = Keys_Loop[4]; BIN5 = self.BIN[5]; UNIT5 = self.UNIT[5]; Bins_For_Title5 = self.Bins_For_Title[5] 

        N_Figs = len(self.selected_scores) * len(self.selected_nuclides) * len(self.checked_bins_indices) * N_Bins
        if self.N_Fig > 20 and not self.Omit_Blank_Graph_CB.isChecked():
            qm = QMessageBox
            ret = qm.question(self, 'Warning',' More than 20 figures (' + str(N_Figs) + ') have been opened! \n This may consume too much memory.'+
                                '\n continue ploting ?', qm.Yes | qm.No)
            if ret == qm.Yes:
                pass 
            elif ret == qm.No:
                self.WillPlot = False
                return
        msg = 'Cannot plot in Log scale scores that are all null!\n'
        msg1 = ''
        msg2 = ''
        i_fig = 1
        self.i_omitted = 0

        for score in self.selected_scores:
            if score != '':
                for nuclide in self.selected_nuclides:
                    if nuclide != '':
                        for bin in self.checked_bins_indices:
                            Suptitle2 = 'score at '                            
                            if len(self.tally.filters[mesh_idx].mesh._grids) == 3:
                                Suptitle2 = Suptitle2 + str(self.Tallies[self.tally_id][self.filter_ids[mesh_idx]]['bins'][bin-2]).replace('slice at', '')
                            else:
                                if self.Mesh_xy_RB.isChecked():
                                    Suptitle2 = Suptitle2.replace('at ', '') + ' integrated on z axis'
                                elif self.Mesh_xz_RB.isChecked():
                                    if self.mesh_type == 'CylindricalMesh':
                                        Suptitle2 = Suptitle2.replace('at ', '') + ' integrated on \u03F4 axis'
                                    else:
                                        Suptitle2 = Suptitle2.replace('at ', '') + ' integrated on y axis'
                                elif self.Mesh_yz_RB.isChecked():
                                    Suptitle2 = Suptitle2.replace('at ', '') + ' integrated on x axis'
                            if self.Add_error_bars_CB.isChecked():
                                Suptitle2 = Suptitle2.replace('score', 'errors on score')
                            for bin1 in Checked_bins1: 
                                i_bin1 = Checked_bins1.index(bin1)
                                for bin2 in Checked_bins2: 
                                    i_bin2 = Checked_bins2.index(bin2)
                                    for bin3 in Checked_bins3: 
                                        i_bin3 = Checked_bins3.index(bin3)
                                        for bin4 in Checked_bins4: 
                                            i_bin4 = Checked_bins4.index(bin4)
                                            for bin5 in Checked_bins5: 
                                                i_bin5 = Checked_bins5.index(bin5)
                                                #yy = df[df.nuclide == nuclide][df.score == score][df[key] == bin - 1]
                                                yy = df[df.nuclide == nuclide]
                                                yy = yy[yy.score == score]
                                                yy = yy[yy[key] == bin - 1]
                                                if len(Keys_Loop) >= 1:
                                                    yy = yy[df[key1] == bin1]
                                                    if len(Keys_Loop) >= 2:
                                                        yy = yy[df[key2] == bin2]
                                                        if len(Keys_Loop) >= 3:
                                                            yy = yy[df[key3] == bin3]
                                                            if len(Keys_Loop) >= 4:
                                                                yy = yy[df[key4] == bin4]
                                                                if len(Keys_Loop) >= 5:
                                                                    yy = yy[df[key5] == bin5]
                                                self.Print_Formated_df(yy.copy(), self.tally_id, self.editor)
                                                if len(yy) != 0:    
                                                    mean = np.transpose(np.array(yy['mean'].tolist()).reshape((self.dim1, self.dim2)))
                                                    errors = np.transpose(np.array(yy['std. dev.'].tolist()).reshape((self.dim1, self.dim2)))
                                                else:
                                                    mean = None

                                                if self.Add_error_bars_CB.isChecked():
                                                    mean = errors
                                                
                                                if self.yLog_CB.isChecked():
                                                    if np.count_nonzero(mean) == 0:
                                                        Norm = None
                                                        msg1 += 'Figure ' + str(i_fig) + ': ' + score + ' on ' + nuclide + '\n'
                                                    else:
                                                        Min = mean.min()
                                                        if Min == 0:
                                                            Min = 1E-12
                                                        Norm = colors.LogNorm(vmin=Min, vmax=mean.max())
                                                else:
                                                    Norm = None

                                                if self.Omit_Blank_Graph_CB.isChecked() and np.count_nonzero(mean) == 0:
                                                    msg2 += '\nFigure for ' + ': ' + score + ' on ' + nuclide + \
                                                                    str(BIN1) + str(Bins_For_Title1[i_bin1]).replace("'","") + UNIT1 + ' - ' + \
                                                                    str(BIN2) + str(Bins_For_Title2[i_bin2]).replace("'","") + UNIT2 + ' - ' + \
                                                                    str(BIN3) + str(Bins_For_Title3[i_bin3]).replace("'","") + UNIT3 + ' - ' + \
                                                                    str(BIN4) + str(Bins_For_Title4[i_bin4]).replace("'","") + UNIT4 + ' - ' + \
                                                                    str(BIN5) + str(Bins_For_Title5[i_bin5]).replace("'","") + UNIT5 + \
                                                            ' has been omitted.\n'
                                                    self.i_omitted += 1
                                                    break
                                                else:
                                                    i = i_fig - 1
                                                    if i < self.row_SB.value() * self.col_SB.value():
                                                        if self.mesh_type in ['RegularMesh', 'RectilinearMesh']:
                                                            im = self.Plot_Reg_Rect_Mesh(ax[i], mean, self.slice_volumes, Norm, Interpolation, Volume_normalization, Graph_Type, plot_basis)
                                                        elif self.mesh_type == 'CylindricalMesh':
                                                            im = self.Plot_CylindricalMesh(ax[i], mean, self.slice_volumes, Norm, Interpolation, Volume_normalization, Graph_Type, plot_basis)
                                                    else:
                                                        break

                                                    if score == 'flux':
                                                        if self.Norm_to_Vol_CB.isChecked():
                                                            Suptitle1 = score + ' particle / cm\u00b2 per source particle'
                                                        else:
                                                            Suptitle1 = score + ' particle-cm per source particle'
                                                    else:
                                                        if self.Norm_to_Vol_CB.isChecked():
                                                            Suptitle1 = score + ' rate per source particle' 
                                                        else:
                                                            Suptitle1 = score + ' rate ' + ' cm\u00b3 per source particle'
                                                    if self.Norm_to_Power_CB.isChecked() or self.Norm_to_SStrength_CB.isChecked():
                                                        Suptitle1 = Suptitle1.replace('per source particle', ' /s')
                                                    if self.Norm_to_BW_CB.isChecked():
                                                        Suptitle1 = Suptitle1 + ' /eV'
                                                    elif self.Norm_to_UnitLethargy_CB.isChecked():
                                                        Suptitle1 = Suptitle1 + ' per unit lethargy'                      
                                                    
                                                    if self.Add_error_bars_CB.isChecked():
                                                        Suptitle1 = Suptitle1.replace(score, 'errors on ' + score)

                                                    if len(Keys_Loop) == 0:
                                                        Suptitle3 = Suptitle2
                                                    elif len(Keys_Loop) >= 1:
                                                        Suptitle3 = Suptitle2 + '\n' + str(BIN1) + str(Bins_For_Title1[i_bin1]).replace("'","") + UNIT1
                                                        if len(Keys_Loop) >= 2:
                                                            Suptitle3 = Suptitle3 + ' - ' + str(BIN2) + str(Bins_For_Title2[i_bin2]).replace("'","") + UNIT2
                                                            if len(Keys_Loop) >= 3:
                                                                Suptitle3 = Suptitle3 + '\n' + str(BIN3) + str(Bins_For_Title3[i_bin3]).replace("'","") + UNIT3
                                                                if len(Keys_Loop) >= 4:
                                                                    Suptitle3 = Suptitle3 + ' - ' + str(BIN4) + str(Bins_For_Title4[i_bin4]).replace("'","") + UNIT4
                                                                    if len(Keys_Loop) >= 5:
                                                                        Suptitle3 = Suptitle3 + '\n' + str(BIN5) + str(Bins_For_Title5[i_bin5]).replace("'","") + UNIT5
                                                    else:
                                                        self.showDialog('Warning', 'More than 6 filters not supported yet!')

                                                    if nuclide != 'total':
                                                        ax[i].set_title(Suptitle3 + '\nNuclide : ' + nuclide, fontsize=int(self.TitleFont_CB.currentText()))   #, horizontalalignment='center')
                                                    else:    
                                                        ax[i].set_title(Suptitle3, fontsize=int(self.TitleFont_CB.currentText()))   #, horizontalalignment='center')

                                                    ax[i].set_xlabel(self.Curve_xLabel.text(), fontsize=int(self.xFont_CB.currentText()))
                                                    ax[i].set_ylabel(self.Curve_yLabel.text(), fontsize=int(self.yFont_CB.currentText()))

                                                    if i < self.row_SB.value() * self.col_SB.value():
                                                        cbar = fig.colorbar(im, ax=ax[i], aspect=20, pad=0.06, shrink=0.8)  # Match the aspect ratio
                                                        cbar.set_label(Suptitle1, rotation=270, labelpad=20)                                                
                                                        formatter = ScalarFormatter(useMathText=True)  # Use scientific notation
                                                        formatter.set_powerlimits((-2, 2))  # Show scientific notation for values outside the range 10^-2 to 10^2
                                                        cbar.ax.yaxis.set_major_formatter(formatter)

                                                        # Add the exponent notation to the colorbar
                                                        cbar.ax.yaxis.offsetText.set_visible(True)  # Ensure the offset text (e.g., 1e-3) is visible
                                    
                                                    i_fig += 1

        if msg1 != '':
            self.showDialog('Warning', msg + msg1)
        if msg2 != '':
            print(msg2)

    def Check_For_Empty_Scores(self, dff):
        df = dff.copy()
        
        key = self.mesh_axis_key
        x = np.linspace(self.LL1, self.UR1, num=self.dim1 + 1)
        y = np.linspace(self.LL2, self.UR2, num=self.dim2 + 1)
        Keys_Loop = [key[0] for key in self.df.keys()[:-4] if 'mesh' not in key[0] and 'high' not in key[0]]
        mesh_idx = self.Filter_names.index('MeshFilter')
        Key_BINS = [''] * len(Keys_Loop)
        key1 = ''; BIN1 = ''; UNIT1 = ''; Checked_bins1 = ['']; Bins_For_Title1 = ['']
        key2 = ''; BIN2 = ''; UNIT2 = ''; Checked_bins2 = ['']; Bins_For_Title2 = ['']
        key3 = ''; BIN3 = ''; UNIT3 = ''; Checked_bins3 = ['']; Bins_For_Title3 = ['']
        key4 = ''; BIN4 = ''; UNIT4 = ''; Checked_bins4 = ['']; Bins_For_Title4 = ['']
        key5 = ''; BIN5 = ''; UNIT5 = ''; Checked_bins5 = ['']; Bins_For_Title5 = ['']
        i = 0
        for key1 in Keys_Loop:
            filter_name = key1.split(' ')[0].capitalize() +'Filter'
            if 'from' in filter_name: filter_name = filter_name.replace('from', 'From')
            idx = self.Filter_names.index(filter_name)
            Key_BINS[i] = self.Key_Selected_Bins[idx]
            i += 1
        if len(Keys_Loop) >= 1:
            Checked_bins1 = Key_BINS[0]; key1 = Keys_Loop[0]; BIN1 = self.BIN[1]; UNIT1 = self.UNIT[1]; Bins_For_Title1 = self.Bins_For_Title[1]
            if len(Keys_Loop) >= 2:
                Checked_bins2 = Key_BINS[1]; key2 = Keys_Loop[1]; BIN2 = self.BIN[2]; UNIT2 = self.UNIT[2]; Bins_For_Title2 = self.Bins_For_Title[2]
                if len(Keys_Loop) >= 3:
                    Checked_bins3 = Key_BINS[2]; key3 = Keys_Loop[2]; BIN3 = self.BIN[3]; UNIT3 = self.UNIT[3]; Bins_For_Title3 = self.Bins_For_Title[3]
                    if len(Keys_Loop) >= 4:
                        Checked_bins4 = Key_BINS[3]; key4 = Keys_Loop[3]; BIN4 = self.BIN[4]; UNIT4 = self.UNIT[4]; Bins_For_Title4 = self.Bins_For_Title[4]
                        if len(Keys_Loop) >= 5:
                            Checked_bins5 = Key_BINS[4]; key5 = Keys_Loop[4]; BIN5 = self.BIN[5]; UNIT5 = self.UNIT[5]; Bins_For_Title5 = self.Bins_For_Title[5] 

        for score in self.selected_scores:
            if score != '':
                for nuclide in self.selected_nuclides:
                    if nuclide != '':
                        for bin in self.checked_bins_indices:
                            for bin1 in Checked_bins1: 
                                i_bin1 = Checked_bins1.index(bin1)
                                for bin2 in Checked_bins2: 
                                    i_bin2 = Checked_bins2.index(bin2)
                                    for bin3 in Checked_bins3: 
                                        i_bin3 = Checked_bins3.index(bin3)
                                        for bin4 in Checked_bins4: 
                                            i_bin4 = Checked_bins4.index(bin4)
                                            for bin5 in Checked_bins5:
                                                i_bin5 = Checked_bins5.index(bin5)
                                                #yy = df[df.nuclide == nuclide][df.score == score][df[key] == bin - 1][df[key1] == bin1]
                                                yy = df[df.nuclide == nuclide]
                                                yy = yy[yy.score == score]
                                                yy = yy[yy[key] == bin - 1]
                                                yy = yy[yy[key1] == bin1]
                                                if len(Keys_Loop) >= 2:
                                                    yy = yy[df[key2] == bin2]
                                                    if len(Keys_Loop) >= 3:
                                                        yy = yy[df[key3] == bin3]
                                                        if len(Keys_Loop) >= 4:
                                                            yy = yy[df[key4] == bin4]
                                                            if len(Keys_Loop) >= 5:
                                                                yy = yy[df[key5] == bin5]
                                                mean = np.array(yy['mean'].tolist())   #.reshape((self.dim1, self.dim2))
                                                errors = np.array(yy['std. dev.'].tolist())  #.reshape((self.dim1, self.dim2))
                                                
                                                if self.Omit_Blank_Graph_CB.isChecked() and np.count_nonzero(mean) == 0:
                                                    self.N_Fig -= 1
                                                    break

    def Plot_Distribcell(self):       # needs more developemnt
        # Distributed Cell Tally Visualization
        # This example demonstrates how a tally with a DistribcellFilter can be plotted using the openmc.lib module 
        # to determine geometry information. First, we'll begin by creating a simple model with a hexagonal lattice.
        # Jupiter example from https://nbviewer.org/gist/paulromano/f2fbf3d4731e324b6f5ab31ef3fcaa26
        #
        # ***********************************
        self.showDialog('Warning', 'Under development!')
        return
        # ***********************************
        import openmc.lib
        cwd = os.getcwd()
        resolution = (6000, 6000)
        img = np.full(resolution, np.nan)
        xmin, xmax = -30., 30.
        ymin, ymax = -30., 30.
        idx = self.filter_ids.index(self.filter_id)
        key = self.Tallies[self.tally_id]['filter_types'][idx]
        x = np.linspace(xmin, xmax, num=119)
        y = np.linspace(ymin, ymax, num=119)
        df = self.df.loc[(self.df['score'].isin(self.selected_scores)) & (self.df['nuclide'].isin(self.selected_nuclides))]
        df = df.loc[self.df[self.Keys[idx]].isin(self.Key_Selected_Bins[idx])].copy()
        '''for score in self.selected_scores:
            if score != '':
                for nuclide in self.selected_nuclides:
                    if nuclide != '':
                        mean = df[df.score == score][df.nuclide == nuclide]'''
        plt.subplots()
        mean = df
        #os.chdir(os.path.dirname(self.sp_file))
        if True: #with openmc.lib.run_in_memory():
            for row, y in enumerate(np.linspace(ymin, ymax, resolution[0])):
                for col, x in enumerate(np.linspace(xmin, xmax, resolution[1])):
                    try:
                        pass
                        # For each (x, y, z) point, determine the cell and distribcell index
                        cell, distribcell_index = openmc.lib.find_cell((x, y, 0.))
                    except openmc.exceptions.GeometryError:
                        # If a point appears outside the geometry, you'll get a GeometryError exception.
                        # These lines catch the exception and continue on
                        continue
                    if cell.id == self.tally.filters[idx].bins[0]:  # fuel_cell.id:
                        # When the cell ID matches, we set the corresponding pixel in the image using the
                        # distribcell index. Note that we're taking advantage of the fact that the i-th element
                        # in the flux array corresponds to the i-th distribcell instance.
                        return
                        img[row, col] = mean[distribcell_index]
        options = {
                    'origin': 'lower',
                    'extent': (xmin, xmax, ymin, ymax),
                    'vmin': 0.03,
                    'vmax': 0.06,
                    'cmap': 'RdYlBu_r',
                }
        plt.imshow(img, **options)
        plt.xlabel('x [cm]')
        plt.ylabel('y [cm]')
        plt.colorbar()

        plt.xlabel(self.Curve_xLabel.text(), fontsize=int(self.xFont_CB.currentText()))
        plt.ylabel(self.Curve_yLabel.text(), fontsize=int(self.yFont_CB.currentText()))
        plt.xticks(fontsize=int(self.xFont_CB.currentText())*0.75, rotation=int(self.xLabelRot_CB.currentText()))
        plt.yticks(fontsize=int(self.yFont_CB.currentText())*0.75)
        plt.colorbar().ax.tick_params(labelsize=int(self.xFont_CB.currentText())*0.75)
        plt.tight_layout()
        plt.show()
        #os.chdir(cwd)

    def box_plot(self):
        print('Ploted Scores : \n', self.df.to_string())
        key = self.Plot_by_CB.currentText()
        print('selected key : ', key)
        if key != 'score':
            #if key == 'nuclide':
            for score in self.selected_scores:
                bp = self.df[self.df.score == score].boxplot(column='mean', by=key)
                plt.show()
                if score not in ['flux', 'current']:    
                    plt.title(score + ' RR')
                else:    
                    plt.title(score)
        else:
            if 'cell' in self.df.keys():
                bp = self.df.boxplot(column='mean', by=key)
                plt.show()
                for cell in self.Checked_cells:
                    bp = self.df[self.df.cell == cell].boxplot(column='mean', by=key)
                    plt.show()
                    plt.title('RR in cell ' + str(cell))
            else:
                bp = self.df.boxplot(column='mean', by=key)
                plt.show()
                plt.title('RR ')

    def Reset_Plot_Settings(self):
        self.TitleFont_CB.setCurrentIndex(7)
        self.xFont_CB.setCurrentIndex(6)
        self.yFont_CB.setCurrentIndex(6)        
        self.xLabelRot_CB.setCurrentIndex(0)
        self.Legende_CB.setCurrentIndex(6)
        self.Graph_Layout_CB.setCurrentIndex(0)
        self.Graph_type_CB.setCurrentIndex(0)
        self.Plot_by_CB.setCurrentIndex(0)
        self.Curve_title.clear()
        self.Curve_xLabel.clear()
        self.Curve_yLabel.clear()
        self.Curve_y2Label.clear()
        for CB in [self.xLog_CB, self.yLog_CB, self.Add_error_bars_CB, self.xGrid_CB, self.yGrid_CB, self.MinorGrid_CB]:
            CB.setChecked(False)
        for CB in [self.xLog_CB, self.yLog_CB, self.Add_error_bars_CB, self.xGrid_CB, self.yGrid_CB, self.MinorGrid_CB, self.label_2, self.label_3]:
            CB.setEnabled(True)
        if 'Keff' in self.Tally_id_comboBox.currentText():
            self.Add_error_bars_CB.setEnabled(False)

    def normalOutputWritten(self,text):
        if self.tabWidget.currentIndex() == 0:
            self.cursor = self.editor.textCursor()
            self.cursor.insertText(text)
            self.editor.setTextCursor(self.cursor)
        elif self.tabWidget.currentIndex() == 1:
            self.cursor = self.editor2.textCursor()
            self.cursor.insertText(text)
            self.editor2.setTextCursor(self.cursor)

    def broadning_pulse_height(self):
        # ref. : https://github.com/openmc-dev/openmc-notebooks/blob/main/gamma-detector.ipynb
        try:
            sp = openmc.StatePoint(self.sp_file)
            tally = sp.get_tally(id=tally_id)
            pulse_height_values = tally.get_values(scores=['pulse-height']).flatten()
            # we want to display the pulse-height value in the center of the bin
            energy_bins = self.Checked_energies
            energy_bin_centers = energy_bins[1:] + 0.5 * (energy_bins[1] - energy_bins[0])
            plt.figure()
            plt.semilogy(energy_bin_centers, pulse_height_values)

            # plot the strongest sources as vertical lines
            plt.axvline(x=800_000, color="red", ls=":")     # source_1
            plt.axvline(x=661_700, color="red", ls=":")     # source_2

            plt.xlabel('Energy [eV]')
            plt.ylabel('Counts')
            plt.title('Pulse Height Values')
            plt.grid(True)
            plt.tight_layout()

            a, b, c = 1000, 4, 0.0002
            number_broadening_samples = 1e6
            samples = np.random.choice(energy_bin_centers[1:], size=int(number_broadening_samples), p=pulse_height_values[1:]/np.sum(pulse_height_values[1:]))
            broaded_pulse_height_values = gauss(samples)

            broaded_spectrum, _ = np.histogram(broaded_pulse_height_values, bins=energy_bins)
            renormalized_broaded_spectrum = broaded_spectrum / np.sum(broaded_spectrum) * np.sum(pulse_height_values[1:])

            plt.figure()

            plt.semilogy(energy_bin_centers[1:], pulse_height_values[1:], label="original simulation result")
            plt.semilogy(energy_bin_centers[1:], renormalized_broaded_spectrum[1:], label="broaded detector response")

            # plot the strongest sources as vertical lines
            plt.axvline(x=800_000, color="red", ls=":", label="gamma source")     # source_1
            plt.axvline(x=661_700, color="red", ls=":")                           # source_2

            plt.legend()
            plt.xlabel('Energy [eV]')
            plt.ylabel('Counts')
            plt.title('Pulse Height Values')
            plt.grid(True)
            plt.tight_layout()
        except:
            return

    def gauss(self, E, a, b, c):
        sigma = (a + b * (E + c * E**2)**0.5) / (2 * (2 * np.log(2))**0.5)
        return np.random.normal(loc=E, scale=sigma)

    #############################################################################
    #                        Editor methods and buttons
    #############################################################################

    def Define_Buttons(self):
        #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        #++++++++++++++++++++++++++++++++++ D E F I N E B U T T O N S ++++++++++++++++++++++++++++++++++++++++
        #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        ### begin toolbar
        tb = self.addToolBar("File")
        tb.setContextMenuPolicy(Qt.PreventContextMenu)
        tb.setIconSize(QSize(QSize(24, 24)))
        tb.setMovable(False)
        tb.setAllowedAreas(Qt.AllToolBarAreas)
        tb.setFloatable(False)
        ### file buttons
        self.newAct = QAction(QIcon("src/icons/new24.png"), "&New", self, shortcut=QKeySequence.New,
                statusTip="new file", triggered=self.newFile)
        tb.addAction(self.newAct)

        self.openAct = QAction(QIcon("src/icons/open24.png"), "&Open", self, shortcut=QKeySequence.Open,
                statusTip="open file", triggered=self.openFile)
        tb.addAction(self.openAct)

        self.saveAct = QAction(QIcon("src/icons/document-save.png"), "&Save", self, shortcut=QKeySequence.Save,
                statusTip="save file", triggered=self.fileSave)
        tb.addAction(self.saveAct)

        self.saveAsAct = QAction(QIcon("src/icons/document-save-as.png"), "&Save as ...", self, shortcut=QKeySequence.SaveAs,
                statusTip="save file as ...", triggered=self.fileSaveAs)
        tb.addAction(self.saveAsAct)
        
        self.pdfAct = QAction(QIcon("src/icons/pdf.png"), "export PDF", self, shortcut="Ctrl+Shift+p",
                statusTip="save file as PDF", triggered=self.exportPDF)
        tb.addAction(self.pdfAct)
        self.Landscape_CB = QtWidgets.QCheckBox(self, text="Landscape", checkable=True)
        tb.addWidget(self.Landscape_CB)
        #tb.addAction(QAction("Landscape", self, checkable=True))

        ### color chooser
        tb.addSeparator()
        tb.addAction(QIcon('src/icons/color.png'), "change Color", self.changeColor)
        tb.addSeparator()
        tb.addAction(QIcon("src/icons/eraser.png"), "clear Output Label", self.clearLabel)
        tb.addSeparator()
        
        ### print preview
        self.printPreviewAct = QAction(QIcon("src/icons/document-print-preview.png"), "Print Preview", self, shortcut="Ctrl+Shift+P",
                statusTip="Preview Document", triggered=self.handlePrintPreview)
        tb.addAction(self.printPreviewAct)
        ### print
        self.printAct = QAction(QIcon("src/icons/document-print.png"), "Print", self, shortcut=QKeySequence.Print,
                statusTip="Print Document", triggered=self.handlePrint)
        tb.addAction(self.printAct) 

        tb.addSeparator()
        self.comboSize = QComboBox(tb)
        tb.addSeparator()
        self.comboSize.setObjectName("comboSize")
        tb.addWidget(self.comboSize)
        self.comboSize.setEditable(True)

        db = QFontDatabase()
        for size in db.standardSizes():
            self.comboSize.addItem("%s" % (size))
        self.comboSize.addItem("%s" % (90))
        self.comboSize.addItem("%s" % (100))
        self.comboSize.addItem("%s" % (160))
        self.comboSize.activated[str].connect(self.textSize)
        self.comboSize.setCurrentIndex(
                self.comboSize.findText(
                        "%s" % (QApplication.font().pointSize()))) 
        tb.addSeparator()
        self.bgAct = QAction(QIcon("src/icons/sbg_color.png"), "change Background Color",self, triggered=self.changeBGColor)
        self.bgAct.setStatusTip("change Background Color")
        tb.addSeparator()
        tb.addAction(self.bgAct)
        tb.addSeparator()

        # checkBox for highlighting
        self.checkbox = QCheckBox('Highlighting', self)
        tb.addWidget(self.checkbox)
        self.checkbox.stateChanged.connect(self.HLAct)

        ### find / replace toolbar
        #self.addToolBarBreak()
        tbf = self.addToolBar("Find")
        tbf.setContextMenuPolicy(Qt.PreventContextMenu)
        tbf.setMovable(False)
        tbf.setIconSize(QSize(iconsize))
        self.findfield = QLineEdit()
        self.findfield.addAction(QIcon("icons/edit-find.png"), QLineEdit.LeadingPosition)
        self.findfield.setClearButtonEnabled(True)
        self.findfield.setFixedWidth(150)
        self.findfield.setPlaceholderText("find")
        self.findfield.setToolTip("press RETURN to find")
        self.findfield.setText("")
        ft = self.findfield.text()
        self.findfield.returnPressed.connect(self.findText)
        tbf.addWidget(self.findfield)
        tbf.addSeparator()
        self.gotofield = QLineEdit()
        self.gotofield.addAction(QIcon("src/icons/go-next.png"), QLineEdit.LeadingPosition)
        self.gotofield.setClearButtonEnabled(True)
        self.gotofield.setFixedWidth(120)
        self.gotofield.setPlaceholderText("go to line")
        self.gotofield.setToolTip("press RETURN to go to line")
        self.gotofield.returnPressed.connect(self.gotoLine)
        tbf.addWidget(self.gotofield)
        tbf.addSeparator()
        tb.addWidget(tbf)
        ## addStretch
        empty = QWidget();
        empty.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Preferred);
        tb.addWidget(empty)
        self.exitAct = QAction(QIcon("src/icons/quit.png"), "exit", self, shortcut=QKeySequence.Quit,
                statusTip="Exit", triggered=self.Close)
        tb.addAction(self.exitAct)

        self.filemenu=self.menuFile 
        self.separatorAct = self.filemenu.addSeparator()
        self.filemenu.addAction(self.newAct)
        self.filemenu.addAction(self.openAct)
        self.filemenu.addAction(self.saveAct)
        self.filemenu.addAction(self.saveAsAct)
        self.filemenu.addSeparator()
        self.filemenu.addAction(self.pdfAct)
        self.filemenu.addSeparator()
        """for i in range(self.MaxRecentFiles):
            self.filemenu.addAction(self.recentFileActs[i])"""
        self.updateRecentFileActions()
        self.filemenu.addSeparator()

        self.clearRecentAct = QAction(QIcon("src/icons/close.png"), "clear Recent Files List", self, triggered=self.clearRecentFiles)
        self.filemenu.addAction(self.clearRecentAct)
        self.filemenu.addSeparator()

        editmenu = self.menuEdit
        editmenu.addAction(QAction(QIcon('src/icons/undo.png'), "Undo", self, triggered = self.editor.undo, shortcut = "Ctrl+u"))
        editmenu.addAction(QAction(QIcon('src/icons/redo.png'), "Redo", self, triggered = self.editor.redo, shortcut = "Shift+Ctrl+u"))
        editmenu.addSeparator()
        editmenu.addAction(QAction(QIcon('src/icons/copy.png'), "Copy", self, triggered = self.editor.copy, shortcut = "Ctrl+c"))
        editmenu.addAction(QAction(QIcon('src/icons/cut.png'), "Cut", self, triggered = self.editor.cut, shortcut = "Ctrl+x"))
        editmenu.addAction(QAction(QIcon('src/icons/paste.png'), "Paste", self, triggered = self.editor.paste, shortcut = "Ctrl+v"))
        editmenu.addAction(QAction(QIcon('src/icons/delete.png'), "Delete", self, triggered = self.editor.cut, shortcut = "Del"))
        editmenu.addSeparator()
        editmenu.addAction(QAction(QIcon('src/icons/select-all.png'), "Select All", self, triggered = self.editor.selectAll, shortcut = "Ctrl+a"))
        editmenu.addSeparator()

        for CB in [self.TitleFont_CB, self.xFont_CB, self.yFont_CB, self.Legende_CB]:
            CB.setEditable(True)
            db = QFontDatabase()
            for size in db.standardSizes():
                CB.addItem("%s" % (size))
            CB.addItem("%s" % (90))
            CB.addItem("%s" % (100))
            CB.addItem("%s" % (160))
        
        self.xLabelRot_CB.addItems(['0', '5', '15', '25', '30', '45', '60', '75', '90'])
        self.Reset_Plot_Settings()
        #self.readSettings()
        #self.lineLabel1.setText("self.root is: " + str(self.sp_file), 0)

        # Status bar
        self.lineLabel1 = QLabel()
        self.lineLabel2 = QLabel()
        self.lineLabel3 = QLabel()
        self.lineLabel2.setAlignment(QtCore.Qt.AlignCenter)
        self.lineLabel3.setAlignment(QtCore.Qt.AlignCenter)
        widget = QWidget(self)
        widget.setLayout(QHBoxLayout())
        widget.layout().addWidget(self.lineLabel1)
        widget.layout().addWidget(VLine())
        widget.layout().addWidget(self.lineLabel2)
        widget.layout().addWidget(VLine())
        widget.layout().addWidget(self.lineLabel3)
        self.statusBar.addWidget(widget, 1)

        # Add shortcut to buttons
        self.browse_PB.setShortcut("Ctrl+b")

    def Close(self):
        import matplotlib.pyplot as plt

        box = QMessageBox()
        box.setIcon(QMessageBox.Question)
        box.setWindowTitle('Close gui!')
        box.setText("<h4><p>Many opened figures will be closed.</p>\n" \
                        "<p>Choose action</p></h4>")
        box.setStandardButtons(QMessageBox.Yes| QMessageBox.Discard | QMessageBox.No)
        #box.setStandardButtons(QMessageBox.Yes| QMessageBox.Discard | QMessageBox.No | QMessageBox.Cancel)
        buttonY = box.button(QMessageBox.Yes)
        buttonY.setText('keep all')
        buttonD = box.button(QMessageBox.Discard)
        buttonD.setText('close figures only')
        buttonN = box.button(QMessageBox.No)
        buttonN.setText('Close all')        
        
        box.exec_()

        if box.clickedButton() == buttonY:
            return 
        elif box.clickedButton() == buttonD:
            plt.close('all')
                    
        elif box.clickedButton() == buttonN:
            plt.close('all')
            self.close()

    def HLAct(self):
        if self.tabWidget_2.currentIndex() == 0:
            editor = self.editor
        elif self.tabWidget_2.currentIndex() == 1:
            editor = self.editor1
        elif self.tabWidget_2.currentIndex() == 2:
            editor = self.editor2
        if self.checkbox.isChecked():
            from src.syntax_py import Highlighter
            self.highlighter = Highlighter(editor.document())
        else:
            from src.syntax import Highlighter
            self.highlighter = Highlighter(editor.document())

    """def getLineNumber(self):
        if self.tabWidget_2.currentIndex() == 0:
            editor = self.editor
        elif self.tabWidget_2.currentIndex() == 1:
            editor = self.editor1
        editor.moveCursor(self.editor.cursor.StartOfLine)
        linenumber = self.editor.textCursor().blockNumber() + 1
        return linenumber"""

    def goToLine(self, ft):
        if self.tabWidget_2.currentIndex() == 0:
            editor = self.editor
        elif self.tabWidget_2.currentIndex() == 1:
            editor = self.editor1
        elif self.tabWidget_2.currentIndex() == 2:
            editor = self.editor2
        editor.moveCursor(int(self.gofield.currentText()),
                                QTextCursor.MoveAnchor) ### not working

    def findText(self):
        if self.tabWidget_2.currentIndex() == 0:
            editor = self.editor
        elif self.tabWidget_2.currentIndex() == 1:
            editor = self.editor1
        elif self.tabWidget_2.currentIndex() == 2:
            editor = self.editor2
        word = self.findfield.text()
        if editor.find(word):
            linenumber = editor.textCursor().blockNumber() + 1
            self.lineLabel1.setText("found <b>'" + self.findfield.text() + "'</b> at Line: " + str(linenumber))
            editor.centerCursor()
        else:
            self.lineLabel1.setText("<b>'" + self.findfield.text() + "'</b> not found")
            editor.moveCursor(QTextCursor.Start)
            if editor.find(word):
                linenumber = editor.textCursor().blockNumber() + 1
                self.lineLabel1.setText("found <b>'" + self.findfield.text() + "'</b> at Line: " + str(linenumber))
                editor.centerCursor()

    def gotoLine(self):
        if self.tabWidget_2.currentIndex() == 0:
            editor = self.editor
        elif self.tabWidget_2.currentIndex() == 1:
            editor = self.editor1
        elif self.tabWidget_2.currentIndex() == 2:
            editor = self.editor2
        ln = int(self.gotofield.text())
        linecursor = QTextCursor(editor.document().findBlockByLineNumber(ln-1))
        editor.moveCursor(QTextCursor.End)
        editor.setTextCursor(linecursor)

    def changeBGColor(self):
        if self.tabWidget_2.currentIndex() == 0:
            editor = self.editor
        elif self.tabWidget_2.currentIndex() == 1:
            editor = self.editor1
        elif self.tabWidget_2.currentIndex() == 2:
            editor = self.editor2
        all = editor.document().toHtml()
        bgcolor = all.partition("<body style=")[2].partition(">")[0].partition('bgcolor="')[2].partition('"')[0]
        if not bgcolor == "":
            col = QColorDialog.getColor(QColor(bgcolor), self)
            if not col.isValid():
                return
            else:
                colorname = col.name()
                new = all.replace("bgcolor=" + '"' + bgcolor + '"', "bgcolor=" + '"' + colorname + '"')
                editor.document().setHtml(new)
        else:
            col = QColorDialog.getColor(QColor("#FFFFFF"), self)
        if not col.isValid():
            return
        else:
            all = editor.document().toHtml()
            body = all.partition("<body style=")[2].partition(">")[0]
            newbody = body + "bgcolor=" + '"' + col.name() + '"'
            new = all.replace(body, newbody)
            editor.document().setHtml(new)
        bgcolor = "background-color: " + col.name()
        editor.setStyleSheet(bgcolor)

    def mergeFormatOnWordOrSelection(self, format):
        if self.tabWidget_2.currentIndex() == 0:
            editor = self.editor
        elif self.tabWidget_2.currentIndex() == 1:
            editor = self.editor1
        elif self.tabWidget_2.currentIndex() == 2:
            editor = self.editor2
        cursor = editor.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.WordUnderCursor)

        cursor.mergeCharFormat(format)
        editor.mergeCurrentCharFormat(format)

    def textSize(self, pointSize):
        pointSize = float(self.comboSize.currentText())
        if pointSize > 0:
            fmt = QTextCharFormat()
            fmt.setFontPointSize(pointSize)
            self.mergeFormatOnWordOrSelection(fmt)

    def clearRecentFiles(self):
        self.settings.remove('recentFileList')
        self.recentFileActs = []
        self.settings.sync()

    def infobox(self,title, message):
        QMessageBox(QMessageBox.Information, title, message, QMessageBox.NoButton, self, Qt.Dialog|Qt.NoDropShadowWindowHint).show()

    def handlePrint(self):
        if self.tabWidget_2.currentIndex() == 0:
            editor = self.editor
        elif self.tabWidget_2.currentIndex() == 1:
            editor = self.editor1
        elif self.tabWidget_2.currentIndex() == 2:
            editor = self.editor2
        if editor.toPlainText() == "":
            self.lineLabel1.setText("no text")
        else:
            dialog = QtPrintSupport.QPrintDialog()
            if dialog.exec_() == QDialog.Accepted:
                self.handlePaintRequest(dialog.printer())
                self.lineLabel1.setText("Document printed")

    def handlePrintPreview(self):
        if self.tabWidget_2.currentIndex() == 0:
            editor = self.editor
        elif self.tabWidget_2.currentIndex() == 1:
            editor = self.editor1
        elif self.tabWidget_2.currentIndex() == 2:
            editor = self.editor2
        if editor.toPlainText() == "":
            self.lineLabel1.setText("no text")
        else:
            dialog = QtPrintSupport.QPrintPreviewDialog()
            dialog.setFixedSize(900,650)
            dialog.paintRequested.connect(self.handlePaintRequest)
            dialog.exec_()
            self.lineLabel1.setText("Print Preview closed")

    def handlePaintRequest(self, printer):
        if self.tabWidget_2.currentIndex() == 0:
            editor = self.editor
        elif self.tabWidget_2.currentIndex() == 1:
            editor = self.editor1
        elif self.tabWidget_2.currentIndex() == 2:
            editor = self.editor2
        printer.setDocName(self.filename)
        document = editor.document()
        document.print_(printer)

    def findNextWord(self):
        if self.tabWidget_2.currentIndex() == 0:
            editor = self.editor
        elif self.tabWidget_2.currentIndex() == 1:
            editor = self.editor1
        elif self.tabWidget_2.currentIndex() == 2:
            editor = self.editor2
        if editor.textCursor().selectedText() == "":
            tc = editor.textCursor()
            tc.select(QTextCursor.WordUnderCursor)
            rtext = tc.selectedText()
        else:
            rtext = editor.textCursor().selectedText()
        self.findfield.setText(rtext)
        self.findText()

    ### QPlainTextEdit contextMenu
    def contextMenuRequested(self, point):
        if self.tabWidget_2.currentIndex() == 0:
            editor = self.editor
        elif self.tabWidget_2.currentIndex() == 1:
            editor = self.editor1
        elif self.tabWidget_2.currentIndex() == 2:
            editor = self.editor2
        cmenu = QMenu()
        cmenu = editor.createStandardContextMenu()
        cmenu.addSeparator()
        cmenu.addAction(self.jumpToAct)
        cmenu.addSeparator()
        cmenu.addAction(QIcon.fromTheme("gtk-find-"),"find this (F10)", self.findNextWord)
        cmenu.addAction(self.texteditAction)
        cmenu.addSeparator()
        cmenu.addAction(QIcon('src/icons/color.png'), "change Color", self.changeColor)
        cmenu.exec_(editor.mapToGlobal(point))   

    def clearLabel(self):
        if self.tabWidget_2.currentIndex() == 0:
            self.editor.clear()
        elif self.tabWidget_2.currentIndex() == 1:
            self.editor1.clear()
        elif self.tabWidget_2.currentIndex() == 2:
            self.editor2.clear()

    """def readSettings(self):
        if self.settings.value("pos") != "":
            pos = self.settings.value("pos", QPoint(200, 200))
            self.move(pos)
        if self.settings.value("size") != "":
            size = self.settings.value("size", QSize(400, 400))
            self.resize(size)"""

    def format(color, style=''):
        """Return a QTextCharFormat with the given attributes.
        """
        _color = QColor()
        _color.setNamedColor(color)

        _format = QTextCharFormat()
        _format.setForeground(_color)
        if 'bold' in style:
            _format.setFontWeight(QFont.Bold)
        if 'italic' in style:
            _format.setFontItalic(True)

        return _format

    def changeColor(self):
        if self.tabWidget_2.currentIndex() == 0:
            editor = self.editor
        elif self.tabWidget_2.currentIndex() == 1:
            editor = self.editor1
        elif self.tabWidget_2.currentIndex() == 2:
            editor = self.editor2
        fmt = QTextCharFormat()
        if not editor.textCursor().selectedText() == "":
            col = QColorDialog.getColor(QColor("#" + editor.textCursor().selectedText()), self)
            if not col.isValid():
                return
            else:
                colorname = col.name()
                _color = QColor()
                _color.setNamedColor(colorname)
                fmt.setForeground(_color)
                self.mergeFormatOnWordOrSelection(fmt)
        else:
            col = QColorDialog.getColor(QColor("black"), self)
            if not col.isValid():
                return
            else:
                colorname = col.name()
                _color = QColor()
                _color.setNamedColor(colorname)
                fmt.setForeground(_color)
                self.mergeFormatOnWordOrSelection(fmt)

    """def clearBookmarks(self):
        self.bookmarks.clear()"""

    def newFile(self):
        if self.tabWidget_2.currentIndex() == 0:
            editor = self.editor
        elif self.tabWidget_2.currentIndex() == 1:
            editor = self.editor1
        elif self.tabWidget_2.currentIndex() == 2:
            editor = self.editor2
        ### New File
        if self.maybeSave():
            editor.clear()
            #editor.setPlainText(self.mainText)
            self.filename = ""
            self.setModified(False)
            editor.moveCursor(editor.cursor.End)
            self.lineLabel1.setText("new File created.")
            editor.setFocus()
            #self.bookmarks.clear()
            self.setWindowTitle("new File[*]") 

    """def openFileOnStart(self, path=None):
        ### open File
        if path:
            self.openPath = QFileInfo(path).path() ### store path for next time
            inFile = QFile(path)
            if inFile.open(QFile.ReadWrite | QFile.Text):
                text = inFile.readAll()
                try:
                        # Python v3.
                    text = str(text, encoding = 'utf8')
                except TypeError:
                        # Python v2.
                    text = str(text)
                self.editor.setPlainText(text.replace(chr(9), "    "))
                self.setModified(False)
                self.setCurrentFile(path)
                self.editor.setFocus()
                ### save backup
                file = QFile(self.filename + "_backup")
                if not file.open( QFile.WriteOnly | QFile.Text):
                    QMessageBox.warning(self, "Error",
                        "Cannot write file %s:\n%s." % (self.filename, file.errorString()))
                    return
                outstr = QTextStream(file)
                QApplication.setOverrideCursor(Qt.WaitCursor)
                outstr << self.editor.toPlainText()
                QApplication.restoreOverrideCursor()
                self.lineLabel1.setText("File '" + path + "' loaded succesfully & bookmarks added & backup created ('" + self.filename + "_backup" + "')")"""

    def openFile(self, path=None):
        ### open File
        if self.openPath == "":
            self.openPath = self.dirpath
        if self.maybeSave():
            if not path:
                path, _ = QFileDialog.getOpenFileName(self, "Open File", self.openPath,
                    "Text Files (*.txt);; all Files (*)")

            '''if path:
                self.openFileOnStart(path)'''

    def fileSave(self):
        if self.tabWidget_2.currentIndex() == 0:
            editor = self.editor
        elif self.tabWidget_2.currentIndex() == 1:
            editor = self.editor1
        elif self.tabWidget_2.currentIndex() == 2:
            editor = self.editor2
        if (self.filename != ""):
            file = QFile(self.filename)
            if not file.open( QFile.WriteOnly | QFile.Text):
                QMessageBox.warning(self, "Error",
                        "Cannot write file %s:\n%s." % (self.filename, file.errorString()))
                return

            outstr = QTextStream(file)
            QApplication.setOverrideCursor(Qt.WaitCursor)
            outstr << editor.toPlainText()
            QApplication.restoreOverrideCursor()                
            self.setModified(False)
            self.fname = QFileInfo(self.filename).fileName() 
            self.setWindowTitle(self.fname + "[*]")
            self.lineLabel1.setText("File saved.")
            self.setCurrentFile(self.filename)
            editor.setFocus()

        else:
            self.fileSaveAs()

    def exportPDF(self):
        if self.tabWidget_2.currentIndex() == 0:
            editor = self.editor
        elif self.tabWidget_2.currentIndex() == 1:
            editor = self.editor1
        elif self.tabWidget_2.currentIndex() == 2:
            editor = self.editor2
        if editor.toPlainText() == "":
            self.lineLabel1.setText("no text")
        else:
            if (self.filename != ""):
                newname = self.strippedName(self.filename).replace(QFileInfo(self.filename).suffix(), "pdf")
            else:
                newname = 'tallies'
            #newname = editor.strippedName(self.filename).replace(QFileInfo(self.filename).suffix(), "pdf")
            fn, _ = QFileDialog.getSaveFileName(self,
                    "PDF files (*.pdf);;All Files (*)", (QDir.homePath() + "/PDF/" + newname))
            printer = QtPrintSupport.QPrinter(QtPrintSupport.QPrinter.HighResolution)
            printer.setOutputFormat(QtPrintSupport.QPrinter.PdfFormat)
            printer.setPaperSize(QtPrintSupport.QPrinter.A4)
            printer.setPageSize(QtPrintSupport.QPrinter.A4)
            printer.setPageMargins(0, 10, 0, 10, QtPrintSupport.QPrinter.Millimeter)
            if self.Landscape_CB.isChecked():
                printer.setOrientation(QtPrintSupport.QPrinter.Landscape)
                textWidth = printer.pageRect().height()
            else:
                printer.setOrientation(QtPrintSupport.QPrinter.Portrait)
                textWidth = printer.pageRect().width()
            

            editor.document().setTextWidth(textWidth)
            
            # Adjust font size to fit within available width
            fontMetrics = editor.fontMetrics()
            text = editor.toPlainText()
            font = self.adjustFontSizeToFitWidth(editor, text, textWidth)
            editor.document().setDefaultFont(font)

            #printer.setFullPage(True)
            printer.setOutputFileName(fn)
            editor.document().print_(printer)
            # restore old font
            font.setPointSize(float(self.comboSize.currentText()))
            fontMetrics = editor.fontMetrics()
            editor.document().setDefaultFont(font)

    def adjustFontSizeToFitWidth(self, editor, text, width):
        # Start with a large font size
        font = editor.document().defaultFont()
        font.setPointSize(12)

        # Create a QFontMetrics object to measure text size
        fm = editor.fontMetrics()

        # Iterate until the text fits within the width
        while fm.width(text) > width and font.pointSize() > 4:
            font.setPointSize(font.pointSize() - 1)

        return font
    
    def fileSaveAs(self):
        ### save File
        fn, _ = QFileDialog.getSaveFileName(self, "Save as...", self.filename, "Text Files (*.txt);; all Files (*)")

        if not fn:
            print("Error saving")
            return False

        self.filename = fn
        self.fname = QFileInfo(QFile(fn).fileName())
        return self.fileSave()

    def maybeSave(self):
        ### ask to save
        if not self.isModified():
            return True

        if self.filename.startswith(':/'):
            return True

        ret = QMessageBox.question(self, "Message",
                "<h4><p>The document was modified.</p>\n" \
                "<p>Do you want to save changes?</p></h4>",
                QMessageBox.Yes | QMessageBox.Discard | QMessageBox.Cancel)

        if ret == QMessageBox.Yes:
            if self.filename == "":
                self.fileSaveAs()
                return False
            else:
                self.fileSave()
                return True

        if ret == QMessageBox.Cancel:
            return False

        return True   

    def isModified(self):
        if self.tabWidget_2.currentIndex() == 0:
            editor = self.editor
        elif self.tabWidget_2.currentIndex() == 1:
            editor = self.editor1
        elif self.tabWidget_2.currentIndex() == 2:
            editor = self.editor2
        return editor.document().isModified()

    def setModified(self, modified):
        if self.tabWidget_2.currentIndex() == 0:
            editor = self.editor
        elif self.tabWidget_2.currentIndex() == 1:
            editor = self.editor1
        elif self.tabWidget_2.currentIndex() == 2:
            editor = self.editor2
        editor.document().setModified(modified)

    """def createActions(self):
        for i in range(self.MaxRecentFiles):
            self.recentFileActs.append(QAction(self, visible=False, triggered=self.openRecentFile))"""

    """def openRecentFile(self):
        action = self.sender()
        if action:
            myfile = action.data()
            if (self.maybeSave()):
                if QFile.exists(myfile):
                    self.openFileOnStart(myfile)
                else:
                    self.msgbox("Info", "File does not exist!")"""

    def setCurrentFile(self, fileName):
        self.filename = fileName
        if self.filename:
            self.setWindowTitle(self.strippedName(self.filename) + "[*]")
        else:
            self.setWindowTitle("no File")      
        
        files = self.settings.value('recentFileList', [])

        try:
            files.remove(fileName)
        except ValueError:
            pass

        if not fileName == "/tmp/tmp.py":
            files.insert(0, fileName)
        #del files[self.MaxRecentFiles:]

        self.settings.setValue('recentFileList', files)

    def updateRecentFileActions(self):
        if self.settings.contains('recentFileList'):
            mytext = ""
            files = self.settings.value('recentFileList', [])

    def strippedName(self, fullFileName):
        return QFileInfo(fullFileName).fileName()

class EmittingStream(QtCore.QObject):
    textWritten = QtCore.pyqtSignal(str)

    def write(self, text):
        self.textWritten.emit(str(text))
        pass

    def flush(self):
        pass

class CheckableComboBox(QtWidgets.QComboBox):
    def __init__(self, parent = None):
        super(CheckableComboBox, self).__init__(parent)
        self._changed = False
        self.setView(QtWidgets.QListView(self))
        self.view().pressed.connect(self.handleItemPressed)
        self.setModel(PyQt5.QtGui.QStandardItemModel(self))

    def handleItemPressed(self, index):
        item = self.model().itemFromIndex(index)
        if item.checkState() == QtCore.Qt.Checked:
            item.setCheckState(QtCore.Qt.Unchecked)
            self.undo_action(index.row())
        else:
            item.setCheckState(QtCore.Qt.Checked)
            self.do_action(index.row())
        self._changed = True

    def do_action(self, index):
        if self.model().item(index).text() == 'All bins' and self.model().item(1, 0).checkState() == QtCore.Qt.Checked:
            for i in range(2, self.count()):
                self.model().item(i, 0).setCheckState(QtCore.Qt.Checked)

    def undo_action(self, index):
        if self.model().item(index).text() == 'All bins' and self.model().item(1, 0).checkState() != QtCore.Qt.Checked:
            for i in range(1, self.count()):    #  2
                self.model().item(i, 0).setCheckState(QtCore.Qt.Unchecked)
        else:
            try:    
                self.model().item(1, 0).setCheckState(QtCore.Qt.Unchecked)
            except:
                pass

    def checkedItems(self):
        checkedItems = []
        for index in range(self.count()):
            item = self.model().item(index)
            if item.checkState() == QtCore.Qt.Checked:
                checkedItems.append(index)
        return checkedItems

    def hidePopup(self):
        if not self._changed:
            super().hidePopup()
        self._changed = False

    def itemChecked(self, index):
        item = self.model().item(index, self.modelColumn())
        return item.checkState() == Qt.Checked

    def setItemChecked(self, index, checked=False):
        item = self.model().item(index, self.modelColumn())  # QStandardItem object
        if checked:
            item.setCheckState(Qt.Checked)
        else:
            item.setCheckState(Qt.Unchecked)

    def setItemDisabled(self, index):
        item = self.model().item(index, self.modelColumn())  # QStandardItem object
        if item:
            item.setCheckState(Qt.Unchecked)
            item.setEnabled(False)

class VLine(QFrame):
    # a simple VLine, like the one you get from designer
    def __init__(self):
        super(VLine, self).__init__()
        self.setFrameShape(self.VLine | self.Sunken)


#  to be removed if called by gui.py
"""
if not QApplication.instance():
    qapp = QApplication(sys.argv)
else:
    qapp = QApplication.instance()

mainwindow = TallyDataProcessing('', '')
mainwindow.show()

# Only call exec() if the event loop hasn't been started yet
sys.exit(qapp.exec())
"""




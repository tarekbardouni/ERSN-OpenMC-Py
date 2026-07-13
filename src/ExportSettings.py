#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import os
import math
import re
import numpy as np
import PyQt5
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
from PyQt5 import QtCore, QtGui, QtWidgets
from src.syntax_py import Highlighter
from src.PyEdit import TextEdit, NumberBar 
import math
from PyQt5.QtGui import QValidator

class EmittingStream(QtCore.QObject):
    textWritten = QtCore.pyqtSignal(str)
 
    def write(self,text):
        self.textWritten.emit(str(text))
        pass

    def flush(self):
        pass 

class Expression(str):
    def __repr__(self):
        return self

################################################################################
#//////////////////////////////////////////////////////////////////////////////#
#          M A I N    C L A S S    E X P O R T S E T T I N G S                 #
#\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\#
################################################################################

class ExportSettings(QWidget):
    from .func import resize_ui, showDialog, Def_Source_ToolTips, Exit, Move_Commands_to_End
    from .class_CheckableComboBox import CheckableComboBox
    from .Validators import UniversalNumericListValidator

    def __init__(self, OpenMC_Ver, v_1, Geom, Sett, Directory, Surf_list, Surf_Id_list, Cells_list, Mat_list, Univ_list, Vol_Calcs_list, 
                            Source_list, Source_Id, Strength_list, parent=None):
        super(ExportSettings, self).__init__(parent)
        global UniversalNumericListValidator
        UniversalNumericListValidator = self.UniversalNumericListValidator
        uic.loadUi("src/ui/ExportSettings.ui", self)
        self.v_1 = v_1
        self.Uniform_Sampling_CB.setEnabled(False)
        self.text_inserted = False
        self._initButtons()
        self.Insert_Header = True
        #self.Imported_X_Y_List = False
        self.openmc_version = OpenMC_Ver
        self.directory = Directory
        self.surface_name_list = Surf_list
        self.surface_id_list = Surf_Id_list
        self.Source_Surfaces_CB.addItems(self.surface_name_list)
        self.cell_name_list = Cells_list
        self.materials_name_list = Mat_list
        self.universes_name_list = Univ_list
        self.vol_calcs = Vol_Calcs_list
        self.list_of_cells = []
        self.list_of_universes = []
        self.list_of_surfaces = []
        self.list_of_surfaces_ids = []
        self.list_of_materials = []  
        self.Source_name_list = Source_list
        self.Source_id_list = Source_Id
        self.Source_strength_list = Strength_list
        self.Geom = Geom
        self.Sett = Sett
        #self.vol_calcs = []
        self.Strength_LE.setText('1.')
        self.src_filename = ''
        self.Threshold_CB.setCurrentIndex(3)
        self.Entropy_LE_List = [self.X_dim, self.Y_dim, self.Z_dim, 
                                self.X_LL_Entropy, self.Y_LL_Entropy, self.Z_LL_Entropy,
                                self.X_UR_Entropy, self.Y_UR_Entropy, self.Z_UR_Entropy]
        # validators
        for item in [self.LineEdit_1, self.LineEdit_2, self.LineEdit_5, self.Particles_Number_LE, 
                     self.Trigger_max_batches_LE, self.Trigger_batch_interval_LE, self.Source_ID_LE]:
            item.setValidator(UniversalNumericListValidator(
                    schema=("pos_int",), max_items=1, allow_negative=False, allow_pi=False))

        for item in [self.X_LL, self.Y_LL, self.Z_LL, self.X_UR, self.Y_UR, self.Z_UR,
                     self.Mu_Min_LE, self.Mu_Max_LE]:
            item.setValidator(UniversalNumericListValidator(
                schema=("float",), max_items=1, allow_negative=True, allow_pi=False))
            
        for item in [self.Strength_LE, self.Keff_Trigger_Value_LE, self.W_CutOff_LE, self.E_CutOff_LE,
                     self.T_CutOff_LE]:
            item.setValidator(UniversalNumericListValidator(
                schema=("float",), max_items=1, allow_negative=False, allow_pi=False))

        for item in [self.X_dim, self.Y_dim, self.Z_dim]: 
            item.setValidator(UniversalNumericListValidator(
                schema=("pos_int",), max_items=1, allow_negative=False, allow_pi=False))
        
        for item in [self.X_LL_Entropy, self.Y_LL_Entropy, self.Z_LL_Entropy,
                                self.X_UR_Entropy, self.Y_UR_Entropy, self.Z_UR_Entropy]:
            item.setValidator(UniversalNumericListValidator(
                schema=("float",), max_items=1, allow_negative=True, allow_pi=False))
            
        for item in self.Entropy_LE_List:
            item.setEnabled(False)
            item.clear()
                
        for item in [self.Phi_Min_LE, self.Phi_Max_LE]:
            item.setValidator(UniversalNumericListValidator(
                schema=("float",), max_items=1, allow_negative=True, allow_pi=True))

        for item in [self.Energy_LE, self.Proba_LE]:
            item.setValidator(UniversalNumericListValidator(
                schema=("float",), max_items=None, allow_negative=False, allow_pi=False))

        self.Origin_LE.setValidator(UniversalNumericListValidator(
                schema=("float",), max_items=3, allow_negative=True, allow_pi=False))
        self.Add_Tracks_PB.setEnabled(False)
        for Label in [self.label_X_R, self.label_Y_Theta, self.label_Z_phi]:
            Label.setAlignment(Qt.AlignCenter)
        self.Import_Lists_PB.hide()
        self.label_25.hide()
        self.Inactive_Found = False
        self.Generations_Found = False
        #
        self.Widget_Status()
        self.Def_Source_ToolTips()
        self.Def_Source()
        self.Def_Energy_Dist()
        self.Def_Angle_Dist()
        self.Def_Time_Dist()
        self.Def_Constraints()
        
        if self.Source_id_list:
            ID = int(self.Source_id_list[-1]) + 1
        else:
            ID = 1
        self.Source_ID_LE.setText(str(ID))
        self.Name_LE.setText('source' + str(ID))
        self.Source_id = ID
        # add new editor
        self.plainTextEdit = TextEdit()
        self.plainTextEdit.setWordWrapMode(QTextOption.NoWrap)
        self.numbers = NumberBar(self.plainTextEdit)
        layoutH = QHBoxLayout()
        layoutH.addWidget(self.numbers)
        layoutH.addWidget(self.plainTextEdit)
        self.EditorLayout.addLayout(layoutH, 0, 0)
        self.Settings_Header = '\n############################################################################### \n'+\
                                 '#                 Exporting to OpenMC settings.xml file \n'+\
                                 '###############################################################################'                
                
        self.Find_Run_Mode()
        
        sys.stdout = EmittingStream(textWritten=self.normalOutputWritten)
        #sys.stderr = EmittingStream(textWritten=self.normalOutputWritten)
        # to show window at the middle of the screen and resize it to the screen size
        self.resize_ui()


    def _initButtons(self):
        self.Run_Mode_CB.currentIndexChanged.connect(self.Widget_Status)
        self.Entropy_type_CB.currentIndexChanged.connect(self.Entropy_Widgets_Status)
        self.Photon_CB.stateChanged.connect(self.Widget_Status_1)
        self.Create_Surface_SRC_CB.stateChanged.connect(self.Widget_Status_2)
        self.Volume_Calc_CB.currentIndexChanged.connect(self.Widget_Status_3)

        self.Direction_Dist_CB.currentIndexChanged.connect(self.Widget_Status_4)
        self.Ref_UVW_CB.currentIndexChanged.connect(self.Widget_Status_5)
        self.Ref_VWU_CB.currentIndexChanged.connect(self.Widget_Status_6)

        self.One_Source_RB.toggled.connect(self.Def_Source_Settings)
        self.Uniform_Sampling_CB.stateChanged.connect(self.Uniform_Sampling)
        self.Source_Type_CB.currentIndexChanged.connect(self.Def_Source_Settings)
        self.Source_Type_CB.currentIndexChanged.connect(self.Def_Source_ToolTips)
        self.Source_Geom_CB.currentIndexChanged.connect(self.Def_Source_ToolTips)
        self.Source_Geom_CB.currentIndexChanged.connect(self.Def_Source_Spatial)

        self.X_Dist_CB.currentIndexChanged.connect(self.Def_Source_ToolTips)
        self.Y_Dist_CB.currentIndexChanged.connect(self.Def_Source_ToolTips)
        self.Z_Dist_CB.currentIndexChanged.connect(self.Def_Source_ToolTips)
        self.X_Dist_CB.currentIndexChanged.connect(self.Def_Source_Spatial_Dist_X)
        self.Y_Dist_CB.currentIndexChanged.connect(self.Def_Source_Spatial_Dist_Y)
        self.Z_Dist_CB.currentIndexChanged.connect(self.Def_Source_Spatial_Dist_Z)        

        self.Source_Geom_CB.currentIndexChanged.connect(self.Def_Source_Spatial_Dist_X)
        self.Source_Geom_CB.currentIndexChanged.connect(self.Def_Source_Spatial_Dist_Y)
        self.Source_Geom_CB.currentIndexChanged.connect(self.Def_Source_Spatial_Dist_Z)

        self.Energy_Dist_CB.currentIndexChanged.connect(self.Def_Source_ToolTips)
        self.Energy_Dist_CB.currentIndexChanged.connect(self.Def_Source_Energy)
        self.Time_Dist_CB.currentIndexChanged.connect(self.Def_Source_Time)
        self.Constraints_CB.currentIndexChanged.connect(self.Def_Source_Constraints)
        self.Use_Constraints_Checkbox.stateChanged.connect(self.Use_Constraints)

        self.Mu_Dist_CB.currentIndexChanged.connect(self.Def_Source_Angle_Dist_Mu)
        self.Phi_Dist_CB.currentIndexChanged.connect(self.Def_Source_Angle_Dist_Phi)
        self.Mu_Dist_CB.currentIndexChanged.connect(self.Def_Source_ToolTips)
        self.Phi_Dist_CB.currentIndexChanged.connect(self.Def_Source_ToolTips)

        self.Particle_CB.currentIndexChanged.connect(self.Def_Energy_Dist)
        self.Create_Separate_SRC_CB.stateChanged.connect(self.Create_Separate_Source)
        self.Create_Surface_SRC_CB.stateChanged.connect(self.Create_Surface_Source)
        self.LL_CheckB.stateChanged.connect(self.onStateChange)
        self.GeomBound_CheckB.stateChanged.connect(self.onStateChange)
        self.Source_Surfaces_CB.currentIndexChanged.connect(self.Add_Surface_Source)
        self.Import_Lists_PB.clicked.connect(lambda: self.Import_x_y_Lists(self.Energy_LE, self.Proba_LE))
        
        self.Add_Run_Mode_PB.clicked.connect(self.Run_Mode)
        self.Add_CutOff_PB.clicked.connect(self.Add_CutOff)
        self.Add_Vol_Calc_PB.clicked.connect(self.Volume_Calculation)
        self.Add_Tracks_PB.clicked.connect(self.Tracks_Settings)
        self.Add_Trigger_PB.clicked.connect(self.Keff_Trigger_Settings)
        self.Add_Entropy_PB.clicked.connect(self.Entropy_Settings)
        
        self.Add_Source_PB.clicked.connect(self.Add_Sources)
        self.Add_space_PB.clicked.connect(self.Add_Source_Space)
        self.Add_Energy_PB.clicked.connect(self.Add_Source_Energy)
        self.Add_Angle_PB.clicked.connect(self.Add_Source_Angle)
        self.Add_Time_PB.clicked.connect(self.Add_Source_Time)
        self.Add_Constraints_PB.clicked.connect(self.Add_Source_Constraints)

        self.Cells_CB.currentIndexChanged.connect(self.Add_Cells_Volume)
        self.Export_Settings_PB.clicked.connect(self.Export_to_Main_Window)
        self.Clear_PB.clicked.connect(self.clear_text)
        self.Exit_PB.clicked.connect(self.Exit)

        self.ttb_RB.setDisabled(True)
        self.led_RB.setDisabled(True)
        self.ttb_RB.setChecked(True)
        self.led_RB.setChecked(False)
        self.Create_Separate_SRC_CB.hide()
        self.Create_Surface_SRC_CB.hide()
        self.Source_Surfaces_CB.hide()
        self.Cells_CB.hide()
        self.LineEdit_3.hide()
        self.LineEdit_4.hide()
        self.Particles_Max_LE.hide()
        self.Volume_Calc_CB.hide()
        self.Add_Vol_Calc_PB.hide()
        self.Exponent_LE.hide()
        self.Interpolate_CB.hide()
        self.Add_Run_Mode_PB.setEnabled(False)
        self.Add_Vol_Calc_PB.setEnabled(False)
        self.Add_Entropy_PB.setEnabled(False)
        self.Num_of_Srcs_Label.setEnabled(False)
        self.Number_of_Sources.setEnabled(False)
        self.Create_Separate_SRC = False
        self.Create_Surface_SRC = False
        self.Name_LE.setText('source')
        self.Origin_LE.hide()
        self.Origin_Label.hide()
        self.Disable_SRC_Widgets()
        self.LL_CheckB.hide()
        self.GeomBound_CheckB.hide()

    @pyqtSlot(int)
    def onStateChange(self, state):
        if state == Qt.Checked:
            if self.sender() == self.LL_CheckB:
                self.GeomBound_CheckB.setChecked(False)
            elif self.sender() == self.GeomBound_CheckB:
                self.LL_CheckB.setChecked(False)
            self.Set_LL_GB()

    def Find_string(self, text_window, string_to_find):
        self.list_of_items = []
        self.current_line = ''
        self.Insert_Header = True
        document = text_window.toPlainText()
        lines = [item for item in document.split('\n') if item and item != '#']
        for line in lines:
            if string_to_find in line:
                self.current_line = line
                self.list_of_items.append(line[0:len(line) -1])
                self.Insert_Header = False
                break

    def Add_Cells_Volume(self):
        if self.Run_Mode_CB.currentIndex() == 3:
            #self.list_of_cells.clear()
            if self.Cells_CB.currentIndex() != 0:
                if self.Volume_Calc_CB.currentIndex() == 1:
                    cell = self.cell_name_list[self.Cells_CB.currentIndex() - 1]
                    if cell not in self.list_of_cells:
                        self.list_of_cells.append(cell)
                    self.LineEdit_3.setText(str(self.list_of_cells).replace("'", ""))
                elif self.Volume_Calc_CB.currentIndex() == 3:
                    mat = self.materials_name_list[self.Cells_CB.currentIndex() - 1]
                    if mat not in self.list_of_materials:
                        self.list_of_materials.append(mat)
                    self.LineEdit_3.setText(str(self.list_of_materials).replace("'", ""))
                elif self.Volume_Calc_CB.currentIndex() == 4:
                    if self.universes_name_list:
                        univ = self.universes_name_list[self.Cells_CB.currentIndex() - 1]
                        if univ not in self.list_of_universes:
                            self.list_of_universes.append(univ)
                        self.LineEdit_3.setText(str(self.list_of_universes).replace("'", ""))
                
            self.Cells_CB.setCurrentIndex(0)

    def Widget_Status(self):                            # If Run Mode changed
        if not self.Inactive_Found:
            self.inactives = 10
        if not self.Generations_Found:
            self.generations = 1
        self.LineEdit_4.setText('')
        self.list_of_surfaces_ids.clear()
        if self.Run_Mode_CB.currentIndex() in [0, 1, 2]:
            self.Vol_Trigger_CB.hide()
            self.Vol_Trigger_type_CB.hide()
            self.Vol_Trigger_value_CB.hide()
            for item in [self.Volume_Calc_CB, self.Source_Surfaces_CB, self.Cells_CB, self.label_11,
                            self.LineEdit_4, self.LineEdit_3, self.Particles_Max_LE]:
                item.hide()
            for item in [self.Label_1, self.Label_2, self.Label_5, self.Label_37, self.LineEdit_1, self.LineEdit_2,
                        self.LineEdit_5, self.Particles_Number_LE, self.Create_Separate_SRC_CB, self.Create_Surface_SRC_CB]:
                item.show()
                if self.Run_Mode_CB.currentIndex() == 0:
                    item.setEnabled(False)
                elif self.Run_Mode_CB.currentIndex() in [1, 2]:
                    item.setEnabled(True)
            
            if self.Run_Mode_CB.currentIndex() == 0:
                self.W_CutOff_CB.clear()
                self.E_CutOff_CB.clear()
                self.T_CutOff_CB.clear()
            elif self.Run_Mode_CB.currentIndex() in [1, 2]:
                self.W_CutOff_CB.addItems(['select type', 'weight', 'weight_avg'])
                self.E_CutOff_CB.addItems(['select type', 'energy_neutron', 'energy_photon', 'energy_electron', 'energy_positron'])
                self.T_CutOff_CB.addItems(['select type', 'time_neutron', 'time_photon', 'time_electron', 'time_positron'])

            self.Label_1.setText('Batches')
            self.Label_2.setText('Inactive Batches')
            self.Label_5.setText('Generations')
            self.LineEdit_2.setText(str(self.inactives))
            self.LineEdit_5.setText(str(self.generations))
            if self.Run_Mode_CB.currentIndex() in [1, 2]:
                self.Add_Run_Mode_PB.setEnabled(True)
                self.Volume_Calc_CB.hide()
                self.Cells_CB.hide()
                self.LineEdit_3.hide()
                self.Create_Separate_SRC_CB.show()
                self.Create_Surface_SRC_CB.show()
                self.label_16.setEnabled(True)
                self.Photon_CB.setEnabled(True)
                self.ttb_RB.setChecked(True)
                self.led_RB.setChecked(False)
                if self.Run_Mode_CB.currentIndex() == 1:
                    self.LineEdit_2.setEnabled(True)
                    self.Label_2.setEnabled(True)                    
                elif self.Run_Mode_CB.currentIndex() == 2:
                    self.LineEdit_5.show()
                    self.Label_5.show()
                    self.Volume_Calc_CB.hide()
                    self.LineEdit_2.setEnabled(False)
                    self.Label_2.setEnabled(False)
            self.LL_CheckB.hide()
            self.GeomBound_CheckB.hide()
        elif self.Run_Mode_CB.currentIndex() == 3:
            self.Vol_Trigger_CB.show()
            self.Vol_Trigger_type_CB.show()
            self.Vol_Trigger_value_CB.show()
            self.LL_CheckB.show()
            self.GeomBound_CheckB.show()
            self.Add_Run_Mode_PB.setEnabled(False)
            self.label_16.setEnabled(False)
            self.Label_17.setEnabled(False)
            self.Photon_CB.setEnabled(False)
            self.ttb_RB.setEnabled(False)
            self.led_RB.setEnabled(False)
            self.Photon_CB.setChecked(False)
            self.Create_Separate_SRC_CB.setChecked(False)
            self.Create_Surface_SRC_CB.setChecked(False)        
            if self.Volume_Calc_CB.currentIndex() == 0:
                self.Add_Vol_Calc_PB.setEnabled(False)
            else:
                self.Add_Vol_Calc_PB.setEnabled(True)
            self.GeomBound_CheckB.show()
            self.LL_CheckB.show()
            self.Volume_Calc_CB.setCurrentIndex(0)
            self.Add_Vol_Calc_PB.show()
            self.Add_Run_Mode_PB.hide()
            self.Volume_Calc_CB.show()
            self.LineEdit_1.hide()
            self.Label_1.hide()
            self.LineEdit_2.show()
            self.Label_2.show()
            self.Label_5.show()
            self.Label_5.setText('Lower Left (x, y, z)')
            self.Label_2.setText('Upper Right (x, y, z)')
            self.LineEdit_5.setText('(-1, -1, -1)')
            self.LineEdit_2.setText('(1, 1, 1)')
            self.Create_Separate_SRC_CB.setEnabled(False)
            self.Create_Surface_SRC_CB.setEnabled(False)
        
        self.Create_Separate_SRC_CB.setChecked(False)
        self.Create_Surface_SRC_CB.setChecked(False)

    def Widget_Status_1(self):                              # if photon mode changed
        if self.Photon_CB.isChecked():
            self.ttb_RB.setEnabled(True)
            self.led_RB.setEnabled(True)
            self.Label_17.setEnabled(True)
        else:
            self.ttb_RB.setEnabled(False)
            self.led_RB.setEnabled(False)
            self.Label_17.setEnabled(False)

    def Widget_Status_2(self):                              # if creating source mode changed
            if self.Create_Surface_SRC:
                self.Particles_Max_LE.show()
                self.LineEdit_4.show()
                self.Source_Surfaces_CB.show()
                self.Source_Surfaces_CB.setCurrentIndex(0)
            else:
                pass

    def Set_LL_GB(self):
        if self.GeomBound_CheckB.isChecked():
            self.LineEdit_5.setEnabled(False)
            self.LineEdit_2.setEnabled(False)
        elif self.LL_CheckB.isChecked():
            self.LineEdit_5.setEnabled(True)
            self.LineEdit_2.setEnabled(True)

    def Widget_Status_3(self):                              # if volume calculation option changed
        items = [self.Label_5, self.LineEdit_5, self.Label_37, self.Particles_Number_LE, self.Label_2, self.LineEdit_2]
        if self.Volume_Calc_CB.currentIndex() == 0:
            self.Add_Vol_Calc_PB.setEnabled(False)
            for item in items:
                item.setEnabled(False)
            return
        self.LineEdit_5.setText('(-1, -1, -1)')
        self.LineEdit_2.setText('(1, 1, 1)')
        self.LineEdit_3.show()
        self.LineEdit_3.clear()
        self.Add_Vol_Calc_PB.setEnabled(True)
        for item in items:
            item.setEnabled(True)
        self.Cells_CB.show()
        self.Cells_CB.clear()
        if self.Volume_Calc_CB.currentIndex() == 1:            # cells volume
            if self.cell_name_list:                     
                self.Cells_CB.addItem('Select cell')
                self.Cells_CB.addItems(self.cell_name_list)        
        elif self.Volume_Calc_CB.currentIndex() == 2:
            self.Cells_CB.clear()
            self.LineEdit_3.setText(self.Geom + '.get_all_cells().values()')    
        elif self.Volume_Calc_CB.currentIndex() == 3:               # materials volume
            if self.materials_name_list:
                self.Cells_CB.addItem('Select material')
                self.Cells_CB.addItems(self.materials_name_list)
        elif self.Volume_Calc_CB.currentIndex() == 4:               # universes volume
            if self.universes_name_list:                     
                self.Cells_CB.addItem('Select universe')
                self.Cells_CB.addItems(self.universes_name_list)

    def Widget_Status_5(self):
        if self.Ref_UVW_CB.currentIndex() == 6:
            self.UVW_LE.setEnabled(True)
        else:
            self.UVW_LE.setEnabled(False)

    def Widget_Status_6(self):
        if self.Ref_VWU_CB.currentIndex() == 6:
            self.VWU_LE.setEnabled(True)
        else:
            self.VWU_LE.setEnabled(False)

    def Widget_Status_4(self):
        if self.Direction_Dist_CB.currentIndex() == 0:
            self.Add_Angle_PB.setEnabled(False)
        else:
            self.Add_Angle_PB.setEnabled(True)

        #if self.Direction_Dist_CB.currentIndex() in [0, 1]:
        for item in [self.Mu_Min_LE, self.Mu_Max_LE, self.Phi_Min_LE, self.Phi_Max_LE,
                    self.label_10, self.Ref_UVW_CB, self.label_29, self.Ref_VWU_CB, 
                    self.Mu_Dist_CB, self.Phi_Dist_CB, self.label_20, self.label_21,
                    self.Mu_Interp_CB, self.Phi_Interp_CB, self.label_28, self.label_32]:
            item.setEnabled(False)
        
        if self.Direction_Dist_CB.currentIndex() in [2, 3]:
            for item in [self.label_10, self.Ref_UVW_CB]:
                item.setEnabled(True)
        elif self.Direction_Dist_CB.currentIndex() == 4:
            for item in [self.Mu_Min_LE, self.Mu_Max_LE, self.Phi_Min_LE, self.Phi_Max_LE,
                        self.label_10, self.Ref_UVW_CB, self.label_29, self.Ref_VWU_CB,
                        self.Mu_Dist_CB, self.Phi_Dist_CB, self.label_20, self.label_21,
                        self.label_28, self.label_32]:
                item.setEnabled(True)

        self.Ref_VWU_CB.setCurrentIndex(0)
        self.Ref_UVW_CB.setCurrentIndex(2)

    def Use_Constraints(self): 
        Ws = [self.label_35, self.label_36, self.Constraints_LB_LE, self.Constraints_UB_LE, 
              self.Constraints_CB]      
        if self.Use_Constraints_Checkbox.isChecked():
            for w in Ws:
                w.setEnabled(True)
        else:
            for w in Ws:
                w.setEnabled(False)
            self.Add_Constraints_PB.setEnabled(False)
            self.Constraints_CB.setCurrentIndex(0)

    def Def_Settings(self):
        self.Find_string(self.v_1, "openmc.Settings")
        if self.Insert_Header:
            self.Find_string(self.plainTextEdit, "openmc.Settings")
            if self.Insert_Header:
                print(self.Settings_Header)
                print(self.Sett + " = openmc.Settings()\n")
            else:
                pass

    def Import_OpenMC(self):
        self.Find_string(self.v_1, "import openmc")
        if self.Insert_Header:
            cursor = self.v_1.textCursor()
            cursor.setPosition(0)
            self.v_1.setTextCursor(cursor)
            self.v_1.insertPlainText('import openmc\n')

    def Import_Numpy(self):
        if 'np.pi' in self.plainTextEdit.toPlainText():
            self.Find_string(self.plainTextEdit, "import numpy")
            if self.Insert_Header:
                self.Find_string(self.v_1, "import numpy")
                if self.Insert_Header:
                    print('import numpy as np')

    def Run_Mode(self):
        self.Import_OpenMC()
        # /////////////////////////////   Run Mode   /////////////////////////////
        if self.Run_Mode_CB.currentIndex() == 0:
            self.showDialog('Warning', 'Select Run Mode first !')
            return
        
        self.Def_Settings()
        string_to_find = self.Sett + ".run_mode"
        self.Find_string(self.v_1, string_to_find)

        if not self.Insert_Header:
            qm = QMessageBox
            ret = qm.question(self, 'Warning', 'Run Mode already specified in the project !\nDo you really want to edit settings?', qm.Yes | qm.No)
            if ret == qm.No:
                self.Run_Mode_Extra(self.v_1)
            elif ret == qm.Yes:
                self.Insert_Settings()
        else:
            self.Find_string(self.plainTextEdit, string_to_find)
            if not self.Insert_Header:
                msg = 'Only one run mode is allowed in the project !'
                self.showDialog('Warning', msg)
                self.Run_Mode_Extra(self.plainTextEdit)
            else:
                self.Insert_Settings()

        #self.Run_Mode_CB.setCurrentIndex(0)
        self.Photon_CB.setChecked(False)
        self.Create_Separate_SRC_CB.setChecked(False)
        self.Create_Surface_SRC_CB.setChecked(False)
        try:
            self.Set_Tracks_ComboBoxes()
        except:
            return

    def Set_Tracks_ComboBoxes(self):
        # Set ComboBoxes for tracks recording
        self.Batch_List = []; self.Generation_List = []; self.Particle_List = []
        for i in reversed(range(self.Tracks_Grid_Lay.count())): 
            self.Tracks_Grid_Lay.itemAt(i).widget().setParent(None)
        batches = int(self.LineEdit_1.text())
        generations = int(self.LineEdit_5.text())
        particles = int(self.Particles_Number_LE.text())
        for batch in range(1, batches + 1):
            self.Batch_List.append(str(batch))
        for generation in range(1, generations + 1):
            self.Generation_List.append(str(generation))
        for particle in range(1, particles + 1):
            self.Particle_List.append(str(particle))
        self.Batch_Bins_comboBox = self.CheckableComboBox()
        self.Batch_Bins_comboBox.addItem('Check Batches')
        self.Batch_Bins_comboBox.addItems(self.Batch_List)
        self.Gen_Bins_comboBox = self.CheckableComboBox()
        self.Gen_Bins_comboBox.addItem('Check Generations')
        self.Gen_Bins_comboBox.addItems(self.Generation_List)
        self.Particle_Bins_comboBox = self.CheckableComboBox()
        self.Particle_Bins_comboBox.addItem('Check Particles')
        self.Particle_Bins_comboBox.addItems(self.Particle_List)
        self.Tracks_Grid_Lay.addWidget(self.Batch_Bins_comboBox)
        self.Tracks_Grid_Lay.addWidget(self.Gen_Bins_comboBox)
        self.Tracks_Grid_Lay.addWidget(self.Particle_Bins_comboBox)
        self.Batch_Bins_comboBox.model().item(0).setEnabled(False)
        self.Gen_Bins_comboBox.model().item(0).setEnabled(False)
        self.Particle_Bins_comboBox.model().item(0).setEnabled(False)        

    def Insert_Settings(self):
        if self.Run_Mode_CB.currentIndex() in [1, 2]:
            # Eigenvalue problem
            if self.Run_Mode_CB.currentIndex() == 1:
                print(self.Sett + ".run_mode = 'eigenvalue'")
                print(self.Sett + ".particles = " + str(self.Particles_Number_LE.text()))
                print(self.Sett + ".batches = " + str(self.LineEdit_1.text()))
                print(self.Sett + ".inactive = " + self.LineEdit_2.text())
                print(self.Sett + ".generations_per_batch = " + str(self.LineEdit_5.text()) + "\n")
            # Fixed source problem
            elif self.Run_Mode_CB.currentIndex() == 2:
                print(self.Sett + ".run_mode = 'fixed source'")
                print(self.Sett + ".particles = " + str(self.Particles_Number_LE.text()))
                print(self.Sett + ".batches = " + str(self.LineEdit_1.text()) + '\n')
                print(self.Sett + ".generations_per_batch = " + str(self.LineEdit_5.text()) + "\n")
        
            if self.Photon_CB.isChecked():
                print(self.Sett + ".photon_transport = True")
                if self.ttb_RB.isChecked():
                    print(self.Sett + ".electron_treatment = 'ttb'")
                elif self.led_RB.isChecked():
                    print(self.Sett + ".electron_treatment = 'led'")
            
            if self.Create_Separate_SRC_CB.isChecked():
                print(self.Sett + ".sourcepoint = {‘separate’: True}")
            
            if self.Create_Surface_SRC_CB.isChecked():
                self.LE_to_List1(self.LineEdit_4)
                Surfaces_List = str(self.List)
                print(self.Sett + ".surf_source_write = { 'surfaces_ids': " + Surfaces_List + ", 'max_particles': " + str(self.Particles_Max_LE.text()) +" }")
        
        self.Add_Tracks_PB.setEnabled(True)

    def is_float(self, value):
        try:
            x = float(value)
            return math.isfinite(x)
        except ValueError:
            return False

    def Add_CutOff(self):
        cutoff_string = self.Sett + ".cutoff = {}"
        weight_cutoff_string = ''
        energy_cutoff_string = ''
        time_cutoff_string = ''
        survival_normalization = False
        if self.W_CutOff_CB.currentIndex() != 0:
            W_cutoff_value = self.W_CutOff_LE.text()
            if W_cutoff_value == '' or not self.is_float(W_cutoff_value):
                self.showDialog('Warning', 'Weight cutoff value must be a valid float !')
                return
            else:
                weight_cutoff_string = f"{self.Sett}.cutoff['{self.W_CutOff_CB.currentText()}'] = {float(W_cutoff_value)}"
                if self.Survival_Norm_CB.isChecked():
                    survival_normalization = True
                    survival_normalization_string = f"{self.Sett}.cutoff['survival_normalization'] = True"

        if self.E_CutOff_CB.currentIndex() != 0:
            E_cutoff_value = self.E_CutOff_LE.text()
            if E_cutoff_value == '' or not self.is_float(E_cutoff_value):
                self.showDialog('Warning', 'Energy cutoff value must be a valid float !')
                return
            else:
                energy_cutoff_string = f"{self.Sett}.cutoff['{self.E_CutOff_CB.currentText()}'] = {float(E_cutoff_value)}"
      
        if self.T_CutOff_CB.currentIndex() != 0:
            T_cutoff_value = self.T_CutOff_LE.text()
            if T_cutoff_value == '' or not self.is_float(T_cutoff_value):
                self.showDialog('Warning', 'Time cutoff value must be a valid float !')
                return
            else:
                time_cutoff_string = f"{self.Sett}.cutoff['{self.T_CutOff_CB.currentText()}'] = {float(T_cutoff_value)}"
      
        if cutoff_string.strip() not in self.plainTextEdit.toPlainText().strip() and cutoff_string.strip() not in self.v_1.toPlainText().strip():
            print(cutoff_string)
        print(f"{weight_cutoff_string}")
        if survival_normalization:    
            print(survival_normalization_string)
        print(f"{energy_cutoff_string}")
        print(f"{time_cutoff_string}")

        self.W_CutOff_CB.setCurrentIndex(0)
        self.E_CutOff_CB.setCurrentIndex(0)
        self.T_CutOff_CB.setCurrentIndex(0)
        self.W_CutOff_LE.clear()
        self.E_CutOff_LE.clear()
        self.T_CutOff_LE.clear()

    def extract_lines_between_markers(self, document, start_str, end_str):
        result = []
        recording = False
        for line in document:
            if start_str in line:
                recording = True
            if recording:
                result.append(line)
            if end_str in line and recording:
                break
        return result
    
    def get_lines_with_string(self, document, search_string):
        for line in document:
            if search_string in line and line[0] != '#':
                matching_line = line
                break
            else:
                matching_line = ''
        return matching_line

    def Find_Run_Mode(self):
        document = self.v_1.toPlainText()
        if 'openmc.Settings' not in document:
            return        
        electron_treatment = 'ttb'
        Particle_type = 'neutron'
        cursor = self.plainTextEdit.textCursor()
        doc_lines = [line for line in document.split('\n') if line != '' and line[0] != '#']
        #Settings_Lines = [line for line in doc_lines if self.Sett + '.' in line]
        #Settings_Lines = self.extract_lines_between_markers(doc_lines, self.Sett, self.Sett + '.export_to_xml()')
        Settings_Lines = self.extract_lines_between_markers(doc_lines, 'openmc.Settings()', self.Sett + '.export_to_xml()')
        Source_Line = [line for line in doc_lines if 'openmc.Source' in line]
        if Source_Line:
            for line in Source_Line:
                line = line[line.find("(") + 1: line.find(")")].split(',')
                for item in line:
                    if 'particle' in item:
                        Particle_type = item.split('=')[1].strip()
        else:
            Particle_type = 'neutron'
        run_mode = ''
        if Settings_Lines:
            if '.run_mode' in '\n'.join(Settings_Lines):
                matching_line = self.get_lines_with_string(Settings_Lines, '.run_mode')
                if matching_line:
                    run_mode = matching_line.split('=')[1].strip()
                    if 'fixed source' in run_mode:
                        self.Run_Mode_CB.setCurrentIndex(2)
                    elif 'eigenvalue' in run_mode:
                        self.Run_Mode_CB.setCurrentIndex(1)
            else:
                if 'VolumeCalculation' in '\n'.join(Settings_Lines):
                    self.Run_Mode_CB.setCurrentIndex(3)
                else:
                    if Particle_type == 'neutron':
                        run_mode = 'eigenvalue'
                        self.Run_Mode_CB.setCurrentIndex(1)   # by default 'eigenvalue'
        
        if run_mode in ['eigenvalue', 'fixed source']:
            for line in Settings_Lines :
                if self.Sett + '.particles' in line.replace(" ", "").split('=')[0]:
                    self.particles = line.split('=')[1].strip()
                    #self.Particles_Number_LE.setText(str(self.particles))
                    self.Find_Settings_Parameters(Settings_Lines, self.Particles_Number_LE, self.particles)
                elif self.Sett + '.inactive' in line.replace(" ", "").split('=')[0]: 
                    self.Inactive_Found = True
                    self.inactives = line.split('=')[1].strip()
                    #self.LineEdit_2.setText(str(self.inactives))
                    self.Find_Settings_Parameters(Settings_Lines, self.LineEdit_2, self.inactives)
                elif self.Sett + '.batches' in line.replace(" ", "").split('=')[0]:                
                    self.batches = line.split('=')[1].strip()
                    #self.LineEdit_1.setText(str(self.batches))
                    self.Find_Settings_Parameters(Settings_Lines, self.LineEdit_1, self.batches)
                elif self.Sett + '.generations_per_batch' in line.replace(" ", "").split('=')[0]: 
                    self.Generations_Found = True
                    self.generations = line.split('=')[1].strip()
                    #self.LineEdit_5.setText(str(self.generations))
                    self.Find_Settings_Parameters(Settings_Lines, self.LineEdit_5, self.generations)
                elif self.Sett + '.photon_transport' in line.replace(" ", "").split('=')[0]:
                    photon_transport = line.split('=')[1].strip()
                    if 'True' in line: 
                        self.Photon_CB.setChecked(True)
                    else:
                        self.Photon_CB.setChecked(False)
                        self.ttb_RB.setEnabled(False)
                        self.led_RB.setEnabled(False)
                    """elif self.Sett + '.cutoff' in line.replace(" ", "").split('=')[0]:
                    if 'energy_photon' in line:
                        if '{' in line:
                            photon_cutoff = line.split(':')[1].replace('}', '').strip()
                        else:
                            photon_cutoff = line.strip().split('=')[1]
                        self.Find_Settings_Parameters(Settings_Lines, self.Photon_Cut, photon_cutoff)
                    if 'energy_neutron' in line:
                        if '{' in line:
                            neutron_cutoff = line.split(':')[1].replace('}', '').strip()
                        else:
                            neutron_cutoff = line.strip().split('=')[1]
                        self.Find_Settings_Parameters(Settings_Lines, self.Neutron_Cut, neutron_cutoff)"""
                elif self.Sett + '.electron_treatment' in line.replace(" ", "").split('=')[0]:
                    electron_treatment = line.split('=')[1].strip()
                        
            if 'ttb' in electron_treatment: 
                self.ttb_RB.setChecked(True)
            else:
                self.led_RB.setChecked(True)
            
            try:
                self.Set_Tracks_ComboBoxes()
            except:
                return

            self.Add_Tracks_PB.setEnabled(True)

    def Find_Settings_Parameters(self, lines, LE, parameter):
        if parameter.isdigit():
            LE.setText(str(parameter))
        else:
            for line in lines:
                if parameter == line.split('=')[0].strip():
                    parameter = line.split('=')[1].strip()
                    break
            LE.setText(str(parameter))

    def parse_list(self, text):
        separators = [' ', ',', ';', ':']
        for sep in separators:
            text = text.replace(sep, ' ')
        
        parts = text.split()
        values = []

        for part in parts:
            values.append([Expression(part)][0])
        return values
    
    def parse_pi_expression(self, expr):
        """Parse expressions containing pi safely, including scientific notation."""
        if isinstance(expr, (int, float)):
            return float(expr)

        expr = str(expr).strip().lower()
        expr = expr.replace(' ', '')

        # Handle scientific notation FIRST (before other processing)
        # Convert 1e-5 to 0.00001, 1.2e-3 to 0.0012, etc.
        def convert_scientific(match):
            num = match.group(0)
            try:
                return str(float(num))
            except:
                return num
        
        # Match scientific notation patterns like 1e-5, 1.2e-3, 1E-5
        expr = re.sub(r'(\d+\.?\d*)[eE][+-]?\d+', convert_scientific, expr)

        # Insert implicit multiplication (now works after scientific notation is converted)
        expr = re.sub(r'(\d)(pi)', r'\1*pi', expr)
        expr = re.sub(r'(pi)(\d)', r'pi*\2', expr)

        # Normalize leading zeros in numbers
        def normalize_number(match):
            num = match.group(0)
            if '.' in num:
                return str(float(num))
            return str(int(num))

        expr = re.sub(r'\d+\.?\d*', normalize_number, expr)

        # Allow only safe characters (now including 'e' for scientific notation)
        if not re.fullmatch(r'[0-9pi\.\+\-\*/\(\)eE]*', expr):
            raise ValueError(f"Invalid expression: {expr}")

        safe_dict = {
            "__builtins__": {},
            "pi": math.pi
        }

        try:
            return float(eval(expr, safe_dict, {}))
        except Exception as e:
            raise ValueError(f"Cannot parse '{expr}': {e}")
    
    def parse_pi_expression2(self, expr):
        """Parse expressions containing pi safely."""

        if isinstance(expr, (int, float)):
            return float(expr)

        expr = str(expr).strip().lower()
        expr = expr.replace(' ', '')

        # Insert implicit multiplication
        expr = re.sub(r'(\d)(pi)', r'\1*pi', expr)
        expr = re.sub(r'(pi)(\d)', r'pi*\2', expr)

        # Normalize leading zeros in numbers
        def normalize_number(match):
            num = match.group(0)

            # Preserve decimal numbers
            if '.' in num:
                return str(float(num))

            return str(int(num))

        expr = re.sub(r'\d+\.?\d*', normalize_number, expr)

        # Allow only safe characters
        if not re.fullmatch(r'[0-9pi\.\+\-\*/\(\)]*', expr):
            raise ValueError(f"Invalid expression: {expr}")

        safe_dict = {
            "__builtins__": {},
            "pi": math.pi
        }

        try:
            return float(eval(expr, safe_dict, {}))
        except Exception as e:
            raise ValueError(f"Cannot parse '{expr}': {e}")

    def parse_pi_expression1(self, expr):
        """Robust parser for pi expressions"""
        if isinstance(expr, (int, float)):
            return float(expr)
        
        expr_str = str(expr).lower().replace(' ', '')
        
        # Handle cases like '2pi' -> '2*pi'
        expr_str = re.sub(r'(\d+)pi', r'\1*pi', expr_str)
        
        # Handle cases like 'pi2.5' -> 'pi*2.5' (though this is unusual)
        expr_str = re.sub(r'pi(\d+\.?\d*)', r'pi*\1', expr_str)
        
        # Replace pi with np.pi
        expr_str = expr_str.replace('pi', 'np.pi')
        
        try:
            # Evaluate safely
            result = eval(expr_str, {"np": np, "__builtins__": {}})
            return float(result)
        except:
            try:
                return float(expr)
            except:
                raise ValueError(f"Cannot parse: {expr}")

    def format_list_without_quotes(self, lst):
        # Return a string representation of a list without quotes
        return '[' + ', '.join(str(item) for item in lst) + ']'
    
    def Sorting(self, List):
        List = sorted(List, key=lambda pair: self.parse_pi_expression(pair))
        List = [e.replace('pi', 'np.pi') if 'np.pi' not in str(e) and 'pi' in str(e) else e for e in List]
        return List

    def Replace_PI_N(self, e):
        if 'pi' in e and e != 'pi' and e != '-pi':  # replace 2pi or pi2 by 2*pi
            if "*" not in e:
                if "/" in e : 
                    try:
                        if isinstance(float(re.sub(r'[pi]', '', e.split('pi')[0])), (int, float)):
                            e = re.sub(r'[pi]', '', e) + "*pi"
                    except:
                        pass
                else:
                    try:
                        if isinstance(float(re.sub(r'[pi]', '', e)), (int, float)):
                            e = re.sub(r'[pi]', '', e) + "*pi"
                    except:
                        pass

            elif '*' in e:   # replace pi*2 by 2*pi
                try:
                    if isinstance(float(re.sub(r'[pi*]', '', e)), (int, float)):
                        e = re.sub(r'[pi*]', '', e) + "*pi"
                    elif isinstance(float(re.sub(r'[pi]', '', e)), (int, float)):
                        e = re.sub(r'[pi]', '', e) + "*pi"
                except:
                    pass
        return e

    def LE_to_List(self, LineEdit1, LineEdit2, X, Y):
        text1 = LineEdit1.text().replace('np.', '')
        text2 = LineEdit2.text()
        if '[' in text1 and ']' in text1:
            text1 = text1.strip('[]')   
        else:
            text1 = text1.replace('[', '').replace(']', '')
        if '[' in text2 and ']' in text2:
            text2 = text2.strip('[]')   
        else:
            text2 = text2.replace('[', '').replace(']', '')
        for separator in [',', ';', ':', ' ']:
            if separator in text1:
                text1 = str(' '.join(text1.replace(separator, ' ').split()))
        for separator in [',', ';', ':', ' ']:
            if separator in text2:
                text2 = str(' '.join(text2.replace(separator, ' ').split()))
        List1 = self.parse_list(text1)
        List2 = self.parse_list(text2)
        X_Length = len(List1)
        P_Length = len(List2)

        if X_Length != P_Length:
            print('# Lists {X} and {Y} in the line below must be the same length. Check the entered data !')
            
        if sum([float(P) for P in List2]) != 1.:
            print('# Warning', 'Probability is not normalized to 1. Check the entered data in the line below!')
        
        # Sort with the fixed parser
        paired = sorted(zip(List1, List2), key=lambda pair: self.parse_pi_expression(pair[0]))
        x_sorted, y_sorted = zip(*paired)
        x_sorted = list(x_sorted)
        y_sorted = list(y_sorted)

        for e in x_sorted:
            if 'pi' in e and "/" not in e and e != 'pi' and e != '-pi' and "*" not in e:
                try:
                    if isinstance(float(re.sub(r'[pi*]', '', e)), (int, float)):
                        index = x_sorted.index(e)
                        e = re.sub(r'[pi]', '', e) + "*pi"
                        x_sorted[index] = e
                except ValueError:
                    print("# Error in iterable object !")
            elif 'pi*' in e:
                try:
                    if isinstance(float(re.sub(r'[pi*]', '', e)), (int, float)):
                        index = x_sorted.index(e)
                        e = re.sub(r'[pi*]', '', e) + "*pi"
                        x_sorted[index] = e
                except ValueError:
                    print("# Error in iterable object !")

        for e in x_sorted:
            if 'pi' not in e:
                index = x_sorted.index(e)
                e = float(e)
                x_sorted[index] = str(e)

        x_sorted = [e.replace('pi', 'np.pi')for e in x_sorted]
        y_sorted = [float(e) for e in y_sorted]

        LineEdit1.setText(re.sub(r'["\']', '', str(x_sorted)))
        LineEdit2.setText(re.sub(r'["\']', '', str(y_sorted)))

        if len(x_sorted) >= 5:
            print(f"{X} = {self.format_list_without_quotes(x_sorted)}")
            print(f"{Y} = {self.format_list_without_quotes(y_sorted)}")

        return x_sorted, y_sorted

    def LE_to_List1(self, LineEdit):
        text = LineEdit.text()
        for separator in [',', ';', ':', ' ']:
            if separator in text:
                text = str(' '.join(text.replace(separator, ' ').split()))
        self.List = text.split() #str(text.split(separator)).replace("'", '')
        return self.List

    def LE_to_List2(self, LineEdit):
        text = LineEdit.text()
        for separator in [',', ';', ':', ' ']:
            if separator in text:
                text = str(' '.join(text.replace(separator, ' ').split()))
        self.List = [float(w) for w in text.split()]
        return self.List

    def Suppress_Line(self, item, TextEdit):
        text = TextEdit.toPlainText()
        TextEdit.clear()
        for l in text.split('\n'):
            if item in l:
                Line = l
                text = text.replace(l, '')
                _list = text.split('\n')
                _list = [ i for i in _list if i ]
                text = '\n'.join(_list)
                cursor = TextEdit.textCursor()
                cursor.insertText(text)
                cursor = self.v_1.textCursor()
                cursor.setPosition(0)
                cursor.insertText(Line + '\n')

    def Run_Mode_Extra(self, Document):
        if self.Create_Separate_SRC:
            self.Find_string(Document, self.Sett + ".sourcepoint")
            if self.Insert_Header:
                print(self.Sett + ".sourcepoint = {‘separate’: True}")
        if self.Create_Surface_SRC:
            self.Find_string(Document, self.Sett + ".surf_source_write")
            if self.Insert_Header:
                print(self.Sett + ".surf_source_write = { 'surfaces_ids': " + str(
                    self.LineEdit_4.text()) + ", 'max_particles': " + str(self.Particles_Max_LE.text()) + " }")
        if self.Photon_CB.isChecked():
            self.Find_string(Document, self.Sett + ".photon_transport")
            if self.Insert_Header:
                print(self.Sett + ".photon_transport = True")
                if self.ttb_RB.isChecked():
                    print(self.Sett + ".electron_treatment = 'ttb'")
                elif self.led_RB.isChecked():
                    print(self.Sett + ".electron_treatment = 'led'")
            else:
                self.Find_string(Document, self.Sett + ".electron_treatment")
                if self.Insert_Header:
                    if self.ttb_RB.isChecked():
                        print(self.Sett + ".electron_treatment = 'ttb'")
                    elif self.led_RB.isChecked():
                        print(self.Sett + ".electron_treatment = 'led'")
        else:
            Doc = Document.toPlainText()
            lines = [line for line in Doc.split('\n') if line != '' and line[0] != '#']
            for line in lines:
                if ".photon_transport" in line:
                    Doc = Doc.replace(line, '')
                elif ".cutoff" in line:
                    Doc = Doc.replace(line, '')
                elif ".electron_treatment" in line:
                    Doc = Doc.replace(line, '')
            Document.clear()
            cursor = Document.textCursor()
            cursor.insertText(Doc)

    def Volume_Calculation(self):
        self.Import_OpenMC()
        # Volume calculation
        if self.Volume_Calc_CB.currentIndex() == 0:
            self.showDialog('Warning', 'Select Volume Calculation option first !')
            return
        
        self.Insert_Header = True
        self.Def_Settings()
        if self.Volume_Calc_CB.currentIndex() != 0:
            if self.LineEdit_3.text() == '':
                self.showDialog('Warning', 'Choose domains first !')
                return
            self.Find_string(self.v_1, 'eigenvalue')
            if not self.Insert_Header:
                self.showDialog('Warning', 'Could not be added, Eigenvalue Mode already specified in the project !')
                return
            else:
                self.Find_string(self.v_1, 'fixed source')
                if not self.Insert_Header:
                    self.showDialog('Warning', 'Could not be added, Fixed-source Mode already specified in the project !')
                    return
                else:
                    self.Find_string(self.plainTextEdit, 'eigenvalue')
                    if not self.Insert_Header:
                        self.showDialog('Warning', 'Only one run mode is allowed in the project !')
                        return
                    else:
                        self.Find_string(self.plainTextEdit, 'fixed source')
                        if not self.Insert_Header:
                            self.showDialog('Warning', 'Only one run mode is allowed in the project !')
                            return
                        else:
                            string_to_find = self.Sett + ".volume_calculations"
                            self.Find_string(self.plainTextEdit, string_to_find)
                            if self.Insert_Header:
                                self.Find_string(self.v_1, string_to_find)
                                if self.Insert_Header:
                                    if '# Volume calculation mode' not in self.v_1.toPlainText():
                                        print('# Volume calculation mode')
                                    self.Insert_Header = False
                                else:
                                    string_to_find = 'openmc.VolumeCalculation'
                                    self.Find_string(self.v_1, string_to_find)
                                    self.Delete_lines(self.v_1, string_to_find, False)
                                    self.Delete_lines(self.v_1, self.Sett + '.volume_calculations', True)
                                    for item in self.list_of_items:
                                        self.vol_calcs.append(item)
                            samples = str(self.Particles_Number_LE.text())
                            if self.LL_CheckB.isChecked():
                                Lower_Left = ", lower_left = " + str(self.LineEdit_5.text())
                                Upper_Right = ", upper_right = " + str(self.LineEdit_2.text())
                            elif self.GeomBound_CheckB.isChecked():
                                Lower_Left = ", lower_left = " +  self.Geom + '.bounding_box[0]'
                                Upper_Right = ", upper_right = " +  self.Geom + '.bounding_box[1]'
                            else:
                                Lower_Left = ''
                                Upper_Right = ''

                            if self.Volume_Calc_CB.currentIndex() in [1, 3, 4]:     # Vol_Calc: Specific cells or Materials or Universes
                                if self.Volume_Calc_CB.currentIndex() == 3:
                                    if not self.LL_CheckB.isChecked() and not self.GeomBound_CheckB.isChecked():
                                        self.showDialog('Warning', 'Could not automatically determine bounding box for stochastic volume calculation !'+
                                                        '\nCheck Lower Left, Upper Right case or Geometry boundings case!')
                                        return
                                self.vol_calcs.append('openmc.VolumeCalculation(' + self.LineEdit_3.text() + ", " + samples +
                                                            Lower_Left + Upper_Right + ')')
                            elif self.Volume_Calc_CB.currentIndex() == 2:     # Vol_Calc: Geometry cells
                                self.vol_calcs.append('openmc.VolumeCalculation([eval(cell.name.strip()) for cell in ' + self.Geom + ".get_all_cells().values()], " + samples + 
                                                            Lower_Left + Upper_Right + ')')
                            self.Find_string(self.plainTextEdit, 'openmc.VolumeCalculation')
                            
                            if not self.Insert_Header:
                                self.Delete_lines(self.plainTextEdit, 'openmc.VolumeCalculation', False)
                                self.plainTextEdit.moveCursor(QtGui.QTextCursor.Start)
                                cursor = QtGui.QTextCursor(self.plainTextEdit.document().findBlockByLineNumber(self.pos))
                                self.plainTextEdit.setTextCursor(cursor)
                                for i, item in enumerate(self.vol_calcs):
                                    if i:
                                        print(',')
                                    print(item, end='')
                                print(" ]")
                            else:
                                print('vol_calcs = [')
                                for i, item in enumerate(self.vol_calcs):
                                    if i:
                                        print(',')
                                    print('\t' + item, end='')
                                print(" ]")
                                print(self.Sett + ".volume_calculations = vol_calcs")
                            if self.Vol_Trigger_CB.isChecked():
                                if self.Vol_Trigger_value_CB.currentIndex() == 0:
                                    self.showDialog('Warning', 'Select threshold value !')
                                    return
                                if self.Vol_Trigger_type_CB.currentIndex() == 0:
                                    self.showDialog('Warning', 'Select statistical quantity to apply threshold on !')
                                    return
                                print('for vol_calc in vol_calcs:')
                                print('\tvol_calc.set_trigger(' + self.Vol_Trigger_value_CB.currentText() + ', ' + self.Vol_Trigger_type_CB.currentText() +')')

        self.Volume_Calc_CB.setCurrentIndex(0)
        self.Cells_CB.hide()
        self.LineEdit_3.hide()

    def Delete_lines(self, text_window, key, clear_flag):
        lines = text_window.toPlainText().split('\n')
        self.pos = 0
        key0 = key
        for i, w in reversed(list(enumerate(lines))):
            #print(i, w)
            if key in w:
                if clear_flag:
                    key = lines[i].split('=')[1].replace(' ', '')
                    key.strip()
                    clear_flag = False
                self.pos = i
                del lines[i]

        text_window.clear()
        cursor = text_window.textCursor()
        text_window.setTextCursor(cursor)
        for i, line in enumerate(lines):
            text_window.insertPlainText(line + '\n')

    def question(self, alert, msg) :
        qm = QMessageBox
        ret = qm.question(self, alert, msg, qm.Yes | qm.No)
        if ret == qm.Yes:
            self.Close_Project()
            self.NewFiles()
        elif ret == qm.No:
            pass

    def Tracks_Settings(self):
        # /////////////////////////   Tracks Setting   /////////////////////////
        self.Tracks_List = []
        try:
            if self.Batch_Bins_comboBox.checkedItems():
                self.Checked_Batches = self.Batch_Bins_comboBox.checkedItems()
                if self.Gen_Bins_comboBox.checkedItems():
                    self.Checked_Generations = self.Gen_Bins_comboBox.checkedItems()
                    if self.Particle_Bins_comboBox.checkedItems():
                        self.Checked_Particles = self.Particle_Bins_comboBox.checkedItems()
                    else:
                        self.showDialog('Warning', 'Check one particle at least!')
                        return  
                else:
                    self.showDialog('Warning', 'Check one generation at least!')
                    return        
            else:
                self.showDialog('Warning', 'Check one batch at least!')
                return
            
            for Batch in self.Checked_Batches:
                for Generation in self.Checked_Generations:
                    for Particle in self.Checked_Particles:
                        self.Tracks_List.append((Batch, Generation, Particle,))
            print("\n" + self.Sett + ".track = " + str(self.Tracks_List))
        except:
            self.showDialog('Warning', 'No batch is defined for track recording!')

    def Keff_Trigger_Settings(self):
        # /////////////////////////   Trigger Setting   /////////////////////////
        self.Import_OpenMC()
        self.Find_string(self.v_1, "openmc.Settings")
        if self.Insert_Header:
            self.Find_string(self.plainTextEdit, "openmc.Settings")
            if self.Insert_Header:
                print(self.Settings_Header)
                print(self.Sett + " = openmc.Settings()\n")
            else:
                pass
        
        if self.Trigger_Active_CB.currentText() == 'True':
            if self.Trigger_max_batches_LE.text().isdigit():
                print(self.Sett + ".keff_trigger = {'type' : '" + self.Keff_Trigger_Type_CB.currentText() + \
                    "', 'threshold' : " + self.Keff_Trigger_Value_LE.text() + self.Threshold_CB.currentText() +'}')
                print(self.Sett + '.trigger_active = ' + self.Trigger_Active_CB.currentText())
                print(self.Sett + '.trigger_max_batches = ' + self.Trigger_max_batches_LE.text() + '\n')
                if self.Trigger_batch_interval_LE.text().isdigit():
                    print(self.Sett + '.trigger_batch_interval = ' + self.Trigger_batch_interval_LE.text())
            else:
                self.showDialog('Warning', 'Trigger needs maximum number of batches to be given as an integer!')
                return
        else:
            print(self.Sett + ".keff_trigger = {'type' : '" + self.Keff_Trigger_Type_CB.currentText() + \
            "', 'threshold' : " + self.Keff_Trigger_Value_LE.text() + self.Threshold_CB.currentText() +'}')

    def Entropy_Settings(self):
        # /////////////////////////   Entropy Setting   /////////////////////////
        if self.Entropy_type_CB.currentIndex() == 1:
            if self.X_LL_Entropy.text() and self.Y_LL_Entropy.text() and self.Y_LL_Entropy.text()\
                    and self.X_UR_Entropy.text() and self.Y_UR_Entropy.text() and self.Y_UR_Entropy.text()\
                    and self.Z_UR_Entropy.text() and self.X_dim.text() and self.Y_dim.text() and self.Z_dim.text():
                if float(self.X_LL_Entropy.text()) >= float(self.X_UR_Entropy.text()) or \
                        float(self.Y_LL_Entropy.text()) >= float(self.Y_UR_Entropy.text()) or \
                        float(self.Z_LL_Entropy.text()) >= float(self.Z_UR_Entropy.text()):
                    self.showDialog('Warning', 'Upper bound must be greater than lower bound. Check the entered data.')
                    return
                LL = str((self.X_LL_Entropy.text(), self.Y_LL_Entropy.text(), self.Z_LL_Entropy.text())).replace("'", "")
                UR = str((self.X_UR_Entropy.text(), self.Y_UR_Entropy.text(), self.Z_UR_Entropy.text())).replace("'","")
                dim = str((self.X_dim.text(), self.Y_dim.text(), self.Z_dim.text())).replace("'","")
                for item in self.Entropy_LE_List:
                    item.clear()
            else:
                ret = QMessageBox.question(self, 'Warning', 'All the fields must be filled or default data will be used. \
                                           \nThe default data may be incompatible with the model geometry!\nUse the default data ?')
                if ret == QMessageBox.Yes:
                    LL = "(-50, -50, -25))"
                    UR = "(50, 50, 25)"
                    dim = "(8, 8, 8)"
                elif ret == QMessageBox.No:
                    return

            print("\nentropy_mesh = openmc.RegularMesh()")
            print("entropy_mesh.lower_left = " + LL)
            print("entropy_mesh.upper_right = " + UR)
            print("entropy_mesh.dimension = " + dim)
            print(self.Sett + ".entropy_mesh = entropy_mesh\n")
        elif self.Entropy_type_CB.currentIndex() == 2:
            print("\nentropy_mesh = openmc.RegularMesh()")
            print("entropy_mesh.lower_left, entropy_mesh.upper_right = " + self.Geom + ".bounding_box")
            print("entropy_mesh.dimension = (8, 8, 8)")
            print(self.Sett + ".entropy_mesh = entropy_mesh\n")

        self.Entropy_type_CB.setCurrentIndex(0)

    def Entropy_Widgets_Status(self):
        if self.Entropy_type_CB.currentIndex() == 0:
            self.Add_Entropy_PB.setEnabled(False)
        else:
            self.Add_Entropy_PB.setEnabled(True)
            if self.Entropy_type_CB.currentIndex() == 1:
                for item in self.Entropy_LE_List:
                    item.setEnabled(True)
            else:
                for item in self.Entropy_LE_List:
                    item.clear()
                    item.setEnabled(False)
        

    def Def_Source_Settings(self):
        # /////////////////////////   Source Settings   /////////////////////////
        if self.One_Source_RB.isChecked():
            self.Num_of_Srcs_Label.setEnabled(False)
            self.Number_of_Sources.setEnabled(False)
            self.Uniform_Sampling_CB.setEnabled(False)
        else:
            self.Num_of_Srcs_Label.setEnabled(True)
            self.Number_of_Sources.setEnabled(True)
            self.Uniform_Sampling_CB.setEnabled(True)

        self.spatial = 'spatial' + self.Source_ID_LE.text()
        self.angle = 'angle' + self.Source_ID_LE.text()
        self.energy = 'energy' + self.Source_ID_LE.text()
        self.time = 'time' + self.Source_ID_LE.text()
        self.constraints = 'constraints' + self.Source_ID_LE.text()

        if self.Source_Type_CB.currentIndex() == 0:
            self.Particle_CB.setCurrentIndex(0)
            for w in [self.Add_Source_PB, self.Source_Geom_CB, self.Energy_Dist_CB, self.Direction_Dist_CB,
                      self.Time_Dist_CB, self.Use_Constraints_Checkbox]:
                w.setEnabled(False)
        else:
            self.Add_Source_PB.setEnabled(True)

    def Def_Source(self):
        Source_Keys = ['IndependentSource', 'FileSource', 'surf_source_read', 'CompiledSource']
        Space_Keys = ['Point', 'Box', 'CartesianIndependent', 'CylindricalIndependent', 'SphericalIndependent'] 
        Univariate_Keys = ['select option', 'Uniform', 'Discrete', 'Tabular']
        self.Source_Type_CB.addItem('Select type')
        self.Source_Type_CB.addItems(Source_Keys)
        self.Source_Geom_CB.addItem('Select distribution')
        self.Source_Geom_CB.addItems(Space_Keys)
        self.X_Dist_CB.addItems(Univariate_Keys)
        self.Y_Dist_CB.addItems(Univariate_Keys)
        self.Z_Dist_CB.addItems(Univariate_Keys)
        
        for w in [self.Add_Source_PB, self.Source_Geom_CB, self.Energy_Dist_CB, self.Direction_Dist_CB,
                  self.Time_Dist_CB, self.Use_Constraints_Checkbox]:
            w.setEnabled(False)
        
    def Def_Energy_Dist(self):
        self.Energy_Dist_CB.clear()
        self.Energy_Dist_CB.addItem('Select type')
        if self.Particle_CB.currentText() == 'neutron':
            self.Energy_Dist_CB.addItems(['discrete', 'uniform', 'powerlaw', 'maxwell', 'watt', 
                                          'normal', 'muir', 'tabular', 'legendre']) 
            item = self.Energy_Dist_CB.model().item(9)
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
        else:
            self.Energy_Dist_CB.addItems(['discrete', 'tabular'])

    def Def_Angle_Dist(self):
        self.Direction_Dist_CB.clear()
        self.Direction_Dist_CB.addItem('Select type')
        self.Direction_Dist_CB.addItems(['Isotropic', 'Monodirectional', 'UnitSphere', 'PolarAzimuthal'])

        self.Mu_Dist_CB.clear()
        #self.Mu_Dist_CB.addItem('Select type')
        self.Mu_Dist_CB.addItems(['Uniform', 'Discrete', 'Tabular', 'Normal'])

        self.Phi_Dist_CB.clear()
        #self.Phi_Dist_CB.addItem('Select type')
        self.Phi_Dist_CB.addItems(['Uniform', 'Discrete', 'Tabular', 'Normal'])

    def Def_Time_Dist(self):
        self.Time_Dist_CB.clear()
        self.Time_Dist_CB.addItem('Select type')
        self.Time_Dist_CB.addItems(['Uniform', 'Discrete'])

    def Def_Constraints(self):
        self.Add_Constraints_PB.setEnabled(False)
        Keys = ['Select type', 'domain_type', 'domain_ids', 'time_bounds', 'energy_bounds', 'fissionable', 'rejection_strategy']
        self.Constraints_CB.clear()
        self.Constraints_CB.addItems(Keys)

    """def Choose_Only_Fissionable(self):
        if self.Source_Geom_CB.currentIndex() == 2:
            if self.Particle_CB.currentText() == 'neutron':
                self.Only_Fissionable_CB.setEnabled(True)
            else:
                self.Only_Fissionable_CB.setEnabled(False)
            if self.Only_Fissionable_CB.isChecked():
                self.Only_Fissionable = True
            else:
                self.Only_Fissionable = False
        else:
            self.Only_Fissionable_CB.setEnabled(False)
            self.Only_Fissionable_CB.setChecked(False)
            self.Only_Fissionable = False"""

    def Create_Separate_Source(self):
        if self.Create_Separate_SRC_CB.isChecked():
            self.Create_Separate_SRC = True
        else:
            self.Create_Separate_SRC = False

    def Add_Surface_Source(self):
        if self.Create_Surface_SRC:
            self.list_of_surfaces.append(self.surface_name_list[self.Source_Surfaces_CB.currentIndex() - 1])
            self.list_of_surfaces_ids.append(self.surface_id_list[self.Source_Surfaces_CB.currentIndex()])
            self.LineEdit_4.setText(str(self.list_of_surfaces_ids).replace("'", ""))

    def Create_Surface_Source(self):
        if self.Create_Surface_SRC_CB.isChecked():
            self.Create_Surface_SRC = True
            self.Source_Surfaces_CB.show()
            self.LineEdit_4.show()
            self.label_11.show()
            self.Particles_Max_LE.show()
        else:
            self.Create_Surface_SRC = False
            self.Source_Surfaces_CB.hide()
            self.LineEdit_4.hide()
            self.label_11.hide()
            self.Particles_Max_LE.hide()

    def Def_Source_Spatial(self):
        Source_Keys = ['IndependentSource', 'FileSource', 'surf_source_read', 'CompiledSource']
        Space_Keys = ['Point', 'Box', 'CartesianIndependent', 'CylindricalIndependent', 'SphericalIndependent'] 

        if self.Source_Geom_CB.currentIndex() == 0:
            self.Add_space_PB.setEnabled(False)
        else:
            self.Add_space_PB.setEnabled(True)
        
        if self.Source_Type_CB.currentText() == 'IndependentSource':
            for LineEdit in [self.X_LL, self.Y_LL, self.Z_LL, self.X_UR, self.Y_UR, self.Z_UR]:
                LineEdit.clear()
            
            if self.Source_Geom_CB.currentText() in Space_Keys:
                self.Enable_SRC_ED_Widgets_Space()
            else:
                self.Disable_SRC_Widgets_Space()
            
            if self.Source_Geom_CB.currentText() == 'Point':                  #  Point Source
                for w in [self.label_12, self.X_Dist_CB, self.Y_Dist_CB, self.Z_Dist_CB]:
                        w.hide()
                for w in [self.X_UR, self.Y_UR, self.Z_UR, self.UR_label]:
                        w.setEnabled(False)
                for w in [self.X_LL, self.Y_LL, self.Z_LL]:
                        w.setText(str(0))
                self.LL_label.setText('Coordinates')
            elif self.Source_Geom_CB.currentText() == 'Box':                # Box
                for w in [self.X_UR, self.Y_UR, self.Z_UR, self.UR_label]:
                    w.setEnabled(True)
                self.LL_label.setText('Lower left')
                self.UR_label.setText('Upper right')
                self.label_12.hide()
                for combobox in [self.X_Dist_CB, self.Y_Dist_CB, self.Z_Dist_CB]:
                    combobox.hide()
            elif self.Source_Geom_CB.currentText() in Space_Keys[2:]:      # cartesian, spherical, cylindrical
                self.label_12.setEnabled(True)
                self.label_12.show()
                self.LL_label.setText('min/values')
                self.UR_label.setText('max/proba')
                for combobox in [self.X_Dist_CB, self.Y_Dist_CB, self.Z_Dist_CB]:
                    combobox.show()
                if self.Source_Geom_CB.currentText() in Space_Keys[3:]:    # spherical, cylindrical
                    self.Origin_Label.show()
                    self.Origin_Label.setText('Origin')
                    self.Origin_LE.show()
                    self.Origin_LE.clear()
                    self.Origin_LE.setText('0. ,0., 0.')
                    self.label_X_R.setText('R')
                    if self.Source_Geom_CB.currentText() == 'CylindricalIndependent':
                        self.label_Y_Theta.setText('Phi')
                        self.label_Z_phi.setText('Z')
                    if self.Source_Geom_CB.currentText() == 'SphericalIndependent':
                        self.label_Y_Theta.setText('Theta')
                        self.label_Z_phi.setText('Phi')
                    for combobox in [self.X_Dist_CB, self.Y_Dist_CB, self.Z_Dist_CB]:
                        combobox.view().setRowHidden(combobox.findText('Tabular'), True)

                if self.Source_Geom_CB.currentText() not in ['CylindricalIndependent', 'SphericalIndependent']:
                    self.label_X_R.setText('X')
                    self.label_Y_Theta.setText('Y')
                    self.label_Z_phi.setText('Z')
                    self.Origin_Label.hide()
                    self.Origin_LE.hide()
                    for combobox in [self.X_Dist_CB, self.Y_Dist_CB, self.Z_Dist_CB]:
                        combobox.view().setRowHidden(combobox.findText('Tabular'), False)

                for W in [self.label_X_R, self.label_Z_phi, self.LL_label, self.X_LL, self.Y_LL, self.Z_LL, 
                        self.UR_label, self.X_UR, self.Y_UR, self.Z_UR]:
                    W.setEnabled(True)

            for combobox in [self.X_Dist_CB, self.Y_Dist_CB, self.Z_Dist_CB]:
                combobox.setCurrentIndex(1)
        elif self.Source_Type_CB.currentText() in ['FileSource', 'surf_source_read']:
            self.src_filename = QtWidgets.QFileDialog.getOpenFileName(self, 'Open File', "~", "*.h5;; source*.h5;; surface*.h5")[0]
            if self.src_filename:
                self.Origin_Label.show()
                self.Origin_Label.setText('File')
                self.Origin_LE.show()
                if self.directory and self.directory in self.src_filename:
                    self.src_filename = self.src_filename.split('/')[-1]
                self.Origin_LE.setText(self.src_filename)
            else:
                self.Source_Geom_CB.setCurrentIndex(0)
        elif self.Source_Geom_CB.currentIndex() == ['CompiledSource']:
            self.src_filename = QtWidgets.QFileDialog.getOpenFileName(self, 'Open File', "~", "*.so;; libsource.so")[0]
            self.Origin_Label.show()
            self.Origin_LE.show()
            if self.src_filename:
                self.Origin_Label.setText('File')
                if self.directory and self.directory in self.src_filename:
                    self.src_filename = self.src_filename.split('/')[-1]
            else:
                self.src_filename = 'build/libsource.so'
            
            self.Origin_LE.setText(self.src_filename)

    def Def_Source_Energy(self):
        #['discrete', 'uniform', 'powerlaw', 'maxwell', 'watt', 'normal', 'muir', 'tabular'])  # , 'legendre', 'mixture'])
        self.Interpolate_CB.hide()
        self.Exponent_LE.hide()
        self.Import_Lists_PB.hide()
        self.label_25.hide()
        self.label_14.show()
        self.Proba_LE.show()
        self.Energy_LE.clear()
        self.Proba_LE.clear()

        if self.Energy_Dist_CB.currentIndex() == 0:
            self.Add_Energy_PB.setEnabled(False)
        else:
            self.Add_Energy_PB.setEnabled(True)

        for W in [self.Energy_LE, self.Proba_LE, self.label_13, self.label_14]:
            W.setEnabled(True)

        if self.Energy_Dist_CB.currentText() == 'discrete':  
            self.label_13.setText('Energy in eV')
            self.label_14.setText('Probability')
            self.Import_Lists_PB.show()
            for LE in [self.Energy_LE, self.Proba_LE]:
                LE.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=None, allow_negative=False, allow_pi=False))
        elif self.Energy_Dist_CB.currentText() == 'uniform':  
            self.label_13.setText('Lower bound')
            self.label_14.setText('Upper bound')
            for LE in [self.Energy_LE, self.Proba_LE]:
                LE.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=1, allow_negative=False, allow_pi=False))
        elif self.Energy_Dist_CB.currentText() == 'powerlaw':  
            self.label_25.show()
            self.Exponent_LE.show()
            self.label_13.setText('Lower bound')
            self.label_14.setText('Upper bound')
            self.label_25.setText('Exponent')
            for LE in [self.Energy_LE, self.Proba_LE]:
                LE.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=1, allow_negative=False, allow_pi=False))
            self.Exponent_LE.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=1, allow_negative=False, allow_pi=False))
        elif self.Energy_Dist_CB.currentText() == 'maxwell': 
            self.Proba_LE.hide()
            self.label_14.hide()
            self.label_13.setText('TM in eV')
            self.Energy_LE.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=1, allow_negative=False, allow_pi=False))
        elif self.Energy_Dist_CB.currentText() == 'watt': 
            self.label_13.setText('Param. a in eV')
            self.label_14.setText('Param. b in 1/eV')
            for LE in [self.Energy_LE, self.Proba_LE]:
                LE.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=1, allow_negative=False, allow_pi=False))
        elif self.Energy_Dist_CB.currentText() == 'normal': 
            self.label_13.setText('Mean value')
            self.label_14.setText('Standard dev.')
            for LE in [self.Energy_LE, self.Proba_LE]:
                LE.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=1, allow_negative=False, allow_pi=False))
        elif self.Energy_Dist_CB.currentText() == 'muir': 
            self.label_25.show()
            self.label_13.setText('Mean e0 in eV')
            self.label_14.setText('Mass ratio')
            self.label_25.setText('KT in eV')
            self.Exponent_LE.show()
            for LE in [self.Energy_LE, self.Proba_LE, self.Exponent_LE]:
                LE.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=1, allow_negative=False, allow_pi=False))
        elif self.Energy_Dist_CB.currentText() == 'tabular': 
            self.label_25.show()
            self.Interpolate_CB.clear()
            self.Interpolate_CB.addItems(['select option', 'histogram', 'linear-linear', 'linear-log', 'log-linear', 'log-log'])
            for i in [3, 4, 5]:
                item = self.Interpolate_CB.model().item(i)
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            self.label_13.setText('Energy in eV')
            self.label_14.setText('Probability')
            self.label_25.setText('Interpolation')
            self.Interpolate_CB.show()
            self.Interpolate_CB.setEnabled(True)
            self.Import_Lists_PB.show()
            for LE in [self.Energy_LE, self.Proba_LE]:
                LE.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=None, allow_negative=False, allow_pi=False))
        elif self.Energy_Dist_CB.currentText() == 'legendre': 
            self.Proba_LE.hide()
            self.label_14.hide()
            self.label_13.setText('List of coef.')

            """elif self.Energy_Dist_CB.currentText() == 'mixture': 
                pass
            """
        else:
            self.Proba_LE.show()
            self.label_14.show()
            self.label_13.setText('Energy in eV')
            self.label_14.setText('Probability')
    
    def Def_Source_Time(self):
        if self.Time_Dist_CB.currentIndex() == 0:
            self.Add_Time_PB.setEnabled(False)
        else:
            self.Add_Time_PB.setEnabled(True)

        for W in [self.label_33, self.label_34, self.Time_LBound_LE, self.Time_UBound_LE]:
            W.setEnabled(True)

        if self.Time_Dist_CB.currentText() == 'Discrete':  
            self.label_33.setText('Time in s')
            self.label_34.setText('Probability')
            for LE in [self.Time_LBound_LE, self.Time_UBound_LE]:
                LE.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=None, allow_negative=False, allow_pi=False))
                LE.setToolTip("Only one float number is accepted")
        elif self.Time_Dist_CB.currentText() == 'Uniform':  
            self.label_33.setText('Lower bound')
            self.label_34.setText('Upper bound')
            for LE in [self.Time_LBound_LE, self.Time_UBound_LE]:
                LE.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=1, allow_negative=False, allow_pi=False))
                LE.setToolTip("A list of float numbers is accepted")

    def Def_Source_Constraints(self):
        if self.Constraints_CB.currentIndex() == 0:
            self.Add_Constraints_PB.setEnabled(False)
        else:
            self.Add_Constraints_PB.setEnabled(True)

    def Import_x_y_Lists(self, line1, line2):
        if self.Energy_Dist_CB.currentText() in ['discrete', 'tabular']:
            file = QtWidgets.QFileDialog.getOpenFileName(self, 'Open File', "~", "*;; *.inp;; *.dat;; *.txt")[0]
        if file:
            f = open(file, "r")
            lines = f.readlines()
            x = []; y = []
            line_num = 0
            for line in lines:
                line_num += 1
                # Skip empty lines and comments
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                # Split using multiple delimiters: comma, colon, semicolon, or whitespace
                # \s+ matches any whitespace (spaces, tabs)
                parts = re.split(r'[,:;\s]+', line.strip())
                # Filter out empty strings that might result from multiple delimiters
                parts = [part for part in parts if part]

                if len(parts) < 2:
                    print(f"Warning: Line {line_num} has less than 2 values: '{line}'")
                    continue
                
                try:
                    x.append(float(parts[0]))
                    y.append(float(parts[1]))
                except ValueError:
                    print(f"Warning: Line {line_num} contains non-numeric values: '{line}'")
                    continue
                
            f.close()
            # check if x is sorted
            x, y = self.sort_x_and_reorder_y(x, y)
            line1.setText(str(x)[str(x).find("[") + 1: str(x).find("]")])  
            line2.setText(str(y)[str(y).find("[") + 1: str(y).find("]")])  

    def sort_x_and_reorder_y(self, x, y):
        """
        If x is not sorted, sort x and reorder y to maintain x-y pairs.
        Args:
            x: List of x values
            y: List of y values
        Returns:
            sorted_x, sorted_y (new lists, original lists not modified)
        """
        """if len(x) != len(y):
            raise ValueError(f"Lists must have same length. x: {len(x)}, y: {len(y)}")"""
        
        # Check if x is already sorted
        if all(a <= b for a, b in zip(x, x[1:])):
            return x.copy(), y.copy()  # Return copies to be consistent
        
        # Sort based on x values while keeping y paired
        paired = list(zip(x, y))
        paired.sort(key=lambda pair: pair[0])  # Sort by x value
        
        # Unzip back to separate lists
        sorted_x, sorted_y = zip(*paired)
        
        return list(sorted_x), list(sorted_y)

    def Disable_SRC_Widgets_Space(self):
        for label in [self.label_X_R, self.label_Y_Theta, self.label_Z_phi, self.label_12, self.LL_label, self.UR_label]:
            label.setEnabled(False)
        for lineedit in [self.X_LL, self.Y_LL, self.Z_LL, self.X_UR, self.Y_UR, self.Z_UR]:
            lineedit.setEnabled(False)
        for combobox in [self.X_Dist_CB, self.Y_Dist_CB, self.Z_Dist_CB]:
            combobox.setEnabled(False)

    def Enable_SRC_ED_Widgets_Space(self):
        for label in [self.label_X_R, self.label_Y_Theta, self.label_Z_phi, self.label_12, self.LL_label, self.UR_label]:
            label.setEnabled(True)
        for lineedit in [self.X_LL, self.Y_LL, self.Z_LL, self.X_UR, self.Y_UR, self.Z_UR]:
            lineedit.setEnabled(True)
        for combobox in [self.X_Dist_CB, self.Y_Dist_CB, self.Z_Dist_CB]:
            combobox.setEnabled(True)

    def Disable_SRC_Widgets(self):
        for label in [self.label_X_R, self.label_Y_Theta, self.label_Z_phi, self.label_12, self.LL_label, self.UR_label,
                      self.label_10, self.label_13, self.label_14, self.label_20, self.label_21, self.label_28, 
                      self.label_29, self.label_32, self.label_33, self.label_34, self.label_35, self.label_36]:
            label.setEnabled(False)
        for lineedit in [self.X_LL, self.Y_LL, self.Z_LL, self.X_UR, self.Y_UR, self.Z_UR, self.Energy_LE,
                         self.Proba_LE, self.Mu_Min_LE, self.Phi_Min_LE, self.Mu_Max_LE, self.Phi_Max_LE,
                         self.UVW_LE, self.VWU_LE, self.Time_LBound_LE, self.Time_UBound_LE,
                         self.Constraints_LB_LE, self.Constraints_UB_LE]:
            lineedit.setEnabled(False)
        for combobox in [self.X_Dist_CB, self.Y_Dist_CB, self.Z_Dist_CB, self.Interpolate_CB, self.Ref_UVW_CB, 
                         self.Ref_UVW_CB, self.Ref_VWU_CB, self.Mu_Dist_CB, self.Phi_Dist_CB, self.Constraints_CB]:
            combobox.setEnabled(False)

    def Enable_SRC_ED_Widgets1(self):
        for label in [self.label_10, self.label_13, self.label_14, self.label_20, self.label_21]:
            label.setEnabled(True)
        for lineedit in [self.Energy_LE, self.Proba_LE, self.Mu_Min_LE, self.Phi_Min_LE, self.Mu_Max_LE, self.Phi_Max_LE]:
            lineedit.setEnabled(True)
        for combobox in [self.Energy_Dist_CB, self.Interpolate_CB, self.Direction_Dist_CB, self.Ref_UVW_CB, self.Mu_Dist_CB, self.Phi_Dist_CB]:
            combobox.setEnabled(True)

    def Enable_SRC_ED_Widgets(self):
        for combobox in [self.Energy_Dist_CB, self.Direction_Dist_CB]:
            combobox.setEnabled(True)

    def Def_Source_Spatial_Dist_X(self):
        if self.X_Dist_CB.currentText() in ['Discrete', 'Tabular']:        # discrete and tabular
            if self.Source_Geom_CB.currentText() in ['CylindricalIndependent', 'SphericalIndependent']:
                #self.X_LL.setValidator(self.float_validator_list)     
                self.X_LL.setValidator(UniversalNumericListValidator(
                        schema=("float",), max_items=None, allow_negative=False, allow_pi=False))      # R values
            else:
                self.X_LL.setValidator(UniversalNumericListValidator(
                        schema=("float",), max_items=None, allow_negative=True, allow_pi=False))      # X values

            #self.X_UR.setValidator(self.float_validator_list_positif)   
            self.X_UR.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=None, allow_negative=False, allow_pi=False))      # proba
        else:                                                               # Uniform
            if self.Source_Geom_CB.currentText() in ['CylindricalIndependent', 'SphericalIndependent']:
                #self.X_LL.setValidator(self.Dblevalidator)    
                self.X_LL.setValidator(UniversalNumericListValidator(
                        schema=("float",), max_items=1, allow_negative=False, allow_pi=False))         # R min
            else:
                self.X_LL.setValidator(UniversalNumericListValidator(
                        schema=("float",), max_items=1, allow_negative=True, allow_pi=False))         # X min

            if self.Source_Geom_CB.currentText() in ['CylindricalIndependent', 'SphericalIndependent']:
                self.X_UR.setValidator(UniversalNumericListValidator(
                        schema=("float",), max_items=1, allow_negative=False, allow_pi=False))         # R max
            else:
                self.X_UR.setValidator(UniversalNumericListValidator(
                        schema=("float",), max_items=1, allow_negative=True, allow_pi=False))         # X max

    def Def_Source_Spatial_Dist_Y(self):
        if self.Y_Dist_CB.currentText() in ['Discrete', 'Tabular']:         # discrete and tabular 
            if self.Source_Geom_CB.currentText() in ['CylindricalIndependent', 'SphericalIndependent']:
                #self.Y_LL.setValidator(self.float_validator_list_pi)
                self.Y_LL.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=None, allow_negative=True, allow_pi=True))        # Theta values
            else:    
                #self.Y_LL.setValidator(self.float_validator_list)           
                self.Y_LL.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=None, allow_negative=True, allow_pi=False))        # Y values
            #self.Y_UR.setValidator(self.float_validator_list_positif)       
            self.Y_UR.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=None, allow_negative=False, allow_pi=False))        # proba
        else:                                               # uniform
            if self.Source_Geom_CB.currentText() in ['CylindricalIndependent', 'SphericalIndependent']:
                #self.Y_LL.setValidator(self.float_validator_pi)     # min
                self.Y_LL.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=1, allow_negative=True, allow_pi=True))        # Theta min
                #self.Y_UR.setValidator(self.float_validator_pi)     # max
                self.Y_UR.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=1, allow_negative=True, allow_pi=True))        # Theta max
            else:
                #self.Y_LL.setValidator(self.Dblevalidator)    # min
                self.Y_LL.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=1, allow_negative=True, allow_pi=False))        # Y min
                #self.Y_UR.setValidator(self.Dblevalidator)    # max
                self.Y_UR.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=1, allow_negative=True, allow_pi=False))        # Y max

    def Def_Source_Spatial_Dist_Z(self):
        if self.Z_Dist_CB.currentText() in ['Discrete', 'Tabular']:         # discrete and tabular 
            if self.Source_Geom_CB.currentText() in ['CylindricalIndependent', 'SphericalIndependent']:
                #self.Z_LL.setValidator(self.float_validator_list_pi)
                self.Z_LL.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=None, allow_negative=True, allow_pi=True))        # Phi values
            else:    
                #self.Z_LL.setValidator(self.float_validator_list)           
                self.Z_LL.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=None, allow_negative=True, allow_pi=False))        # Z values
            #self.Z_UR.setValidator(self.float_validator_list_positif)       
            self.Z_UR.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=None, allow_negative=False, allow_pi=False))        # proba
        else:                                               # uniform
            if self.Source_Geom_CB.currentText() in ['CylindricalIndependent', 'SphericalIndependent']:
                #self.Z_LL.setValidator(self.float_validator_pi)     # min
                self.Z_LL.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=1, allow_negative=True, allow_pi=True))        # Phi min
                #self.Z_UR.setValidator(self.float_validator_pi)     # max
                self.Z_UR.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=1, allow_negative=True, allow_pi=True))        # Phi max
            else:
                #self.Z_LL.setValidator(self.Dblevalidator)    # min
                self.Z_LL.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=1, allow_negative=True, allow_pi=False))        # Z min
                #self.Z_UR.setValidator(self.Dblevalidator)    # max
                self.Z_UR.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=1, allow_negative=True, allow_pi=False))        # Z max

    def Def_Source_Angle_Dist_Mu(self):
        self.Mu_Interp_CB.clear()
        self.Mu_Interp_CB.addItems(['select interpolation', 'histogram', 'linear-linear'])

        if self.Mu_Dist_CB.currentText() == 'Uniform':                  # uniform
            #self.Mu_Min_LE.setValidator(self.Dblevalidator)    # min
            self.Mu_Min_LE.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=1, allow_negative=True, allow_pi=False))        # min
            #self.Mu_Max_LE.setValidator(self.Dblevalidator)    # max
            self.Mu_Max_LE.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=1, allow_negative=True, allow_pi=False))        # min

        elif self.Mu_Dist_CB.currentText() in ['Discrete', 'Tabular']:  # discrete, Tabular
            #self.Mu_Min_LE.setValidator(self.float_validator_list)           # values
            self.Mu_Min_LE.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=None, allow_negative=True, allow_pi=False))        # values
            #self.Mu_Max_LE.setValidator(self.float_validator_list_positif)   # proba
            self.Mu_Max_LE.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=None, allow_negative=False, allow_pi=False))        # proba

        if self.Mu_Dist_CB.currentText() == 'Tabular':
            self.Mu_Interp_CB.setEnabled(True)
        else:
            self.Mu_Interp_CB.setEnabled(False)

    def Def_Source_Angle_Dist_Phi(self):
        self.Phi_Interp_CB.clear()
        self.Phi_Interp_CB.addItems(['select interpolation', 'histogram', 'linear-linear'])
        #self.UVW_LE.setValidator(self.float_validator_list)
        self.UVW_LE.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=None, allow_negative=True, allow_pi=False))
        if self.Phi_Dist_CB.currentText() == 'Uniform':                    # uniform
            self.Phi_Min_LE.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=1, allow_negative=True, allow_pi=True))    # min
            #.setValidator(self.float_validator_pi)                     
            self.Phi_Max_LE.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=1, allow_negative=True, allow_pi=True))    # max
            #.setValidator(self.float_validator_pi)                     
        elif self.Phi_Dist_CB.currentText() in ['Discrete', 'Tabular']:    # discrete, Tabular
            self.Phi_Min_LE.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=None, allow_negative=True, allow_pi=True))    # values
            #.setValidator(self.float_validator_list_pi)            
            self.Phi_Max_LE.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=None, allow_negative=False, allow_pi=False))   # proba
            #.setValidator(self.float_validator_list_positif)       
        
        if self.Mu_Dist_CB.currentText() == 'Tabular':
            self.Phi_Interp_CB.setEnabled(True)
        else:
            self.Phi_Interp_CB.setEnabled(False)

    def Change_Text_Color(self):
        for LineEdit in [self.X_LL, self.X_UR, self.Y_LL, self.Y_UR, self.Z_LL, self.Z_UR, self.Energy_LE, self.Proba_LE,
                         self.Mu_Min_LE, self.Mu_Max_LE, self.Phi_Min_LE, self.Phi_Min_LE]:
            LineEdit.setStyleSheet("QLineEdit{color:black}")
            
    def Add_Sources1(self):
        self.Import_OpenMC()
        self.Find_string(self.v_1, "openmc.Settings")
        if self.Insert_Header:
            self.Find_string(self.plainTextEdit, "openmc.Settings")
            if self.Insert_Header:
                print(self.Settings_Header)
                print(self.Sett + " = openmc.Settings()\n")
            else:
                pass

        if self.Source_Geom_CB.currentIndex() in [1, 2, 3, 4, 5]:
            self.Particle = self.Particle_CB.currentText()
            """if self.Only_Fissionable and self.openmc_version < 150:
                self.Only_Fissionable_String = ', only_fissionable=True'
            else:
                self.Only_Fissionable_String = ''"""
            
            energy_str = ''; angle_str = ''
            if self.Array_Sources_RB.isChecked():
                self.Num_of_Srcs_Label.show()
                self.Number_of_Sources.show()
                if float(self.Strength_LE.text()) >= 1.:
                    self.showDialog('Warning', 'Strength must be smaller than 1. !.')
                Number_of_Sources = int(self.Number_of_Sources.value())
                for Is in range(Number_of_Sources - 1):
                    self.Source_Spatial_Distribution()
                    self.Source_Energy_Distribution()
                    self.Source_Angle_Distribution()
                    if self.Energy_Dist_CB.currentIndex() != 0:
                        energy_str = self.energy + ', '
                    if self.Direction_Dist_CB.currentIndex() != 0:
                        angle_str = self.angle + ', '
                    if Is == Number_of_Sources - 1: 
                        break
                    self.Source_Geom_CB.setCurrentIndex(0)
                    self.Energy_Dist_CB.setCurrentIndex(0)
                    self.Direction_Dist_CB.setCurrentIndex(0)
                print(str(self.Name_LE.text()) + ' = openmc.IndependentSource(' + self.spatial + ', ' + angle_str + energy_str + 'strength=' + str(
                        self.Strength_LE.text()) + ', particle=' + self.Particle + ')\n')
            else:
                Number_of_Sources = 1
                Err = self.Test_Data()
                if Err != 0:
                    return
                self.Source_Spatial_Distribution()
                self.Source_Energy_Distribution()
                self.Source_Angle_Distribution()
                self.Import_Numpy()
                if self.Energy_Dist_CB.currentIndex() != 0:
                    energy_str = self.energy + ', '
                if self.Direction_Dist_CB.currentIndex() != 0:
                    angle_str = self.angle + ', '

                print(str(self.Name_LE.text()) + ' = openmc.IndependentSource(' + self.spatial + ', ' + angle_str + energy_str + 'strength=' + str(
                        self.Strength_LE.text()) + ', particle=' + self.Particle + ')\n')
        elif self.Source_Geom_CB.currentIndex() == 6:
            ############################### File based source (.h5) #################################
            print(str(self.Name_LE.text()) + " = openmc.FileSource(filename= '" + self.src_filename +"')")
        elif self.Source_Geom_CB.currentIndex() == 7:
            ############################### Read Surface source (.h5) #################################
            print(str(self.Name_LE.text()) + " = openmc.surf_source_read(filename= '" + self.src_filename + "')")
        elif self.Source_Geom_CB.currentIndex() == 8:
            ############################### Read source 'build/libsource.so' #################################
            print(str(self.Name_LE.text()) + " = openmc.CompiledSource()")
            print(str(self.Name_LE.text()) + '.library = ' + "'" + str(self.Origin_LE.text()) + "'")
        
        self.Source_name_list.append(self.Name_LE.text())
        self.Source_id_list.append(int(self.Source_ID_LE.text()))
        document = self.v_1.toPlainText()
        if self.Sett + '.source' in self.plainTextEdit.toPlainText():
            doc = self.plainTextEdit.toPlainText()
            for line in doc.split('\n'):
                if self.Sett + '.source' in line:
                    doc = doc.replace(line, '')
            self.plainTextEdit.clear()

            print(doc)

        strg = self.Sett + '.source = ' + str(self.Source_name_list).replace("'", "")
        print(strg)
        if self.Uniform_Sampling_CB.isChecked():
            print(self.Sett + '.uniform_source_sampling = True')

        self.v_1.clear()
        cursor = self.v_1.textCursor()
        cursor.insertText(document)
        self.Source_id += 1
        self.Source_ID_LE.setText(str(self.Source_id))
        self.Name_LE.setText(''.join([i for i in self.Source_name_list[-1] if not i.isdigit()]) + self.Source_ID_LE.text())
        self.Energy_LE.clear()
        self.Proba_LE.clear()
        self.Mu_Min_LE.clear()
        self.Mu_Max_LE.clear()
        self.Phi_Min_LE.clear()
        self.Phi_Max_LE.clear()
        self.UVW_LE.clear()
        # self.Change_Text_Color()
        self.Particle_CB.setCurrentIndex(0)
        self.Source_Geom_CB.setCurrentIndex(0)
        self.Energy_Dist_CB.setCurrentIndex(0)
        self.Interpolate_CB.setCurrentIndex(0)
        self.Direction_Dist_CB.setCurrentIndex(0)
        self.Mu_Dist_CB.setCurrentIndex(0)
        self.Phi_Dist_CB.setCurrentIndex(0)
        self.Ref_UVW_CB.setCurrentIndex(0)
        self.Ref_VWU_CB.setCurrentIndex(0)
        self.Insert_Header = False

            
    def Add_Sources(self):
        self.Import_OpenMC()
        self.Find_string(self.v_1, "openmc.Settings")
        if self.Insert_Header:
            self.Find_string(self.plainTextEdit, "openmc.Settings")
            if self.Insert_Header:
                print(self.Settings_Header)
                print(self.Sett + " = openmc.Settings()\n")
        if self.Source_Type_CB.currentText() == 'IndependentSource':
            if self.Array_Sources_RB.isChecked():
                self.Num_of_Srcs_Label.show()
                self.Number_of_Sources.show()
                if float(self.Strength_LE.text()) >= 1.:
                    self.showDialog('Warning', 'Strength must be smaller than 1. !.')
                Number_of_Sources = int(self.Number_of_Sources.value())
                for Is in range(Number_of_Sources - 1):
                    if Is == Number_of_Sources - 1: 
                        break
                print(str(self.Name_LE.text()) + ' = openmc.IndependentSource()')
            else:
                Number_of_Sources = 1
                parameter = f"strength={self.Strength_LE.text()}, particle='{self.Particle_CB.currentText()}'"
                print(f"{self.Name_LE.text()} = openmc.IndependentSource({parameter})\n")
        elif self.Source_Type_CB.currentText() == 'FileSource':
            ############################### File based source (.h5) #################################
            print(str(self.Name_LE.text()) + " = openmc.FileSource(filename= '" + self.src_filename +"')")
        elif self.Source_Type_CB.currentText() == '':
            ############################### Read Surface source (.h5) #################################
            print(str(self.Name_LE.text()) + " = openmc.surf_source_read(filename= '" + self.src_filename + "')")
        elif self.Source_Type_CB.currentText() == 4:
            ############################### Read source 'build/libsource.so' #################################
            print(str(self.Name_LE.text()) + " = openmc.CompiledSource()")
            print(str(self.Name_LE.text()) + '.library = ' + "'" + str(self.Origin_LE.text()) + "'")
        
        self.Source_name_list.append(self.Name_LE.text())
        self.Source_id_list.append(int(self.Source_ID_LE.text()))
        document = self.v_1.toPlainText()
        self.Update_Sources_List()
        self.Uniform_Sampling()
        self.v_1.clear()
        cursor = self.v_1.textCursor()
        cursor.insertText(document)
        self.Source_id += 1
        self.Source_ID_LE.setText(str(self.Source_id))
        self.Name_LE.setText(''.join([i for i in self.Source_name_list[-1] if not i.isdigit()]) + self.Source_ID_LE.text())
        
        for w in [self.Add_Source_PB, self.Source_Geom_CB, self.Energy_Dist_CB, self.Direction_Dist_CB,
                  self.Time_Dist_CB, self.Use_Constraints_Checkbox]:
                w.setEnabled(True)
        
        self.Reset_fields()

    def Uniform_Sampling(self):
        if self.plainTextEdit.toPlainText():
            if self.Uniform_Sampling_CB.isChecked():
                self.Find_string(self.v_1, '.uniform_source_sampling = True')
                if self.Insert_Header:
                    self.Find_string(self.plainTextEdit, '.uniform_source_sampling = True')
                    if self.Insert_Header:
                        print(self.Sett + '.uniform_source_sampling = True')
            else:
                document = self.v_1.toPlainText()
                if '.uniform_source_sampling' in self.plainTextEdit.toPlainText():
                    doc = self.plainTextEdit.toPlainText()
                    for line in doc.split('\n'):
                        if '.uniform_source_sampling' in line:
                            doc = doc.replace(line, '')
                    self.plainTextEdit.clear()
                    print(doc)

    def Add_Source_Space(self):
        #  //////////////////////////////// Spatial distribution ////////////////////////////////
        Space_Keys = ['Point', 'Box', 'CartesianIndependent', 'CylindricalIndependent', 'SphericalIndependent'] 

        Source_Name = self.Source_name_list[-1]
        if self.Source_Geom_CB.currentIndex() == 0:
            if self.Number_of_Sources.value() > 1:
                self.showDialog('Warning', 'Choose option first for source' + Source_Name + ' !')
            else: 
                self.showDialog('Warning', 'Choose option first !')
            return
        if self.Source_Geom_CB.currentText() in Space_Keys:
            if self.X_LL.text() == '' or self.Y_LL.text() == '' or self.Z_LL.text() == '':
                self.showDialog('Warning', 'Fill the given fields first !')
                return
        if self.Source_Geom_CB.currentText() in Space_Keys[1:]:
            if self.X_UR.text() == '' or self.Y_UR.text() == '' or self.Z_UR.text() == '':
                self.showDialog('Warning', 'Fill the given fields first !')
                return
        if self.Source_Geom_CB.currentText() == 'Point':
            ###################################  Point Source ###################################
            print(f"{Source_Name}.space = openmc.stats.Point(({float(self.X_LL.text())}, {float(self.Y_LL.text())}, {float(self.Z_LL.text())}))")
        elif self.Source_Geom_CB.currentText() == 'Box':
            ####################################  Box Source ####################################
            print(f"{Source_Name}.space = openmc.stats.Box([{float(self.X_LL.text())}, {float(self.Y_LL.text())}, {float(self.Z_LL.text())}], [{float(self.X_UR.text())}, {float(self.Y_UR.text())}, {float(self.Z_UR.text())}])")
        elif self.Source_Geom_CB.currentText() == 'CartesianIndependent':
            ############################### Cartesian Independent ###############################
            # x Distribution
            Distribution = self.X_Dist_CB.currentText()
            if Distribution == 'Uniform':                      # X Uniform
                boundaries = tuple(sorted((float(self.X_LL.text()), float(self.X_UR.text()))))
                if boundaries[0] == boundaries[1]:
                    print('# x_min and x_max are the same. Check the line below !')
                print(f"x_dist = openmc.stats.{Distribution}{boundaries}")
            elif Distribution in ['Discrete', 'Tabular']:       # X Discrete & Tabular
                X_List, P_List = self.LE_to_List(self.X_LL, self.X_UR, 'X_values', 'X_Proba')
                if len(X_List) < 5:
                    print(f"x_dist = openmc.stats.{Distribution}({self.X_LL.text()}, {self.X_UR.text()})")
                else:
                    print(f"x_dist = openmc.stats.{Distribution}(X_values, X_Proba)")
            # y Distribution
            Distribution = self.Y_Dist_CB.currentText()
            if Distribution == 'Uniform':                       # Y Uniform
                boundaries = tuple(sorted((float(self.Y_LL.text()), float(self.Y_UR.text()))))
                if boundaries[0] == boundaries[1]:
                    print('# y_min and y_max are the same. Check the line below !')
                print(f"y_dist = openmc.stats.{Distribution}{boundaries}")
            elif Distribution in ['Discrete', 'Tabular']:       # Y Discrete & Tabular
                Y_List, P_List = self.LE_to_List(self.Y_LL, self.Y_UR, 'Y_values', 'Y_Proba')
                if len(Y_List) < 5:
                    print(f"y_dist = openmc.stats.{Distribution}({self.Y_LL.text()}, {self.Y_UR.text()})")
                else:
                    print(f"y_dist = openmc.stats.{Distribution}(Y_values, Y_Proba)")
            
            # z Distribution
            Distribution = self.Z_Dist_CB.currentText()
            if Distribution == 'Uniform':                       # Z Uniform
                boundaries = tuple(sorted((float(self.Z_LL.text()), float(self.Z_UR.text()))))
                if boundaries[0] == boundaries[1]:
                    print('# z_min and z_max are the same. Check the line below !')
                print(f"z_dist = openmc.stats.{Distribution}{boundaries}")
            elif Distribution in ['Discrete', 'Tabular']:       # Z Discrete & Tabular
                Z_List, P_List = self.LE_to_List(self.Z_LL, self.Z_UR, 'Z_values', 'Z_Proba')
                if len(Z_List) < 5:
                    print(f"z_dist = openmc.stats.{Distribution}({self.Z_LL.text()}, {self.Z_UR.text()})")
                else:
                    print(f"z_dist = openmc.stats.{Distribution}(Z_values, Z_Proba)")

            print(f"{Source_Name}.space = openmc.stats.CartesianIndependent(x_dist, y_dist, z_dist)")

        elif self.Source_Geom_CB.currentText() == 'CylindricalIndependent':
            ############################### Cylindrical Independent ###############################
            # R Distribution
            Distribution = self.X_Dist_CB.currentText()
            if Distribution == 'Uniform':                      # R Uniform
                boundaries = tuple(sorted((float(self.X_LL.text()), float(self.X_UR.text()))))
                print(f"r_dist = openmc.stats.{Distribution}{boundaries}")
            elif Distribution in ['Discrete', 'Tabular']:       # R Discrete & Tabular
                R_List, P_List = self.LE_to_List(self.X_LL, self.X_UR, 'R_values', 'R_Proba')
                if len(R_List) < 5:
                    print(f"r_dist = openmc.stats.{Distribution}({self.X_LL.text()}, {self.X_UR.text()})")
                else:
                    print(f"r_dist = openmc.stats.{Distribution}(R_values, R_Proba)")
            
            # phi Distribution
            Distribution = self.Y_Dist_CB.currentText()
            if Distribution == 'Uniform':                       # Phi Uniform
                if 'pi' not in self.Y_LL.text():
                    phi_min = float(self.Y_LL.text()) 
                else:
                    phi_min = self.Replace_PI_N(self.Y_LL.text())  
                if 'pi' not in self.Y_UR.text():
                    phi_max = float(self.Y_UR.text())
                else:
                    phi_max = self.Replace_PI_N(self.Y_UR.text())  
                boundaries = tuple(self.Sorting([phi_min, phi_max]))     
                print(f"phi_dist = openmc.stats.{Distribution}{boundaries}".replace("'", "").replace('"', ''))
            elif Distribution in ['Discrete', 'Tabular']:       # Phi Discrete & Tabular
                Phi_List, P_List = self.LE_to_List(self.Y_LL, self.Y_UR, 'Phi_values', 'Phi_Proba')
                if len(Phi_List) < 5:
                    print(f"phi_dist = openmc.stats.{Distribution}({self.Y_LL.text()}, {self.Y_UR.text()})")
                else:
                    print(f"phi_dist = openmc.stats.{Distribution}(Phi_values, Phi_Proba)")

            # z Distribution
            Distribution = self.Z_Dist_CB.currentText()
            if Distribution == 'Uniform':                       # Z Uniform
                boundaries = tuple(sorted((float(self.Z_LL.text()), float(self.Z_UR.text()))))
                print(f"z_dist = openmc.stats.{Distribution}{boundaries}")
            elif Distribution in ['Discrete', 'Tabular']:       # Z Discrete & Tabular
                Z_List, P_List = self.LE_to_List(self.Z_LL, self.Z_UR, 'Z_values', 'Z_Proba')
                if len(Z_List) < 5:
                    print(f"z_dist = openmc.stats.{Distribution}({self.Z_LL.text()}, {self.Z_UR.text()})")
                else:
                    print(f"z_dist = openmc.stats.{Distribution}(Z_values, Z_Proba)")
            
            origin = self.LE_to_List2(self.Origin_LE)
            print(f"{Source_Name}.space = openmc.stats.CylindricalIndependent(r_dist, phi_dist, z_dist, origin={origin})")
        
        elif self.Source_Geom_CB.currentText() == 'SphericalIndependent':
            ################################## Spherical Independent ################################
            # R Distribution
            Distribution = self.X_Dist_CB.currentText()
            if Distribution == 'Uniform':                      # R Uniform
                boundaries = tuple(sorted((float(self.X_LL.text()), float(self.X_UR.text()))))
                print(f"r_dist = openmc.stats.{Distribution}{boundaries}")
            elif Distribution in ['Discrete', 'Tabular']:       # R Discrete & Tabular
                R_List, P_List = self.LE_to_List(self.X_LL, self.X_UR, 'R_values', 'R_Proba')
                if len(R_List) < 5:
                    print(f"r_dist = openmc.stats.{Distribution}({self.X_LL.text()}, {self.X_UR.text()})")
                else:
                    print(f"r_dist = openmc.stats.{Distribution}(R_values, R_Proba)")

            # theta Distribution
            Distribution = self.Y_Dist_CB.currentText()
            if Distribution == 'Uniform':                       # Theta Uniform
                if 'pi' not in self.Y_LL.text():
                    theta_min = (self.Y_LL.text()) 
                else:
                    theta_min = self.Replace_PI_N(self.Y_LL.text())  #.replace('pi', 'np.pi')
                if 'pi' not in self.Y_UR.text():
                    theta_max = (self.Y_UR.text())
                else:
                    theta_max = self.Replace_PI_N(self.Y_UR.text())  #.replace('pi', 'np.pi')
                boundaries = tuple(self.Sorting([theta_min, theta_max]))     
                print(f"theta_dist = openmc.stats.{Distribution}{boundaries}".replace("'", "").replace('"', ''))
            elif Distribution in ['Discrete', 'Tabular']:       # Theta Discrete & Tabular
                Theta_List, P_List = self.LE_to_List(self.Y_LL, self.Y_UR, 'Theta_values', 'Theta_Proba')
                if len(Theta_List) < 5:
                    print(f"theta_dist = openmc.stats.{Distribution}({self.Y_LL.text()}, {self.Y_UR.text()})")
                else:
                    print(f"theta_dist = openmc.stats.{Distribution}(Theta_values, Theta_Proba)")
            
            # phi Distribution
            Distribution = self.Z_Dist_CB.currentText()
            if Distribution == 'Uniform':                       # Phi Uniform
                if 'pi' not in self.Z_LL.text():
                    phi_min = float(self.Z_LL.text()) 
                else:
                    phi_min = self.Replace_PI_N(self.Z_LL.text())  #.replace('pi', 'np.pi')
                if 'pi' not in self.Z_UR.text():
                    phi_max = float(self.Z_UR.text())
                else:
                    phi_max = self.Replace_PI_N(self.Z_UR.text())  #.replace('pi', 'np.pi')
                boundaries = tuple(self.Sorting([phi_min, phi_max]))    
                print(f"phi_dist = openmc.stats.{Distribution}{boundaries}".replace("'", "").replace('"', ''))
            elif Distribution in ['Discrete', 'Tabular']:       # Phi Discrete & Tabular
                Phi_List, P_List = self.LE_to_List(self.Z_LL, self.Z_UR, 'Phi_values', 'Phi_Proba')
                if len(Phi_List) < 5:
                    print(f"phi_dist = openmc.stats.{Distribution}({self.Z_LL.text()}, {self.Z_UR.text()})")
                else:
                    print(f"phi_dist = openmc.stats.{Distribution}(Phi_values, Phi_Proba)")    

            origin = self.LE_to_List2(self.Origin_LE)
            if len(origin) != 3:
                self.showDialog('Warning', 'Origin length must be equal to 3 !\nValue will be set to default (0., 0., 0.)')
                origin = [0., 0., 0.]

            print(f"{Source_Name}.space = openmc.stats.SphericalIndependent(r_dist, theta_dist, phi_dist, origin={origin})")

        self.Source_Geom_CB.setCurrentIndex(0)
        self.Update_Sources_List()

    def Add_Source_Energy(self):
        # ////////////////////////////////   Energy distribution   ////////////////////////////////
        #['discrete', 'uniform', 'powerlaw', 'maxwell', 'watt', 'normal', 'muir', 'tabular'])  # , 'mixture'])
        if self.Energy_LE.text() == "":
            self.showDialog('Warning', "Enter data first !")
            return
        
        if self.Energy_Dist_CB.currentText() not in ['maxwell', 'legendre'] and self.Proba_LE.text() == "":
            self.showDialog('Warning', "Enter data first !")
            return
        
        Source_Name = self.Source_name_list[-1]

        if self.Source_Geom_CB.currentIndex() not in [6, 7, 8]:
            if self.Energy_Dist_CB.currentText() == 'discrete':     
                E_List, P_List = self.LE_to_List(self.Energy_LE, self.Proba_LE, 'E_values', 'E_Proba')
                if len(E_List) < 5:    
                    print(f"{Source_Name}.energy = openmc.stats.Discrete({self.Energy_LE.text()}, {self.Proba_LE.text()})")
                else:
                    print(f"{Source_Name}.energy = openmc.stats.Discrete(E_values, E_Proba)")
            elif self.Energy_Dist_CB.currentText() == 'uniform':  
                boundaries = tuple(sorted((float(self.Energy_LE.text()), float(self.Proba_LE.text()))))
                print(f"{Source_Name}.energy = openmc.stats.Uniform{boundaries}")    
            elif self.Energy_Dist_CB.currentText() == 'powerlaw': 
                boundaries = tuple(sorted((float(self.Energy_LE.text()), float(self.Proba_LE.text()))))
                if boundaries[0] == boundaries[1]:
                    self.showDialog("Warning","Lower bound of sampling interval must be less than upper bound!")
                    return
                print(f"{Source_Name}.energy = openmc.stats.PowerLaw({boundaries[0]}, {boundaries[1]}, {self.Exponent_LE.text()})")
            elif self.Energy_Dist_CB.currentText() == 'maxwell':     
                print(f"{Source_Name}.energy= openmc.stats.Maxwell({self.Energy_LE.text()})")
            elif self.Energy_Dist_CB.currentText() == 'watt':      
                print(f"{Source_Name}.energy = openmc.stats.Watt({self.Energy_LE.text()}, {self.Proba_LE.text()})")
            elif self.Energy_Dist_CB.currentText() == 'normal':      
                print(f"{Source_Name}.energy = openmc.stats.Normal({self.Energy_LE.text()}, {self.Proba_LE.text()})")
            elif self.Energy_Dist_CB.currentText() == 'muir':      
                print(f"{Source_Name}.energy = openmc.stats.muir({self.Energy_LE.text()}, {self.Proba_LE.text()}, {self.Exponent_LE.text()})")
            elif self.Energy_Dist_CB.currentText() == 'tabular':      
                E_List, P_List = self.LE_to_List(self.Energy_LE, self.Proba_LE, 'E_values', 'E_Proba')
            
                if len(E_List) < 5:    
                    print(f"{Source_Name}.energy = openmc.stats.Tabular({self.Energy_LE.text()}, {self.Proba_LE.text()}, interpolation='{self.Interpolate_CB.currentText()}')")
                else:
                    print(f"{Source_Name}.energy = openmc.stats.Tabular(E_values, E_Proba, interpolation='{self.Interpolate_CB.currentText()}')")
            
            elif self.Energy_Dist_CB.currentText() == 'legendre':     
                Coef_List = self.LE_to_List2(self.Energy_LE)
                print(f"{Source_Name}.energy = openmc.stats.Legendre({Coef_List})")
        
        self.Energy_LE.clear()
        self.Proba_LE.clear()
        self.Exponent_LE.clear()
        self.Energy_Dist_CB.setCurrentIndex(0)
        self.Update_Sources_List()

    def Add_Source_Angle(self):
        #   ////////////////////////////////   Angle distribution   /////////////////////////////////
        Source_Name = self.Source_name_list[-1]
        
        if self.Direction_Dist_CB.currentIndex() in [0, 1, 2, 3]:
            for item in [self.Mu_Min_LE, self.Mu_Max_LE, self.Phi_Min_LE, self.Phi_Min_LE,
                        self.label_10, self.Ref_UVW_CB, self.label_29, self.Ref_VWU_CB]:
                item.setEnabled(False)
            for item in [self.Mu_Min_LE, self.Mu_Max_LE, self.Phi_Min_LE, self.Phi_Min_LE]:
                item.clear()
        # //////////////////////////////////// Isotropic /////////////////////////////////////////
        if self.Direction_Dist_CB.currentIndex() == 1:
            print(f"{Source_Name}.angle = openmc.stats.Isotropic()")
        # ///////////////////////////////// Monodirectional //////////////////////////////////////
        elif self.Direction_Dist_CB.currentIndex() == 2:
            if self.Ref_UVW_CB.currentIndex() == 6:
                if self.UVW_LE.text() == '':
                    self.showDialog('Warning', 'Enter 3 vector components first!')
                    return
                else:
                    UVW_List = self.LE_to_List2(self.UVW_LE)
                    if len(UVW_List) != 3: 
                        self.showDialog('Warning', 'Vector length must be equal to 3 !')
                        return
            else:
                UVW_List = self.Ref_UVW_CB.currentText()
                
            print(f"{Source_Name}.angle = openmc.stats.Monodirectional(reference_uvw={UVW_List})")
        # //////////////////////////////////// UnitSphere ////////////////////////////////////////
        elif self.Direction_Dist_CB.currentIndex() == 3:
            #self.Ref_UVW_CB.setEnabled(True)
            print(f"{Source_Name}.angle = openmc.stats.UnitSphere(reference_uvw={self.Ref_UVW_CB.currentText()})")
        # //////////////////////////////////// PolarAzimuthal ////////////////////////////////////////
        elif self.Direction_Dist_CB.currentIndex() == 4:
            # Mu distribution
            Distribution = self.Mu_Dist_CB.currentText()
            if Distribution in ['Uniform', 'Normal']:            # Mu Uniform & Normal
                boundaries = tuple(sorted((float(self.Mu_Min_LE.text()), float(self.Mu_Max_LE.text()))))
                print(f"mu_dist = openmc.stats.{Distribution}{boundaries}")
            elif Distribution in ['Discrete', 'Tabular']:       # Mu Discrete & Tabular
                if Distribution == 'Discrete':
                    Interpolation = ''
                else:
                    Interpolation = f", interpolation='{self.Mu_Interp_CB.currentText()}'"
                Mu_List, P_List = self.LE_to_List(self.Mu_Min_LE, self.Mu_Max_LE, 'Mu_values', 'Mu_Proba')
                if len(Mu_List) < 5:
                    print(f"mu_dist = openmc.stats.{Distribution}({self.Mu_Min_LE.text()}, {self.Mu_Max_LE.text()}{Interpolation})")
                else:
                    print(f"mu_dist = openmc.stats.{Distribution}(Mu_values, Mu_Proba{Interpolation})")

            # phi Distribution
            Distribution = self.Phi_Dist_CB.currentText()
            if Distribution in ['Uniform', 'Normal']:           # Phi Uniform & Normal
                if 'pi' not in self.Phi_Min_LE.text():
                    phi_min = float(self.Phi_Min_LE.text()) 
                else:
                    phi_min = self.Replace_PI_N(self.Phi_Min_LE.text())  
                if 'pi' not in self.Phi_Max_LE.text():
                    phi_max = float(self.Phi_Max_LE.text())
                else:
                    phi_max = self.Replace_PI_N(self.Phi_Max_LE.text())  
                boundaries = tuple(self.Sorting([phi_min, phi_max]))     
                print(f"phi_dist = openmc.stats.{Distribution}{boundaries}".replace("'", "").replace('"', ''))
            elif Distribution in ['Discrete', 'Tabular']:       # Phi Discrete & Tabular
                if Distribution == 'Discrete':
                    Interpolation = ''
                else:
                    Interpolation = f", interpolation='{self.Phi_Interp_CB.currentText()}'"
                Phi_List, P_List = self.LE_to_List(self.Phi_Min_LE, self.Phi_Max_LE, 'Phi_values', 'Phi_Proba')
                if len(Phi_List) < 5:
                    print(f"phi_dist = openmc.stats.{Distribution}({self.Phi_Min_LE.text()}, {self.Phi_Max_LE.text()}{Interpolation})")
                else:
                    print(f"phi_dist = openmc.stats.{Distribution}(Phi_values, Phi_Proba{Interpolation})")  

            if self.Ref_UVW_CB.currentIndex() == 6:
                UVW_List = self.LE_to_List2(self.UVW_LE)
                if len(UVW_List) != 3: 
                    self.showDialog('Warning', 'Vector length must be equal to 3 !')
                    return
            else:
                UVW_List = self.Ref_UVW_CB.currentText()

            if self.Ref_VWU_CB.currentIndex() == 6:
                VWU_List = self.LE_to_List2(self.VWU_LE)
                if len(VWU_List) != 3: 
                    self.showDialog('Warning', 'Vector length must be equal to 3 !')
                    return
            else:
                VWU_List = self.Ref_VWU_CB.currentText()
                
            print(f"{Source_Name}.angle = openmc.stats.PolarAzimuthal(mu_dist, phi_dist, reference_uvw={UVW_List}, reference_vwu={VWU_List})")

        for CB in [self.Direction_Dist_CB, self.Ref_UVW_CB, self.Ref_VWU_CB, self.Mu_Dist_CB, self.Phi_Dist_CB]:
            CB.setCurrentIndex(0)

        for W in [self.UVW_LE, self.VWU_LE, self.Mu_Min_LE, self.Mu_Max_LE, self.Phi_Min_LE, self.Phi_Max_LE]:
            W.clear()

        self.Update_Sources_List()

    def Add_Source_Time(self):
        Source_Name = self.Source_name_list[-1]
        Distribution = self.Time_Dist_CB.currentText()
        if Distribution in ['Uniform']:            # Time Uniform
            boundaries = tuple(sorted((float(self.Time_LBound_LE.text()), float(self.Time_UBound_LE.text()))))
            print(f"{Source_Name}.time = openmc.stats.{Distribution}{boundaries}")
        elif Distribution in ['Discrete']:        # Time Discrete
            Time_List, P_List = self.LE_to_List(self.Time_LBound_LE, self.Time_UBound_LE, 'T_values', 'T_Proba')
            if len(Time_List) < 5:
                print(f"{Source_Name}.time = openmc.stats.{Distribution}({self.Time_LBound_LE.text()}, {self.Time_UBound_LE.text()})")
            else:
                print(f"{Source_Name}.time = openmc.stats.{Distribution}(T_values, T_Proba)")
        
        self.Time_Dist_CB.setCurrentIndex(0)
        self.Time_LBound_LE.clear()
        self.Time_UBound_LE.clear()

        self.Update_Sources_List()

    def Add_Source_Constraints(self):
        pass
        
        self.Update_Sources_List()

    def Update_Sources_List(self):
        if self.Sett + '.source' in self.plainTextEdit.toPlainText():
            doc = self.plainTextEdit.toPlainText()
            for line in doc.split('\n'):
                if self.Sett + '.source' in line:
                    doc = doc.replace(line, '')
            self.plainTextEdit.clear()
            print(doc)

        strg = self.Sett + '.source = ' + str(self.Source_name_list).replace("'", "")
        print(strg)

    def Reset_fields(self):
        for W in [self.Energy_LE, self.Proba_LE, self.Mu_Min_LE, self.Mu_Max_LE, self.Phi_Min_LE,
                  self.Phi_Max_LE, self.UVW_LE]:
            W.clear()
      
        for W in [self.Particle_CB, self.Source_Geom_CB, self.Energy_Dist_CB, self.Interpolate_CB,
                  self.Direction_Dist_CB , self.Mu_Dist_CB, self.Phi_Dist_CB, self.Ref_UVW_CB,
                  self.Ref_VWU_CB]:
            W.setCurrentIndex(0)
        
        self.Insert_Header = False
        
    def Test_Data(self):
        #['discrete', 'uniform', 'powerlaw', 'maxwell', 'watt', 'normal', 'muir', 'tabular'])  # , 'mixture'])
        Err = 0
        if self.Name_LE.text() in self.Source_name_list:
            Err = 1
            self.showDialog('Warning', 'Source name must not be repeated!')
        # Check if energy distribution data are given
        if self.Energy_Dist_CB.currentText() == 'discrete':     
            if self.Energy_LE.text() == '' or self.Proba_LE.text() == '':
                Err = 1
                self.showDialog('Warning', 'Energy and Proba lists must be provided !')
        elif self.Energy_Dist_CB.currentText() == 'uniform':      
            if self.Energy_LE.text() == '' or self.Proba_LE.text() == '':
                Err = 0
                self.showDialog('Warning', 'Lower bound and upper bound must be given !\n Defaults to 0. and 1.')
        elif self.Energy_Dist_CB.currentText() == 'powerlaw':      
            if self.Energy_LE.text() == '' or self.Proba_LE.text() == '' or self.Exponent_LE.text() == '':
                Err = 0
                self.showDialog('Warning', 'Lower bound, upper bound and power law exponent must be given ! Defaults to 0., 1. and 0.')
        elif self.Energy_Dist_CB.currentText() == 'maxwell':     
            if self.Energy_LE.text() == '':
                Err = 1
                self.showDialog('Warning', 'Effective temperature must be provided !')
        elif self.Energy_Dist_CB.currentText() == 'watt':      
            if self.Energy_LE.text() == '' or self.Proba_LE.text() == '':
                Err = 1
                self.showDialog('Warning', 'First paramater a and second parameter b must be given !')
        elif self.Energy_Dist_CB.currentText() == 'normal':      
            if self.Energy_LE.text() == '' or self.Proba_LE.text() == '':
                Err = 1
                self.showDialog('Warning', 'Mean value and Standard deviation of the Normal distribution must be given !')
        elif self.Energy_Dist_CB.currentText() == 'muir':      
            if self.Energy_LE.text() == '' or self.Proba_LE.text() == '' or self.Exponent_LE.text() == '':
                Err = 1
                self.showDialog('Warning', 'Mean, Ratio of the sum of the masses and Ion temperature for the Muir distribution must be given !') 
        elif self.Energy_Dist_CB.currentText() == 'tabular':      
            if self.Energy_LE.text() == '' or self.Proba_LE.text() == '':
                Err = 1
                self.showDialog('Warning', 'Tabulated Energies and Tabulated Probabilities must be provided !')
            else:
                if self.Interpolate_CB.currentIndex() == 0:
                    Err = 0
                    self.showDialog('Warning', "Select Interpolation type first ! Defaults to 'linear-linear'.")
                    self.Interpolate_CB.setCurrentIndex(self.Interpolate_CB.findText('linear-linear'))
        elif self.Energy_Dist_CB.currentText() == 'legendre':     
            if self.Energy_LE.text() == '':
                Err = 1
                self.showDialog('Warning', 'Expansion coefficients list must be provided !')

        # Check if direction distribution data are given
        if self.Mu_Dist_CB.currentText() == 'Discrete mu':     
            if self.Mu_Min_LE.text() == '' or self.Mu_Max_LE.text() == '':
                Err = 1
                self.showDialog('Warning', 'Cosine of the polar angle and Proba lists must be provided !')
        elif self.Mu_Dist_CB.currentText() == 'Uniform mu':      
            if self.Mu_Min_LE.text() == '' or self.Mu_Max_LE.text() == '':
                Err = 1
                self.showDialog('Warning', 'Lower bound and upper bound of cosine of polar angle must be given !')

        if self.Mu_Dist_CB.currentText() == 'Discrete mu':     
            if self.Phi_Min_LE.text() == '' or self.Phi_Max_LE.text() == '':
                Err = 1
                self.showDialog('Warning', 'Azimuthal angle in radians and Proba lists must be provided !')
        elif self.Mu_Dist_CB.currentText() == 'Uniform mu':      
            if self.Phi_Min_LE.text() == '' or self.Phi_Max_LE.text() == '':
                Err = 1
                self.showDialog('Warning', 'Lower bound and upper bound of azimuthal angle must be given  in radians!')

        return Err




    def Export_to_Main_Window(self):
        self.Find_string(self.v_1, "openmc.Settings")
        self.v_1.moveCursor(QTextCursor.End)
        if self.Insert_Header:
            self.Find_string(self.plainTextEdit, "openmc.Settings")
            if self.Insert_Header:
                print(self.Settings_Header)
                print(self.Sett + ' = openmc.Settings()\n')
        
        self.Import_Numpy()

        if 'import numpy' in self.plainTextEdit.toPlainText():
            self.Suppress_Line('import numpy', self.plainTextEdit)
        
        self.Insert_Header = False
        string_to_find = self.Sett + ".export_to_xml()"
        self.Find_string(self.v_1, string_to_find)
        cursor = self.v_1.textCursor()
        self.plainTextEdit.moveCursor(QTextCursor.End)
        if self.Insert_Header:
            cursor.insertText(self.plainTextEdit.toPlainText())
            cursor.insertText('\n' + string_to_find + '\n')
        else:
            document = self.v_1.toPlainText()
            if self.tabWidget.currentIndex() == 0:
                print ('\n' + string_to_find)     
                document = self.Replace_Doc(self.plainTextEdit.toPlainText(), document)
                document1 = document.replace(string_to_find, self.plainTextEdit.toPlainText())
            elif self.tabWidget.currentIndex() == 1:
                lines = [line for line in document.split('\n') if line != '' and line[0] != '#']
                for line in lines:
                    if self.Sett + ".source" in line and self.Sett + ".source.Source" not in line: 
                        document1 = document.replace(str(line), self.plainTextEdit.toPlainText())
                        break
                    else:
                        document1 = document.replace(string_to_find, self.plainTextEdit.toPlainText() + '\n' + string_to_find + '\n')
            elif self.tabWidget.currentIndex() == 2:
                document1 = document.replace(string_to_find, self.plainTextEdit.toPlainText() + '\n' + string_to_find + '\n')
            self.v_1.clear()
            cursor.insertText(document1)
        
        document = self.v_1.toPlainText()
        document = self.Move_Commands_to_End(document)
        cursor = self.v_1.textCursor()
        self.v_1.clear()
        cursor.insertText(document)
        self.text_inserted = True
        self.plainTextEdit.clear()
        for w in [self.Add_Source_PB, self.Source_Geom_CB, self.Energy_Dist_CB, self.Direction_Dist_CB,
            self.Time_Dist_CB, self.Use_Constraints_Checkbox]:
            w.setEnabled(False)

        self.Source_Type_CB.setCurrentIndex(0)
        self.Run_Mode_CB.setCurrentIndex(0)

    def Replace_Doc(self, doc1, doc2):
        for line in doc1.split('\n'):
            if '=' in line: 
                key = line.split('=')[0]
                #Value = line.split('=')[1]
                if key in doc2:
                    text_to_replace = key + re.search('%s(.*)%s' % (key, '\n'), doc2).group(1)
                    
                    #if ';' in text_to_replace:
                        #text_to_replace = key + re.search('%s(.*)%s' % (key, ';'), doc2).group(1)
                        
                    doc2 = doc2.replace(text_to_replace, '')
        return doc2
            
    def clear_text(self):
        self.plainTextEdit.clear()

    def normalOutputWritten(self,text):
        self.highlighter = Highlighter(self.plainTextEdit.document())
        cursor = self.plainTextEdit.textCursor()
        cursor.insertText(text)


#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import os
import ast
import PyQt5
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
from src.syntax_py import Highlighter
from src.PyEdit import TextEdit, NumberBar  


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

################################################################################
################################################################################

class EmittingStream(QtCore.QObject):
    textWritten = QtCore.pyqtSignal(str)

    def write(self, text):
        self.textWritten.emit(str(text))
        pass

    def flush(self):
        pass

################################################################################
################################################################################

class ExportDepletion(QWidget):
    ###############################################################################
    #                   Initialize and run depletion calculation
    ###############################################################################
    from .func import resize_ui
    from .func import showDialog, Exit, Find_string
    def __init__(self, v_1, Directory, Materials, Elements, Nuclides, Cells, Mats, Geom, 
                Sett, Operator, Integrator, Deplete_Mats, Deplete_Cells, Model, Chain, Run_Mode, parent=None):
        super(ExportDepletion, self).__init__(parent)
        uic.loadUi("src/ui/ExportDepletion.ui", self)
        sys.stdout = EmittingStream(textWritten=self.normalOutputWritten)
        #sys.stderr = EmittingStream(textWritten=self.normalOutputWritten)
        self.v_1 = v_1 
        self.directory = Directory
        self.materials_name_list = Materials
        self.Depletable_Mats = Deplete_Mats
        self.Depletable_Cells = Deplete_Cells
        self.Model_Elements_List = Elements
        self.Model_Nuclides_List = Nuclides
        self.cell_name_list = Cells
        self.Mats = Mats
        self.Nuclides = Nuclides
        self.Geom = Geom
        self.Sett = Sett
        self.Model = Model
        self.Integrator = Integrator
        self.Operator = Operator
        self.Chain = Chain
        self.Run_Mode = Run_Mode
        
        if self.Run_Mode == 'fixed source':
            self.label_6.setText('Source rate')
            self.NormMod_CB.model().item(self.NormMod_CB.findText('source-rate')).setEnabled(True)
            self.NormMod_CB.model().item(self.NormMod_CB.findText('energy-deposition')).setEnabled(False)
            self.NormMod_CB.model().item(self.NormMod_CB.findText('fission-q')).setEnabled(False)
        elif self.Run_Mode == 'eigenvalue':
            self.label_6.setText('Power')
            self.NormMod_CB.model().item(self.NormMod_CB.findText('energy-deposition')).setEnabled(True)
            self.NormMod_CB.model().item(self.NormMod_CB.findText('fission-q')).setEnabled(True)
            self.NormMod_CB.model().item(self.NormMod_CB.findText('source-rate')).setEnabled(False)

        self.Geom_LE.setText(Geom)
        self.Mats_LE.setText(Mats)
        self.Sett_LE.setText(Sett)
        self.Model_LE.setText(Model)
        self.Operator_LE.setText(Operator)
        self.Integrator_LE.setText(Integrator)
        idx = self.Chain_CB.findText(self.Chain)
        self.Chain_CB.setCurrentIndex(idx)
        self.Chain_File = self.Chain
        self.text_inserted = False
        self.Insert_Header = True
        validator = QDoubleValidator(self)
        self.text_inserted = False
        self.Fission_Q_LE.setEnabled(False)
        # add new editor
        self.plainTextEdit = TextEdit()
        self.plainTextEdit.setWordWrapMode(QTextOption.NoWrap)
        self.numbers = NumberBar(self.plainTextEdit)
        layoutH = QHBoxLayout()
        #layoutH.setSpacing(1.5)
        layoutH.addWidget(self.numbers)
        layoutH.addWidget(self.plainTextEdit)
        self.EditorLayout.addLayout(layoutH, 0, 0)
        self.RedChainLevel_SP.setMaximum(10)
        self.RedChainLevel_SP.setMinimum(0)
        # Create checkable combobox of depletable materials
        self.Depletable_Mat_CB = CheckableComboBox()
        self.Depletable_Mat_CB.addItem('Select depletable material')
        self.Depletable_Mat_CB.addItem('All bins')
        self.gridLayout_19.addWidget(self.Depletable_Mat_CB)
        self.Depletable_Mat_CB.model().item(0).setEnabled(False)
        self.Depletable_Mat_CB.model().item(0).setCheckState(Qt.Unchecked)
        self.Depletable_Mat_CB.addItems(self.Depletable_Mats)
        for i in range(len(self.Depletable_Mats) + 1):
            self.Depletable_Mat_CB.setItemChecked(i, False)
        # Create checkable combobox of nuclides
        self.Nuclides_comboBox = CheckableComboBox()
        self.Nuclides_GL.addWidget(self.Nuclides_comboBox)
        self.Nuclides_comboBox.addItem('Select nuclides')
        self.Nuclides_comboBox.addItem('All bins')
        self.Nuclides_comboBox.model().item(0).setEnabled(False)
        self.Nuclides_comboBox.model().item(0).setCheckState(Qt.Unchecked)
        self.Nuclides_comboBox.addItems(self.Nuclides)
        for i in range(len(self.Nuclides) + 1):
            self.Nuclides_comboBox.setItemChecked(i, False)
        # Create checkable combobox of reactions
        self.Reactions_comboBox = CheckableComboBox()
        self.Reactions_GL.addWidget(self.Reactions_comboBox)
        # Create checkable combobox of depletable domains
        self.Domains_comboBox = CheckableComboBox()
        self.Domains_GL.addWidget(self.Domains_comboBox)
        self.Domains_comboBox.addItem('Select domains')
        self.Domains_comboBox.addItem('All bins')
        self.Domains_comboBox.model().item(0).setEnabled(False)
        self.Domains_comboBox.model().item(0).setCheckState(Qt.Unchecked)
        self.Domains_comboBox.addItems(self.Depletable_Cells)
        for i in range(len(self.Depletable_Cells) + 1):
            self.Domains_comboBox.setItemChecked(i, False) 
        # Create checkable combobox of nuclides_2
        self.Nuclides_comboBox_2 = CheckableComboBox()
        self.Nuclides_GL_2.addWidget(self.Nuclides_comboBox_2)
        self.Nuclides_comboBox_2.addItem('Select nuclides')
        self.Nuclides_comboBox_2.addItem('All bins')
        self.Nuclides_comboBox_2.model().item(0).setEnabled(False)
        self.Nuclides_comboBox_2.model().item(0).setCheckState(Qt.Unchecked)
        self.Nuclides_comboBox_2.addItems(self.Nuclides)
        for i in range(len(self.Nuclides) + 1):
            self.Nuclides_comboBox_2.setItemChecked(i, False)
        # Create checkable combobox of reactions
        self.Reactions_comboBox_2 = CheckableComboBox()
        self.Reactions_GL_2.addWidget(self.Reactions_comboBox_2)
        # Create checkable combobox of depletable domains_2
        self.Domains_comboBox_2 = CheckableComboBox()
        self.Domains_GL_2.addWidget(self.Domains_comboBox_2)
        self.Domains_comboBox_2.addItem('Select domains')
        self.Domains_comboBox_2.addItem('All bins')
        self.Domains_comboBox_2.model().item(0).setEnabled(False)
        self.Domains_comboBox_2.model().item(0).setCheckState(Qt.Unchecked)
        self.Domains_comboBox_2.addItems(self.Depletable_Cells)
        for i in range(len(self.Depletable_Cells) + 1):
            self.Domains_comboBox_2.setItemChecked(i, False) 
        self.Nuclides_LE.clear()
        self.Checked_Nuclides = []
        MGX_GROUP_STRUCTURES_LIST = ['Select Structure', 'enter custom list', 'CASMO-2', 'CASMO-4', 'CASMO-8', 'CASMO-16', 'CASMO-25', 'CASMO-40', 'VITAMIN-J-42', 'CASMO-70',
                                'XMAS-172', 'VITAMIN-J-175', 'TRIPOLI-315,', 'SHEM-361', 'CCFE-709', 'UKAEA-1102']
        for CB in [self.Flux_Energy_Gr_CB, self.Flux_Energy_Gr_CB_2]:
            CB.clear()
            CB.addItems(MGX_GROUP_STRUCTURES_LIST)
        
        self._initButtons()

        # to show window at the middle of the screen and resize it to the screen size
        self.resize_ui(1, 0.6)
    
    def resize_ui(self, H, V):
        # to show window at the middle of the screen and resize it to the screen size
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

        width = int(QDesktopWidget().availableGeometry().width() * H)
        height = int(QDesktopWidget().availableGeometry().height() * V)
        self.setMaximumWidth(width)
        self.setMaximumHeight(height)

    def _initButtons(self):
        self.CreateDepletion_PB.clicked.connect(self.Add_Depletion)
        self.Reset_PB.clicked.connect(self.Reset_Fields)
        self.Undo_Reset_PB.clicked.connect(self.Undo_Reset)
        self.Nuclides_comboBox.currentIndexChanged.connect(self.SelectNuclides)
        self.Nuclides_comboBox_2.currentIndexChanged.connect(self.SelectNuclides)
        self.Reactions_comboBox.currentIndexChanged.connect(self.SelectReactions)
        self.Reactions_comboBox_2.currentIndexChanged.connect(self.SelectReactions)
        self.Domains_comboBox.currentIndexChanged.connect(self.SelectDomains)
        self.Domains_comboBox_2.currentIndexChanged.connect(self.SelectDomains)
        self.Depletable_Mat_CB.currentIndexChanged.connect(self.SelectMaterials)
        self.ExportData_PB.clicked.connect(self.Export_to_Main_Window)
        self.tabWidget.currentChanged.connect(self.Widget_ToolTips)
        self.tabWidget.currentChanged.connect(self.Widget_Set)
        self.Integrator_CB.currentIndexChanged.connect(self.Widget_ToolTips)
        self.ReduceChain_CB.toggled.connect(self.Widget_Set1)
        self.ReduceChain_CB_2.toggled.connect(self.Widget_Set1)
        self.NormMod_CB.currentIndexChanged.connect(self.Widget_Set)
        self.NormMod_CB_2.currentIndexChanged.connect(self.Widget_Set)
        self.FissYieldMode_CB.currentIndexChanged.connect(self.Widget_Set)
        self.RRMode_CB.currentIndexChanged.connect(self.Widget_Set)
        self.Get_XS_Flux_CB.toggled.connect(self.Widget_Set)
        self.Flux_Energy_Gr_CB.currentIndexChanged.connect(self.Widget_Set)
        self.Flux_Energy_Gr_CB_2.currentIndexChanged.connect(self.Widget_Set)
        self.Decay_Only_CB.toggled.connect(self.Widget_Set)
        self.Load_XS_PB.clicked.connect(self.read_micro_xs)
        self.ClearData_PB.clicked.connect(self.Clear_Output)
        self.Exit_PB.clicked.connect(self.Exit)
        self.Widget_Set()
        self.Widget_ToolTips()

    def SelectNuclides(self):
        if self.tabWidget.currentIndex() == 1:
            Chain = self.directory + '/' + self.Chain_CB_2.currentText()
            if not os.path.isfile(Chain):
                self.showDialog('Warning', 'File ' + self.Chain_CB_2.currentText() + " doesn't exist!" )
                for i in range(len(self.Nuclides_comboBox)):
                    self.Nuclides_comboBox.setItemChecked(i, False)
                    self.Nuclides_comboBox.setCurrentIndex(0)
                return
            try:
                if self.Nuclides_comboBox.currentIndex() == 1:
                    if self.Nuclides_comboBox.checkedItems():
                        Checked_Nuclides_bins = self.Nuclides_comboBox.checkedItems()
                    else:
                        Checked_Nuclides_bins = []
                    if Checked_Nuclides_bins:
                        Checked_Nuclides_bins.pop(0)
                elif self.Nuclides_comboBox.currentIndex() > 1:
                    Checked_Nuclides_bins = self.Nuclides_comboBox.checkedItems()
                self.Checked_Nuclides = [elm for elm in self.Nuclides if self.Nuclides.index(elm) + 2 in Checked_Nuclides_bins]
                self.Nuclides_LE.setText(str(self.Checked_Nuclides))   #.replace("'", ""))
                Nuclides = [nc for nc in self.Checked_Nuclides]
                self.Reactions = self.Extract_Reactions_From_Depletion_Chain(Chain, Nuclides)
                self.Reactions_comboBox.clear()
                if 'Select reactions' not in self.Reactions:
                    self.Reactions.insert(0, 'Select reactions')
                if 'All bins' not in self.Reactions:
                    self.Reactions.insert(1, 'All bins')
                self.Reactions_comboBox.addItems(self.Reactions)
                if self.Reactions_comboBox.model().item(0):
                    self.Reactions_comboBox.model().item(0).setEnabled(False)
                    self.Reactions_comboBox.model().item(0).setCheckState(Qt.Unchecked)
                for i in range(len(self.Reactions) + 1):
                    self.Reactions_comboBox.setItemChecked(i, False)
            except:
                pass
            self.Nuclides_comboBox.setCurrentIndex(0)
        elif self.tabWidget.currentIndex() == 2:
            Chain = self.directory + '/' + self.Chain_CB_3.currentText()
            if not os.path.isfile(Chain):
                self.showDialog('Warning', 'File ' + self.Chain_CB_3.currentText() + " doesn't exist!" )
                for i in range(len(self.Nuclides_comboBox_2)):
                    self.Nuclides_comboBox_2.setItemChecked(i, False)
                    self.Nuclides_comboBox_2.setCurrentIndex(0)
                return
            try:
                if self.Nuclides_comboBox_2.currentIndex() == 1:
                    if self.Nuclides_comboBox_2.checkedItems():
                        Checked_Nuclides_bins = self.Nuclides_comboBox_2.checkedItems()
                    else:
                        Checked_Nuclides_bins = []
                    if Checked_Nuclides_bins:
                        Checked_Nuclides_bins.pop(0)
                elif self.Nuclides_comboBox_2.currentIndex() > 1:
                    Checked_Nuclides_bins = self.Nuclides_comboBox_2.checkedItems()
                self.Checked_Nuclides_2 = [elm for elm in self.Nuclides if self.Nuclides.index(elm) + 2 in Checked_Nuclides_bins]
                self.Nuclides_LE_2.setText(str(self.Checked_Nuclides_2))   #.replace("'", ""))
                Nuclides = [nc for nc in self.Checked_Nuclides_2]
                self.Reactions = self.Extract_Reactions_From_Depletion_Chain(Chain, Nuclides)
                self.Reactions_comboBox_2.clear()
                if 'Select reactions' not in self.Reactions:
                    self.Reactions.insert(0, 'Select reactions')
                if 'All bins' not in self.Reactions:
                    self.Reactions.insert(1, 'All bins')
                self.Reactions_comboBox_2.addItems(self.Reactions)
                if self.Reactions_comboBox_2.model().item(0):
                    self.Reactions_comboBox_2.model().item(0).setEnabled(False)
                    self.Reactions_comboBox_2.model().item(0).setCheckState(Qt.Unchecked)
                for i in range(len(self.Reactions) + 1):
                    self.Reactions_comboBox_2.setItemChecked(i, False)
            except:
                pass
            self.Nuclides_comboBox_2.setCurrentIndex(0)

    def Extract_Reactions_From_Depletion_Chain(self, Chain, Nuclides):
        import xml.etree.ElementTree as ET
        # Load the depletion chain XML
        tree = ET.parse(Chain)
        root = tree.getroot()
        # Find the nuclide element
        reaction_types = {}
        reactions = set()  # Using a set to avoid duplicates
        for NC in Nuclides:
            reaction_types[NC] = []
            for nuclide in root.findall("nuclide"):
                if nuclide.get("name") == NC:
                    #print(f"Reactions for {NC}:")
                    for reaction in nuclide.findall("reaction"):
                        rx_type = reaction.get("type")
                        target = reaction.get("target")
                        q_val = reaction.get("Q")
                        #print(f"  Type: {rx_type}, Target: {target}, Q: {q_val}")
                        reaction_types[NC].append(rx_type)
                        reactions.add(rx_type)
                    break
        return sorted(reactions)

    def SelectReactions(self):
        if self.tabWidget.currentIndex() == 1:
            try:
                if self.Reactions_comboBox.currentIndex() == 1:
                    if self.Reactions_comboBox.checkedItems():
                        Checked_Reactions_bins = self.Reactions_comboBox.checkedItems()
                    else:
                        Checked_Reactions_bins = []
                    if Checked_Reactions_bins:
                        Checked_Reactions_bins.pop(0)
                elif self.Reactions_comboBox.currentIndex() > 1:
                    Checked_Reactions_bins = self.Reactions_comboBox.checkedItems()
                self.Checked_Reactions = [elm for elm in self.Reactions[2:] if self.Reactions.index(elm) in Checked_Reactions_bins]
                self.Reactions_LE.setText(str(self.Checked_Reactions))   #.replace("'", ""))
            except:
                pass
            self.Reactions_comboBox.setCurrentIndex(0)
        elif self.tabWidget.currentIndex() == 2:
            try:
                if self.Reactions_comboBox_2.currentIndex() == 1:
                    if self.Reactions_comboBox_2.checkedItems():
                        Checked_Reactions_bins = self.Reactions_comboBox_2.checkedItems()
                    else:
                        Checked_Reactions_bins = []
                    if Checked_Reactions_bins:
                        Checked_Reactions_bins.pop(0)
                elif self.Reactions_comboBox_2.currentIndex() > 1:
                    Checked_Reactions_bins = self.Reactions_comboBox_2.checkedItems()
                self.Checked_Reactions_2 = [elm for elm in self.Reactions[2:] if self.Reactions.index(elm)  in Checked_Reactions_bins]
                self.Reactions_LE_2.setText(str(self.Checked_Reactions_2))  #.replace("'", ""))
            except:
                pass
            self.Reactions_comboBox_2.setCurrentIndex(0)

    def SelectDomains(self):
        if self.tabWidget.currentIndex() == 1:
            #self.Checked_Domains = []
            try:
                if self.Domains_comboBox.currentIndex() == 1:
                    if self.Domains_comboBox.checkedItems():
                        Checked_Domains_bins = self.Domains_comboBox.checkedItems()
                    else:
                        Checked_Domains_bins = []
                    if Checked_Domains_bins:
                        Checked_Domains_bins.pop(0)
                elif self.Domains_comboBox.currentIndex() > 1:
                    Checked_Domains_bins = self.Domains_comboBox.checkedItems()
                self.Checked_Domains = [elm for elm in self.Depletable_Cells if self.Depletable_Cells.index(elm) + 2 in Checked_Domains_bins]
                self.Depl_Domains_LE.clear()
                self.Depl_Domains_LE.setText(str(self.Checked_Domains).replace("'", ""))
            except:
                pass
            self.Domains_comboBox.setCurrentIndex(0)
        elif self.tabWidget.currentIndex() == 2:
            #self.Checked_Domains_2 = []
            try:
                if self.Domains_comboBox_2.currentIndex() == 1:
                    if self.Domains_comboBox_2.checkedItems():
                        Checked_Domains_bins = self.Domains_comboBox_2.checkedItems()
                    else:
                        Checked_Domains_bins = []
                    if Checked_Domains_bins:
                        Checked_Domains_bins.pop(0)
                elif self.Domains_comboBox_2.currentIndex() > 1:
                    Checked_Domains_bins = self.Domains_comboBox_2.checkedItems()
                self.Checked_Domains_2 = [elm for elm in self.Depletable_Cells if self.Depletable_Cells.index(elm) + 2 in Checked_Domains_bins]
                self.Depl_Domains_LE_2.clear()
                self.Depl_Domains_LE_2.setText(str(self.Checked_Domains_2).replace("'", ""))
            except:
                pass
            self.Domains_comboBox_2.setCurrentIndex(0)

    def SelectMaterials(self):
        #self.Depletable_Mats_LE.clear()
        #self.Checked_Depletable_Mats = []
        try:
            if self.Depletable_Mat_CB.currentIndex() == 1:
                if self.Depletable_Mat_CB.checkedItems():
                    Checked_Depletable_Mats_Bins = self.Depletable_Mat_CB.checkedItems()
                else:
                    Checked_Depletable_Mats_Bins = []
                if Checked_Depletable_Mats_Bins:
                    Checked_Depletable_Mats_Bins.pop(0)
            elif self.Depletable_Mat_CB.currentIndex() > 1:
                Checked_Depletable_Mats_Bins = self.Depletable_Mat_CB.checkedItems()
            self.Checked_Depletable_Mats = [elm for elm in self.Depletable_Mats if self.Depletable_Mats.index(elm) + 2 in Checked_Depletable_Mats_Bins]
            self.Depletable_Mats_LE.clear()
            self.Depletable_Mats_LE.setText(str(self.Checked_Depletable_Mats).replace("'", ""))
        except:
            pass
        self.Depletable_Mat_CB.setCurrentIndex(0)

    def Insert_Header_Text(self):
        self.Find_string(self.plainTextEdit, "import openmc")
        self.v_1.moveCursor(QTextCursor.End)
        if self.Insert_Header:
            self.Find_string(self.v_1, "import openmc")
            if self.Insert_Header:
                cursor = self.v_1.textCursor()
                cursor.setPosition(0)
                self.v_1.setTextCursor(cursor)
                self.v_1.insertPlainText('import openmc\n')
        self.Find_string(self.plainTextEdit, "depletion calculation")
        if self.Insert_Header:
            self.Find_string(self.v_1, "depletion calculation")
            if self.Insert_Header:
                self.v_1.moveCursor(QTextCursor.End)
                self.v_1.insertPlainText('\n############################################################################### \n')
                self.v_1.insertPlainText('#                 Initialize and run depletion calculation                        \n')
                self.v_1.insertPlainText('###############################################################################\n')
        self.Insert_Header = False

    def Reset_Fields(self):
        from PyQt5.QtCore import QSettings
        self.checkboxes = {}; self.checkboxes_2 = {}; self.checkboxes_3 = {}; self.comboboxes = {}
        self.comboboxes_2 = {}; self.comboboxes_3 = {}; self.LineEdits = {}; self.LineEdits_2 = {}
        self.LineEdits_3 = {}
        settings = QSettings("OpenMC", "ERSN")
        if self.tabWidget.currentIndex() == 0:
            CBs = [self.ReduceChain_CB, self.Prev_Res_CB, self.DiffBurnMats_CB]
            ComboBs = [self.Chain_CB, self.NormMod_CB, self.FissYieldMode_CB, self.Diff_Vol_Meth_CB, self.RRMode_CB]
            LEs = [self.Fission_Q_LE, self.FissYieldOpts_LE, self.RR_Opts_LE]
            for CB in CBs:
                name = CB.objectName()
                self.checkboxes[name] = CB
                settings.setValue(name, CB.isChecked())
            for CB in ComboBs:
                name = CB.objectName()
                self.comboboxes[name] = CB
                settings.setValue(name, CB.currentIndex())
            for LE in LEs:
                name = LE.objectName()
                self.LineEdits[name] = LE
                settings.setValue(name, LE.text())
            settings.setValue(self.RedChainLevel_SP.objectName(), self.RedChainLevel_SP.value())
        elif self.tabWidget.currentIndex() == 1:
            CBs = [self.Decay_Only_CB, self.ReduceChain_CB_2, self.Prev_Res_CB_2, self.Get_XS_Flux_CB]
            LEs = [self.Fission_Q_LE_2, self.FissYieldOpts_LE_2, self.Depl_Domains_LE, self.Nuclides_LE, self.Fluxes_LE, self.Reactions_LE]
            ComboBs = [self.Chain_CB_2, self.NormMod_CB_2, self.Flux_Energy_Gr_CB, self.Nuclides_comboBox, self.Domains_comboBox, self.Reactions_comboBox]
            for CB in CBs:
                name = CB.objectName()
                self.checkboxes_2[name] = CB
                settings.setValue(name, CB.isChecked())
            for CB in ComboBs:
                name = CB.objectName()
                self.comboboxes_2[name] = CB
                settings.setValue(name, CB.currentIndex())
            for LE in LEs:
                name = LE.objectName()
                self.LineEdits_2[name] = LE
                settings.setValue(name, LE.text())
            for i in range(len(self.Nuclides_comboBox)):
                self.Nuclides_comboBox.setItemChecked(i, False)
                self.Nuclides_comboBox.setCurrentIndex(0)
            for CB in CBs:
                CB.setChecked(False)
            for LE in LEs:
                LE.clear()
            for CB in ComboBs:
                CB.setCurrentIndex(0)
            settings.setValue(self.RedChainLevel_SP_2.objectName(), self.RedChainLevel_SP_2.value())
        elif self.tabWidget.currentIndex() == 2:
            CBs = [self.Save_Flux_CB, self.Save_XS_CB]
            ComboBs = [self.Chain_CB_3, self.Flux_Energy_Gr_CB_2, self.Domains_comboBox_2, self.Nuclides_comboBox_2, self.Reactions_comboBox_2]
            LEs = [self.Depl_Domains_LE_2, self.Nuclides_LE_2, self.Reactions_LE_2, self.Energies_LE]
            for CB in CBs:
                name = CB.objectName()
                self.checkboxes_3[name] = CB
                settings.setValue(name, CB.isChecked())
            for CB in ComboBs:
                name = CB.objectName()
                self.comboboxes_3[name] = CB
                settings.setValue(name, CB.currentIndex())
            for LE in LEs:
                name = LE.objectName()
                self.LineEdits_3[name] = LE
                settings.setValue(name, LE.text()) 

        if self.tabWidget.currentIndex() == 0:
            for CB in CBs:
                CB.setChecked(False)
            for LE in LEs:
                LE.clear()
            for CB in ComboBs:
                CB.setCurrentIndex(0)
            self.RedChainLevel_SP.setValue(0)
        if self.tabWidget.currentIndex() == 1:
            for CB in CBs:
                CB.setChecked(False)
            for LE in LEs:
                LE.clear()
            for CB in ComboBs:
                CB.setCurrentIndex(0)
            self.RedChainLevel_SP_2.setValue(0)
            self.Reactions_comboBox.clear()
        elif self.tabWidget.currentIndex() == 2:   
            for CB in CBs:
                CB.setChecked(False) 
            for LE in LEs:
                LE.clear()
            for CB in ComboBs:
                CB.setCurrentIndex(0)  
            self.Reactions_comboBox_2.clear()          

    def Undo_Reset(self):
        settings = QSettings("OpenMC", "ERSN")
        if self.tabWidget.currentIndex() == 0:
            for name, CB in self.checkboxes.items():
                CB.setChecked(settings.value(name, False, type=bool))
            for name, CB in self.comboboxes.items():
                saved_index = settings.value(name, 0, type=int)
                CB.setCurrentIndex(saved_index)
            for name, LE in self.LineEdits.items():
                saved_text = settings.value(name, 0, type=str)
                LE.setText(saved_text)
            self.RedChainLevel_SP.setValue(settings.value(self.RedChainLevel_SP.objectName(), 0, type=int))
        elif self.tabWidget.currentIndex() == 1:
            for name, CB in self.checkboxes_2.items():
                CB.setChecked(settings.value(name, False, type=bool))
            for name, CB in self.comboboxes_2.items():
                saved_index = settings.value(name, 0, type=int)
                CB.setCurrentIndex(saved_index)
            for name, LE in self.LineEdits_2.items():
                saved_text = settings.value(name, 0, type=str)
                LE.setText(saved_text)
            self.RedChainLevel_SP_2.setValue(settings.value(self.RedChainLevel_SP_2.objectName(), 0, type=int))
        elif self.tabWidget.currentIndex() == 2:
            for name, CB in self.checkboxes_3.items():
                CB.setChecked(settings.value(name, False, type=bool))
            for name, CB in self.comboboxes_3.items():
                saved_index = settings.value(name, 0, type=int)
                CB.setCurrentIndex(saved_index)
            for name, LE in self.LineEdits_3.items():
                saved_text = settings.value(name, 0, type=str)
                LE.setText(saved_text)

    def Add_Depletion(self):
        if self.Geom_LE.text() == '':
            self.showDialog('Warning', 'Cannot create a model, enter Geometry name first !')
            return
        elif self.Sett_LE.text() == '':
            self.showDialog('Warning', 'Cannot create a model, enter Settings name first !')
            return
        elif self.Mats_LE.text() == '':
            self.showDialog('Warning', 'Cannot create a model, enter Materials name first !')
            return
        
        if self.tabWidget.currentIndex() in [0, 1]:  # Coupled and Independent Operators only    
            if not self.TimeSteps_LE.text():
                self.showDialog('Warning', 'Make sure the time steps are entered!' )
                return
            if not self.Power_LE.text():
                self.showDialog('Warning', 'Make sure the power value is entered!' )
                return

            time_steps = self.LE_to_List(self.TimeSteps_LE)
            power_values = self.LE_to_List(self.Power_LE)
            if len(time_steps) != len(power_values) and len(power_values) != 1:
                self.showDialog('Warning', 'Make sure the time steps and power values \nlists have the same length!' )
                return

            if self.TimeUnit_CB.currentText() == 'd':
                T_Fact = 1.
            elif self.TimeUnit_CB.currentText() == 'h':
                T_Fact = 1./24.
            elif self.TimeUnit_CB.currentText() == 'min':
                T_Fact = 1./24./60.
            elif self.TimeUnit_CB.currentText() == 's':
                T_Fact = 1./24./3600.

            if self.Power_Unit_CB.currentText() == 'W':
                P_Fact = 1.
            elif self.Power_Unit_CB.currentText() == 'KW':
                P_Fact = 1.E3
            elif self.Power_Unit_CB.currentText() == 'MW':
                P_Fact = 1.E6

            try:
                time_steps = [float(time) * T_Fact for time in time_steps]
            except:
                self.showDialog('Warning', 'Make sure the time steps are digits!' )       

            try:
                power = [float(p) * P_Fact for p in power_values]
            except:
                self.showDialog('Warning', 'Make sure the Power value is valid!' )

            if len(power_values) == 1:
                power = power_values[0]

            if self.Depletable_Mats_LE.text() == '':
                self.showDialog('Warning', 'Depletable material must be selected!')
                return        
            
            if self.Volume_LE.text() != "":
                Volumes = self.LE_to_List(self.Volume_LE)
            else:
                self.showDialog('Warning', 'Volume must be given!')
                return

            if len(Volumes) != len(self.Checked_Depletable_Mats):
                self.showDialog('Warning', str(len(self.Checked_Depletable_Mats)) + ' volumes must be given!')
                return

            if self.Get_XS_Flux_CB.isChecked() and self.Flux_Energy_Gr_CB.currentIndex() == 0:
                self.showDialog('Warning', 'Select an energy group structure or enter energy group boundaries in [eV]!')
                return

            Volume_Strings = []
            Doc = self.v_1.toPlainText()
            for mat in self.Checked_Depletable_Mats:
                Vol_Prefix = mat + '.volume'
                if Vol_Prefix not in Doc or '#' + Vol_Prefix in Doc:
                    Volume_Strings.append(mat + '.volume = ' + Volumes[self.Checked_Depletable_Mats.index(mat)])

        self.Chain_File = self.Chain_CB.currentText()

        if self.tabWidget.currentIndex() == 0:   # Coupled operator
            if self.Prev_Res_CB.isChecked():
                Results_Str = "\nResults = openmc.deplete.Results('depletion_results.h5')"
                prev_res = ', prev_results=Results'
            else:
                Results_Str = ""
                prev_res = ""
            
            if self.ReduceChain_CB.isChecked():
                reduce_chain = ', reduce_chain=True'
                if self.RedChainLevel_SP.value() == 0:
                    reduce_chain_level = ', reduce_chain_level=None' 
                else:
                    reduce_chain_level = ', reduce_chain_level=' + str(self.RedChainLevel_SP.value())
            else:
                reduce_chain = ""
                reduce_chain_level = ""
                
            if self.NormMod_CB.currentIndex() != 0:
                normalization_mode = ', normalization_mode=' + f'"{self.NormMod_CB.currentText()}"'
            else:
                normalization_mode = ""
            
            if self.NormMod_CB.currentText() == 'fission-q':
                if self.Fission_Q_LE.text() != "":
                    if not self.is_dict_syntax(self.Fission_Q_LE.text()):
                        alert = "Warning"
                        msg = 'Fission-Q must be entered as a dictionary of nuclides as keys and their fission-q!' +\
                            '\n Choose an option!'
                        response = self.question1(alert, msg, "Modify entry", "Use default data")
                        if response == 0:
                            return
                        elif response == 1:
                            Fission_Q = ""
                    else:
                        Fission_Q = ', fission_q=' + self.Fission_Q_LE.text()
                else:
                    self.Fission_Q_LE.clear()
                    Fission_Q = ""
            else:
                Fission_Q = ""

            if self.FissYieldOpts_LE.text() != "":
                if not self.is_dict_syntax(self.FissYieldOpts_LE.text()):
                    alert = "Warning"
                    msg = 'Options must be entered as a dictionary with "energy" key !' +\
                        '\nie: fission_yield_opts={"energy":500e3} \n Choose an option!'
                    response = self.question1(alert, msg, "Modify entry", "Use default data")
                    if response == 0:
                        return
                    elif response == 1:
                        self.FissYieldOpts_LE.clear()
                        FissYieldOpts = ""
                else:
                    FissYieldOpts = ', fission_yield_opts=' + self.FissYieldOpts_LE.text()
            else:
                FissYieldOpts = ""

            if self.DiffBurnMats_CB.isChecked():
                diff_burnable_mats = ', diff_burnable_mats=True'
            else:
                diff_burnable_mats = ""
            
            if self.Diff_Vol_Meth_CB.currentIndex() != 0:
                diff_volume_method = ', diff_volume_method=' + f'"{self.Diff_Vol_Meth_CB.currentText()}"'
            else:                       
                diff_volume_method = ""

            if self.FissYieldMode_CB.currentIndex() != 0:
                Fission_Yield_Mode = ', fission_yield_mode=' + f'"{self.FissYieldMode_CB.currentText()}"'
            else:                       
                Fission_Yield_Mode = ""

            if self. RRMode_CB.currentIndex() != 0:
                Reaction_Rate_Mode = ', reaction_rate_mode=' + f'"{self.RRMode_CB.currentText()}"'
            else:
                Reaction_Rate_Mode = ""

            if self.RRMode_CB.currentText() == 'flux':
                if self.RR_Opts_LE.text() != "":
                    if not self.is_dict_syntax(self.RR_Opts_LE.text()):
                        alert = "Warning"
                        msg = 'Reaction rate options must be entered as a dictionary. Energy group boundaries can be set using the “energies” key !' +\
                            ' ie: reaction_rate_opts={"energies":[1, 500e3]} \n Choose an option!'
                        response = self.question1(alert, msg, "Modify entry", "Change RR mode")
                        if response == 0:
                            return
                        elif response == 1:
                            self.RRMode_CB.setCurrentIndex(0)
                            ReactionRrateOpts = ""
                            return
                    else:
                        ReactionRrateOpts = ', reaction_rate_opts=' + self.RR_Opts_LE.text()               
            else:
                ReactionRrateOpts = ""
        elif self.tabWidget.currentIndex() == 1:   # Independent operator:
            if self.Prev_Res_CB_2.isChecked():
                Results_Str = "\nResults = openmc.deplete.Results('depletion_results.h5')"
                prev_res = ', prev_results=Results'
            else:
                Results_Str = ""
                prev_res = ""
            
            if self.ReduceChain_CB_2.isChecked():
                reduce_chain = ', reduce_chain=True'
                if self.RedChainLevel_SP_2.value() == 0:
                    reduce_chain_level = ', reduce_chain_level=None' 
                else:
                    reduce_chain_level = ', reduce_chain_level=' + str(self.RedChainLevel_SP_2.value())
            else:
                reduce_chain = ""
                reduce_chain_level = ""
                
            if self.NormMod_CB_2.currentIndex() != 0:
                normalization_mode = ', normalization_mode=' + f'"{self.NormMod_CB_2.currentText()}"'
            else:
                normalization_mode = ""
            
            if self.NormMod_CB_2.currentText() == 'fission-q':
                if self.Fission_Q_LE_2.text() != "":
                    if not self.is_dict_syntax(self.Fission_Q_LE_2.text()):
                        alert = "Warning"
                        msg = 'Fission-Q must be entered as a dictionary of nuclides as keys and their fission-q!' +\
                            '\n Choose an option!'
                        response = self.question1(alert, msg, "Modify entry", "Use default data")
                        if response == 0:
                            return
                        elif response == 1:
                            Fission_Q = ""
                    else:
                        Fission_Q = ', fission_q=' + self.Fission_Q_LE_2.text()
                else:
                    self.Fission_Q_LE_2.clear()
                    Fission_Q = ""
            else:
                Fission_Q = ""

            if self.FissYieldOpts_LE_2.text() != "":
                if not self.is_dict_syntax(self.FissYieldOpts_LE_2.text()):
                    alert = "Warning"
                    msg = 'Options must be entered as a dictionary with "energy" key !' +\
                        '\nie: fission_yield_opts={"energy":500e3} \n Choose an option!'
                    response = self.question1(alert, msg, "Modify entry", "Use default data")
                    if response == 0:
                        return
                    elif response == 1:
                        self.FissYieldOpts_LE_2.clear()
                        FissYieldOpts = ""
                else:
                    FissYieldOpts = ', fission_yield_opts=' + self.FissYieldOpts_LE_2.text()
            else:
                FissYieldOpts = ""
        elif self.tabWidget.currentIndex() == 2:   # get flux and XS
            if self.Energies_LE.text() == "":
                self.showDialog('Warning', 'Energy group boundaries in [eV] or the name of the group structure must be given!')
                return

        # add Operator parameters
        self.Insert_Header_Text()
        # add depletion settings to model input script
        print ("\n"+ self.Model_LE.text() + " = openmc.Model(geometry=" + self.Geom_LE.text() + ", materials=" + \
                                                    self.Mats_LE.text()  + ", settings=" + self.Sett_LE.text() + ")\n")
        
        if self.tabWidget.currentIndex() == 0:     # CoupledOperator
            for vol_str in Volume_Strings:  
                print(vol_str + '\n')
            print("\n# Create depletion operator")
            print("\n" + self.Operator_LE.text() + " = openmc.deplete." + self.tabWidget.tabText(self.tabWidget.currentIndex()) + "(" + \
                                         self.Model_LE.text() + ", '" + self.Chain_File + "'" + prev_res + \
                                         diff_burnable_mats + diff_volume_method + normalization_mode + Fission_Q + \
                                         Fission_Yield_Mode + FissYieldOpts + Reaction_Rate_Mode + ReactionRrateOpts + \
                                         reduce_chain + reduce_chain_level + ")" )
        elif self.tabWidget.currentIndex() == 1:   # IndependentOperator
            for vol_str in Volume_Strings:  
                print(vol_str + '\n')
            print("\n# Create depletion operator")
            print("openmc.config['chain_file'] = " + self.Chain_File)
            print('Materials = openmc.Materials(' + self.Depletable_Mats_LE.text() + ')')

            if self.Get_XS_Flux_CB.isChecked():
                En = self.LE_to_List(self.Fluxes_LE)
                if all(self.is_number(E) for E in En):
                    print('energies = ' + str([float(E) for E in En]))
                else:
                    print('energies = ' + f'"{self.Fluxes_LE.text()}"')
                print('nuclides = ' + f'{self.Nuclides_LE.text()}')
                print('flux_in_each_group, micro_xs = openmc.deplete.get_microxs_and_flux(model=' + self.Model_LE.text() + \
                  ', domains=' + self.Depl_Domains_LE.text() + ', nuclides=nuclides' + ', energies=energies' + ')')
            else:                  
                flux = [float(f) for f in self.LE_to_List(self.Fluxes_LE)]
                print('flux_in_each_group = ' + str(flux))
                if self.micro_XS_string != '':
                    print('micro_xs = ' + f'"{self.micro_XS_string}"')
                else:
                    print('micro_xs = ""')
            print("\n" + self.Operator_LE.text() + " = openmc.deplete." + self.tabWidget.tabText(self.tabWidget.currentIndex()) + "(" + \
                                         "Materials, fluxes=flux_in_each_group, micros=micro_xs" + ', ' +\
                                         "'" + self.Chain_File + "'" + prev_res + normalization_mode + Fission_Q + FissYieldOpts + ")" )
        elif self.tabWidget.currentIndex() == 2:   # Get microXS and Flux only
            print("\n# Generate a microscopic cross sections and flux from a Model")
            print("openmc.config['chain_file'] = '" + self.Chain_File + "'")
            En = self.LE_to_List(self.Energies_LE)
            if self.Depl_Domains_LE_2.text() != '[]' and self.Depl_Domains_LE_2.text() != "":
                print('domains = ' + f'{self.Depl_Domains_LE_2.text()}')
                Domains_String = ', domains=domains' 
            else: 
                Domains_String = ''
            if self.Nuclides_LE_2.text() != '[]' and self.Nuclides_LE_2.text() != "":
                print('nuclides = ' + f'{self.Nuclides_LE_2.text()}')
                Nuclides_String = ', nuclides=nuclides'
            else:
                Nuclides_String = ''
            if self.Reactions_LE_2.text() != '[]' and self.Reactions_LE_2.text() != "":
                print('reactions = ' + f'{self.Reactions_LE_2.text()}')
                Reactions_String = ', reactions=reactions'
            else:
                Reactions_String = ''
            if all(self.is_number(E) for E in En):
                print('energies = ' + str([float(E) for E in En]))
            else:
                print("energies = openmc.mgxs.GROUP_STRUCTURES[" + f'"{self.Energies_LE.text()}"' + "][:-1]")
            print('flux_in_each_group, micro_xs = openmc.deplete.get_microxs_and_flux(model=' + self.Model_LE.text() + \
                Domains_String + Nuclides_String + Reactions_String + ', energies=energies' + ')')
            if self.Save_XS_CB.isChecked():
                print('# will export XS to csv file')
                print("for cell in domains:\n \tmicro_xs[domains.index(cell)].to_csv(f'XS_{cell.fill.name}.csv')")
            if self.Save_Flux_CB.isChecked():
                print('# will export Flux to csv file')
                print('for cell in domains:')
                print('\theader = f"Energy [eV]\tFlux in {cell.fill.name} [n-cm/src)"')
                print('\tformatted_Flux = np.column_stack((energies[:-1], flux_in_each_group[domains.index(cell)])).astype(float)')
                print("\tnp.savetxt(f'Flux_in_{cell.fill.name}.csv', formatted_Flux, delimiter=',', header=header)")

            return

        print("\n# Perform simulation using the predictor algorithm")
        print("\ntime_steps = " + str(time_steps) + "     # in days")
        
        if self.Run_Mode == 'fixed source':
            print("\nSource_Rates = " + str(power) + "     # in Watts")
            print("\n" + self.Integrator_LE.text() + " = openmc.deplete." + self.Integrator_CB.currentText() + \
                                           "(op, time_steps, source_rates=Source_Rates, timestep_units='d')")
        elif self.Run_Mode == 'eigenvalue':
            print("\npower = " + str(power) + "     # in Watts")
            print("\n" + self.Integrator_LE.text() + " = openmc.deplete." + self.Integrator_CB.currentText() + \
                                           "(op, time_steps, power, timestep_units='d')") # + self.TimeUnit_CB.currentText() + ")")
        print("\nintegrator.integrate()")

    def is_number(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def Export_to_Main_Window(self):
        document = self.plainTextEdit.toPlainText()
        cursor = self.v_1.textCursor()
        cursor.insertText(document)
        self.text_inserted = True
        self.plainTextEdit.clear()
        if not os.path.isfile(self.directory + '/' + self.Chain_File): 
            self.showDialog('Warning', 'Make sure the file ' + self.Chain_File + ' exists!' )

        document = self.v_1.toPlainText()
        if 'from math import pi' not in document:
            document = document.replace('import openmc', 'import openmc \nfrom math import pi\n')
        else:
            lines = document.split('\n')
            for line in lines:
                if 'from math import pi' in line and line.strip().startswith('#'):
                    document = document.replace(line, line.replace(line[0], '', 1).lstrip())
                    break
        if 'import openmc.deplete' not in document:
            document = document.replace('import openmc', 'import openmc \nimport openmc.deplete\n')
        else:
            lines = document.split('\n')
            for line in lines:
                if 'import openmc.deplete' in line and line.strip().startswith('#'):
                    document = document.replace(line, line.replace(line[0], '', 1).lstrip())
                    break
        cursor = self.v_1.textCursor()
        self.v_1.clear()
        cursor.insertText(document)

    def LE_to_List(self, LineEdit):
        text = LineEdit.text()
        if '(' in text or ')' in text:
            text = text.strip('(').strip(')')
        if '[' in text or ']' in text:
            text = text.strip('[').strip(']')
        for separator in [',', ';', ':', ' ']:
            if separator in text:
                text = str(' '.join(text.replace(separator, ' ').split()))
        List = text.split()
        return List
    
    def Widget_ToolTips(self):
        self.tabWidget.setTabToolTip(0, 'Transport-coupled transport operator.')
        self.tabWidget.setTabToolTip(1, 'Transport-independent transport operator that uses one-group \
                                   \ncross sections to calculate reaction rates.')
        self.Integrator_CB.setItemData(0, 'Deplete using a first-order predictor algorithm.', QtCore.Qt.ToolTipRole)
        self.Integrator_CB.setItemData(1, 'Deplete using the CE/CM algorithm.', QtCore.Qt.ToolTipRole)
        self.Integrator_CB.setItemData(2, 'Deplete using the CE/LI CFQ4 algorithm.', QtCore.Qt.ToolTipRole)
        self.Integrator_CB.setItemData(3, 'Deplete using the CF4 algorithm.', QtCore.Qt.ToolTipRole)
        self.Integrator_CB.setItemData(4, 'Deplete using the EPC-RK4 algorithm.', QtCore.Qt.ToolTipRole)
        self.Integrator_CB.setItemData(5, 'Deplete using the LE/QI CFQ4 algorithm.', QtCore.Qt.ToolTipRole)
        self.Integrator_CB.setItemData(6, 'Deplete using the SI-CE/LI CFQ4 algorithm.', QtCore.Qt.ToolTipRole)
        self.Integrator_CB.setItemData(7, 'Deplete using the SI-LE/QI CFQ4 algorithm.', QtCore.Qt.ToolTipRole)
        self.NormMod_CB.setItemData(0, 'normalization_mode ({"energy-deposition", "fission-q", "source-rate"}) \
                                        \nIndicate how tally results should be normalized.', QtCore.Qt.ToolTipRole)
        self.NormMod_CB.setItemData(1, 'computes the total energy deposited in the system and uses the ratio of \
                                        \nthe power to the energy produced as a normalization factor.' \
                                       '\nMake sure your HDF5 files have heating data!', QtCore.Qt.ToolTipRole)
        self.NormMod_CB.setItemData(2, 'uses the fission Q values from the depletion chain to compute the total ' +\
                                        'energy deposited.', QtCore.Qt.ToolTipRole)
        self.NormMod_CB.setItemData(3, 'normalizes tallies based on the source rate (for fixed source calculations).', QtCore.Qt.ToolTipRole)
        self.Diff_Vol_Meth_CB.setItemData(0, 'Specifies how the volumes of the new materials should be found.', QtCore.Qt.ToolTipRole)
        self.Diff_Vol_Meth_CB.setItemData(1, 'Default is to "divide equally" which divides the original material' +\
                                              ' volume equally between the new materials.', QtCore.Qt.ToolTipRole)
        self.Diff_Vol_Meth_CB.setItemData(2, '‘match cell’ sets the volume of the material to volume of' +\
                                             ' the cell they fill.', QtCore.Qt.ToolTipRole)
        self.RRMode_CB.setItemData(0, 'reaction_rate_mode ({"direct", "flux"}, optional). Indicate how one-group reaction' + \
                                       ' rates should be calculated.', QtCore.Qt.ToolTipRole)
        self.RRMode_CB.setItemData(1, 'The “flux” method tallies a multigroup flux spectrum and then collapses one-group ' +\
                                        ' reaction rates after a transport \nsolve (with an option to tally some reaction ' +\
                                        ' rates directly).', QtCore.Qt.ToolTipRole)
        self.RRMode_CB.setItemData(2, 'The “direct” method tallies transmutation reaction rates directly.', QtCore.Qt.ToolTipRole)
        self.Diff_Vol_Meth_CB.setToolTip("Specifies how the volumes of the new materials should be found. \
                                        \nDefault is to ‘divide equally’ which divides the original material volume \
                                        equally between the new materials, ‘match cell’ sets the volume of the material \
                                        to volume of the cell they fill.")
        self.Fission_Q_LE.setToolTip('fission_q (dict, optional) Dictionary of nuclides and their fission Q values [eV]. \
                                      \nIf not given, values will be pulled from the chain_file.' + 
                                     '\nOnly applicable if "normalization_mode" == "fission-q". \nie : {"U235":190, "Pu239":200}')
        self.RR_Opts_LE.setToolTip('Reaction_rate_opts (dict, optional). Keyword arguments that are passed to the reaction rate helper class. \
                                    \nWhen reaction_rate_mode is set to “flux”, energy group boundaries can be set using the “energies” key. \
                                    \nSee the FluxCollapseHelper class for all options. ie : reaction_rate_opts={"energies":[1,500e3]}')
        self.Chain_CB.setToolTip('Make sure the choosen depletion chain file exists in the model directory!')
        self.FissYieldOpts_LE.setToolTip('Fission_yield_opts (dict of str to option, optional) – Optional arguments to pass to the '+\
                                ' openmc.deplete.helpers.FissionYieldHelper object. \nWill be passed directly on to the helper. \
                                \nie: fission_yield_opts={"energy":500e3}\
                                \nPassing a value of None will use the defaults for the associated helper.')
        self.DiffBurnMats_CB.setToolTip('The fuel pins towards the center of the problem will surely experience a more intense \
                                         \nneutron flux and greater reaction rates than those towards the edge of the domain. \
                                         \nThis indicates that the fuel in the center should be at a more depleted state than \
                                         \nperiphery pins, at least for the fist depletion step. However, without any other \
                                         \ninstructions, OpenMC will deplete fuel as a single material, and all of the fuel \
                                         \npins will have an identical composition at the next transport step.\
                                         \nIf diff_burnable_mats=True this would deplete fuel on the outer region of the problem\
                                         \nwith different reaction rates than those in the center. Materials will be depleted \
                                         \ncorresponding to their local neutron spectra, and have unique compositions at each \
                                         \ntransport step. The volume of the original fuel material must represent the volume \
                                         \nof all the fuel in the problem. When creating the unique materials, this volume will \
                                         \nbe equally distributed across all material instances.')

        if self.tabWidget.currentIndex() == 0:
            self.Volume_LE.setToolTip('Volume of domain in cc. As many volumes as checked materials must be entered !')
        elif self.tabWidget.currentIndex() == 1:
            self.Fluxes_LE.setToolTip('fluxes (list of numpy.ndarray) - Flux in each group in [n-cm/src] for each domain')
            self.Load_XS_PB.setToolTip('Load micros file .csv (list of MicroXS) - Cross sections in [b] for each domain. If the MicroXS' +\
                                        ' object is empty, a decay-only calculation will be run.')
    
    def read_micro_xs(self):
        micro_xs_file = QtWidgets.QFileDialog.getOpenFileName(self, "Select csv file", self.directory, "micro_xs file (*.csv)")[0]
        if os.path.isfile(micro_xs_file):
            micro_xs_file = os.path.basename(micro_xs_file)
            self.micro_XS_string = 'MicroXS.from_csv(' + micro_xs_file + ')'
        else:
            self.micro_XS_string = ''

    def Widget_Set(self):
        if self.tabWidget.currentIndex() == 0:
            if self.NormMod_CB.currentIndex() == 2:
                self.Fission_Q_LE.setEnabled(True)
            else:
                self.Fission_Q_LE.setEnabled(False)
            if self.FissYieldMode_CB.currentIndex() != 0:
                self.FissYieldOpts_LE.setEnabled(True)
            else:
                self.FissYieldOpts_LE.setEnabled(False)
        elif self.tabWidget.currentIndex() == 1:
            if self.NormMod_CB_2.currentIndex() == 1:
                self.Fission_Q_LE_2.setEnabled(True)
            else:
                self.Fission_Q_LE_2.setEnabled(False)
            self.NormMod_CB_2.model().item(1).setEnabled(False)
            for i in [1, 2]:
                self.NormMod_CB_2.model().item(i).setEnabled(True)

            Widgets = [self.label_19, self.label_29, self.label_31, self.Flux_Energy_Gr_CB, self.Depl_Domains_LE,
                       self.Nuclides_LE, self.Domains_comboBox, self.Nuclides_comboBox]

            if self.Get_XS_Flux_CB.isChecked():
                for W in Widgets:
                    W.setEnabled(True)
                
                if self.Flux_Energy_Gr_CB.currentIndex() == 0:
                    self.label_24.setText('Fluxes in [n-cm/src]')
                    self.Fluxes_LE.clear()
                elif self.Flux_Energy_Gr_CB.currentIndex() == 1:
                    self.label_24.setText('Energies in [eV]')
                    self.Fluxes_LE.setEnabled(True)
                else:
                    self.label_24.setText('Group structure')
                    self.Fluxes_LE.setText(self.Flux_Energy_Gr_CB.currentText())
                    self.Fluxes_LE.setEnabled(False)
            else:
                for W in Widgets:
                    W.setEnabled(False)
        elif self.tabWidget.currentIndex() == 2:
            if self.Flux_Energy_Gr_CB_2.currentIndex() == 1:
                self.label_35.setText('Energies in [eV]')
            elif self.Flux_Energy_Gr_CB_2.currentIndex() > 1:
                self.label_35.setText('Group structure')
                self.Energies_LE.setText(self.Flux_Energy_Gr_CB_2.currentText())

    def Widget_Set1(self, checked):
        if self.tabWidget.currentIndex() == 0:
            if checked:
                self.RedChainLevel_SP.setEnabled(True)
            else:
                self.RedChainLevel_SP.setEnabled(False)
        if self.tabWidget.currentIndex() == 1:
            if checked:
                self.RedChainLevel_SP_2.setEnabled(True)
            else:
                self.RedChainLevel_SP_2.setEnabled(False)

    def is_dict_syntax(self, s):
        try:
            # Attempt to parse the string into a Python literal
            result = ast.literal_eval(s)
            # Check if the result is a dictionary
            return isinstance(result, dict)
        except (ValueError, SyntaxError):
            # If a ValueError or SyntaxError occurs, it's not a valid dictionary
            return False

    def question(self, alert, msg) : 
        ret = QMessageBox.question(self, alert, msg,
                                   QMessageBox.Yes | QMessageBox.Discard | QMessageBox.Cancel)

        if ret == QMessageBox.Yes:
            return
        elif ret == QMessageBox.No:
            return
        elif ret == QMessageBox.Cancel:
            return 

    def question1(self, alert, msg, label1, label2):
        msg_box = QMessageBox()
        msg_box.setWindowTitle(alert)
        msg_box.setText(msg)
        yes_button = QPushButton(label1)
        no_button = QPushButton(label2)

        msg_box.addButton(yes_button, QMessageBox.YesRole)
        msg_box.addButton(no_button, QMessageBox.NoRole)
        response = msg_box.exec_()
        return response

    def Clear_Output(self):
        if self.text_inserted:
            self.plainTextEdit.clear()
        else:
            if self.plainTextEdit:
                qm = QMessageBox
                ret = qm.question(self, 'Warning', 'Do you really want to clear data ?', qm.Yes | qm.No)
                if ret == qm.Yes:
                    self.plainTextEdit.clear()
                elif ret == qm.No:
                    pass
            else:
                self.plainTextEdit.clear()

    def normalOutputWritten(self, text):
        self.highlighter = Highlighter(self.plainTextEdit.document())
        cursor = self.plainTextEdit.textCursor()
        cursor.insertText(text)


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

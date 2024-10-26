#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import os
import ast
from PyQt5 import QtCore
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
from src.syntax_py import Highlighter
from src.PyEdit import TextEdit, NumberBar  

class EmittingStream(QtCore.QObject):
    textWritten = QtCore.pyqtSignal(str)

    def write(self, text):
        self.textWritten.emit(str(text))
        pass

    def flush(self):
        pass

class ExportDepletion(QWidget):
    ###############################################################################
    #                   Initialize and run depletion calculation
    ###############################################################################
    from .func import resize_ui, showDialog, Exit, Find_string
    def __init__(self, v_1, Materials, Elements, Nuclides, Cells, Mats, Geom, Sett, Operator, Integrator, Model, parent=None):
        super(ExportDepletion, self).__init__(parent)
        #sys.stdout = EmittingStream(textWritten=self.normalOutputWritten)
        #sys.stderr = EmittingStream(textWritten=self.normalOutputWritten)
        uic.loadUi("src/ui/ExportDepletion.ui", self)
        self.v_1 = v_1 
        self.materials_name_list = Materials
        self.Model_Elements_List = Elements
        self.Model_Nuclides_List = Nuclides
        self.cell_name_list = Cells
        self.Mats = Mats
        self.Geom = Geom
        self.Sett = Sett
        self.Model = Model
        self.Integrator = Integrator
        self.Operator = Operator

        self.Geom_LE.setText(Geom)
        self.Mats_LE.setText(Mats)
        self.Sett_LE.setText(Sett)

        self.text_inserted = False
        self.Insert_Header = True
        self._initButtons()

        validator = QDoubleValidator(self)
        """for LineEd in [self.TimeSteps_LE, self.Power_LE]:
            LineEd.setValidator(validator)"""

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
        
        sys.stdout = EmittingStream(textWritten=self.normalOutputWritten)
        #sys.stderr = EmittingStream(textWritten=self.normalOutputWritten)
        # to show window at the middle of the screen and resize it to the screen size
        self.resize_ui()
         
    def _initButtons(self):
        self.CreateDepletion_PB.clicked.connect(self.Add_Depletion)
        self.ExportData_PB.clicked.connect(self.Export_to_Main_Window)
        self.Op_CB.currentIndexChanged.connect(self.Widget_ToolTips)
        self.Integrator_CB.currentIndexChanged.connect(self.Widget_ToolTips)
        self.NormMod_CB.currentIndexChanged.connect(self.Widget_Set)
        self.Op_CB.currentIndexChanged.connect(self.Widget_Set)
        self.ClearData_PB.clicked.connect(self.Clear_Output)
        self.Exit_PB.clicked.connect(self.Exit)
        self.Widget_Set()
        self.Widget_ToolTips()

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

    def Add_Depletion(self):
        self.Insert_Header_Text()
        if self.Geom_LE.text() == '':
            self.showDialog('Warning', 'Cannot create a model, enter Geometry name first !')
            return
        elif self.Sett_LE.text() == '':
            self.showDialog('Warning', 'Cannot create a model, enter Settings name first !')
            return
        elif self.Mats_LE.text() == '':
            self.showDialog('Warning', 'Cannot create a model, enter Materials name first !')
            return

        self.Chain_File = self.Chain_CB.currentText()
        if self.TimeUnit_CB.currentText() == 'd':
            T_Fact = 1.
        elif self.TimeUnit_CB.currentText() == 'h':
            T_Fact = 1./24.
        elif self.TimeUnit_CB.currentText() == 'min':
            T_Fact = 1./24./60.
        elif self.TimeUnit_CB.currentText() == 's':
            T_Fact = 1./24./3600.
        
        if not self.TimeSteps_LE.text():
            self.showDialog('Warning', 'Make sure the time steps are entered!' )
            return
        if not self.Power_LE.text():
            self.showDialog('Warning', 'Make sure the power value is entered!' )
            return
        time_steps = self.LE_to_List(self.TimeSteps_LE)
        try:
            time_steps = [float(time) * T_Fact for time in time_steps]
        except:
            self.showDialog('Warning', 'Make sure the time steps are digits!' )
        
        if self.Power_Unit_CB.currentText() == 'W':
            P_Fact = 1.
        elif self.Power_Unit_CB.currentText() == 'KW':
            P_Fact = 1.E3
        elif self.Power_Unit_CB.currentText() == 'MW':
            P_Fact = 1.E6
        try:
            power = float(self.Power_LE.text()) * P_Fact
        except:
            self.showDialog('Warning', 'Make sure the Power value is valid!' )
        
        if self.Prev_Res_CB.isChecked():
            prev_res = ', prev_res=Results'
        else:
            prev_res = ""

        if self.DiffBurnMats_CB.isChecked():
            diff_burnable_mats = ', diff_burnable_mats=True'
        else:
            diff_burnable_mats = ""
        
        if self.ReduceChain_CB.isChecked():
            reduce_chain = ', reduce_chain=True'
            if self.RedChainLevel_SP.value() == 0:
                reduce_chain_level = ', reduce_chain_level=None' 
            else:
                reduce_chain_level = ', reduce_chain_level=' + str(self.RedChainLevel_SP.value())
        else:
            reduce_chain = ""
            reduce_chain_level = ""
            
        if self.Diff_Vol_Meth_CB.currentIndex() != 0:
            diff_volume_method = ', diff_volume_method=' + f'"{self.Diff_Vol_Meth_CB.currentText()}"'
        else:                       
            diff_volume_method = ""

        if self.FissYieldMode_CB.currentIndex() != 0:
            Fission_Yield_Mode = ', fission_yield_mode=' + f'"{self.FissYieldMode_CB.currentText()}"'
        else:                       
            Fission_Yield_Mode = ""

        if self.NormMod_CB.currentIndex() != 0:
            normalization_mode = ', normalization_mode=' + f'"{self.NormMod_CB.currentText()}"'
        else:
            normalization_mode = ""
        
        if self.NormMod_CB.currentText() == 'fission-q':
            if self.Fission_Q_LE.text() != "":
                if not self.is_dict_syntax(self.Fission_Q_LE.text()):
                    alert = "Warning"
                    msg = 'Fission-Q must be entered as a dictionary of nuclides and their fission-q!' +\
                          '\n Choose an option!'
                    response = self.question1(alert, msg, "Modify entry", "Use default data")
                    if response == 0:
                        return
                    elif response == 1:
                        Fission_Q = ""
                else:
                    Fission_Q = ', fission_q=' + self.Fission_Q_LE.text()
            else:
                Fission_Q = ""
        else:
            Fission_Q = ""

        if self.RRMode_CB.currentIndex() != 0:
            reaction_rate_mode = ', reaction_rate_mode=' + f'"{self.RRMode_CB.currentText()}"'
        else:
            reaction_rate_mode = ""

        if self.Op_CB.currentText() == 'IndependentOperator':
            if self.From_Nuclide_CB.isChecked():
                if self.Volume_LE.text() != "":
                    volume = self.Volume_LE.text()
                else:
                    self.showDialog('Warning', 'Volume must be given!')
                    return

                if self.Nuclides_LE.text() != "":
                    if not self.is_dict_syntax(self.Fission_Q_LE.text()):
                        alert = "Warning"
                        msg = 'Nulides must be entered as a dictionary of nuclides and their atom densities!' +\
                            '\n Choose an option!'
                        response = self.question1(alert, msg, "Modify entry", "Use default data")
                        if response == 0:
                            return
                        elif response == 1:
                            nuclides = ""
                            From_Nuclides = ""
                    else:
                        nuclides = self.Nuclides_LE.text()
                        From_Nuclides = '.from_nuclides'
            else:
                From_Nuclides = ""
                nuclides = ""
        else:
            From_Nuclides = ""
            nuclides = ""

        if self.FissYieldMode_CB.currentIndex() != 0:
            if self.FissYieldOpts_LE.text() != "":
                if not self.is_dict_syntax(self.FissYieldOpts_LE.text()):
                    alert = "Warning"
                    msg = 'Options must be entered as a dictionary of nuclides and their atom densities!' +\
                        '\n Choose an option!'
                    response = self.question1(alert, msg, "Modify entry", "Use default data")
                    if response == 0:
                        return
                    elif response == 1:
                        nuclides = ""
                        From_Nuclides = ""
                else:
                    nuclides = self.Nuclides_LE.text()
                    From_Nuclides = '.from_nuclides'
        
        else:
            pass

        if self.FissYieldMode_CB.currentIndex() != 0:
                

            if self.FissYieldOpts_LE.text() != "":
                if not self.is_dict_syntax(self.FissYieldOpts_LE.text()):
                    alert = "Warning"
                    msg = 'Options must be entered as a dictionary of nuclides and their atom densities!' +\
                        '\n Choose an option!'
                    response = self.question1(alert, msg, "Modify entry", "Use default data")
                    if response == 0:
                        return
                    elif response == 1:
                        nuclides = ""
                        From_Nuclides = ""
                else:
                    nuclides = self.Nuclides_LE.text()
                    From_Nuclides = '.from_nuclides'
        
        else:
            pass



        # add depletion settings to model input script
        print ("\n"+ self.Model + " = openmc.Model(geometry=" + self.Geom_LE.text() + ", materials=" + \
                                                    self.Mats_LE.text()  + ", settings=" + self.Sett_LE.text() + ")")
        print("\n# Create depletion operator")
        
        # add Operator parameters
        if self.Op_CB.currentText() == 'CoupledOperator':
            print("\n" + self.Operator + " = openmc.deplete." + self.Op_CB.currentText() + From_Nuclides + "(" + \
                                         self.Model + ", '" + self.Chain_File + "'" + prev_res + \
                                         diff_burnable_mats + diff_volume_method + normalization_mode + Fission_Q + \
                                         Fission_Yield_Mode + reaction_rate_mode + reduce_chain + reduce_chain_level + ")" )
        elif self.self.Op_CB.currentText() == 'IndependentOperator':
            print("\n" + self.Operator + " = openmc.deplete." + self.Op_CB.currentText() + "(" + \
                                         self.Materials + ", fluxes, micros, '" + self.Chain_File + "'" + prev_res + \
                                         normalization_mode + Fission_Q + ")" )

        print("\n# Perform simulation using the predictor algorithm")
        print("\ntime_steps = " + str(time_steps) + "     # in days")
        print("\npower = " + str(float(power)) + "     # in Watts")
        print("\n" + self.Integrator + " = openmc.deplete." + self.Integrator_CB.currentText() + \
                                           "(op, time_steps, power, timestep_units='d')")
        print("\nintegrator.integrate()")

    def Export_to_Main_Window(self):
        document = self.plainTextEdit.toPlainText()
        cursor = self.v_1.textCursor()
        cursor.insertText(document)
        self.text_inserted = True
        self.plainTextEdit.clear()
        
        if not os.path.isfile(self.Chain_File.replace("'", "")):
            self.showDialog('Warning', 'Make sure the file ' + self.Chain_File + ' exists!' )

        """string_to_find = '.integrate()'
        self.Find_string(self.v_1, string_to_find)
        cursor = self.v_1.textCursor()
        self.plainTextEdit.moveCursor(QTextCursor.End)
        if self.Insert_Header:
            print('\n' + self.Plots + ' = openmc.Plots(','['+', '.join(self.plot_name_list)+']',')')
            print (string_to_find)
            document = self.plainTextEdit.toPlainText()
        else:
            document = self.v_1.toPlainText()
            lines = document.split('\n')
            for line in lines:
                if ("openmc.Plots" in line):
                    document = document.replace(line,"")
            print('\n' + self.Plots + ' = openmc.Plots(','['+', '.join(self.plot_name_list)+']',')')
            print(string_to_find)
            document = document.replace(string_to_find,self.plainTextEdit.toPlainText())
            self.v_1.clear()
        
        cursor.insertText(document)
        document = self.v_1.toPlainText()

        cursor = self.v_1.textCursor()
        self.v_1.clear()
        cursor.insertText(document)
        self.text_inserted = True
        self.plainTextEdit.clear()"""

    def LE_to_List(self, LineEdit):
        List = []
        text = LineEdit.text().replace('(', '').replace(')', '')
        for separator in [',', ';', ':', ' ']:
            if separator in text:
                text = str(' '.join(text.replace(separator, ' ').split()))
        List = text.split()
        return List
    
    def Widget_ToolTips(self):
        self.Op_CB.setItemData(0, 'Transport-coupled transport operator.', QtCore.Qt.ToolTipRole)
        self.Op_CB.setItemData(1, 'Transport-independent transport operator that uses one-group \
                                   \ncross sections to calculate reaction rates.', QtCore.Qt.ToolTipRole)
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
        self.Fission_Q_LE.setToolTip('fission_q (dict, optional) Dictionary of nuclides and their fission Q values [eV]. \
                                      \nIf not given, values will be pulled from the chain_file.' + 
                                     '\nOnly applicable if "normalization_mode" == "fission-q". \nie : {"U235":190, "Pu239":200}')
        self.RR_Opts_LE.setToolTip('reaction_rate_opts (dict, optional). Keyword arguments that are passed to the reaction rate helper class. \
                                    \nWhen reaction_rate_mode is set to “flux”, energy group boundaries can be set using the “energies” key. \
                                    \nSee the FluxCollapseHelper class for all options.')
        self.Chain_CB.setToolTip('Make sure the choosen depletion chain file exists in the model directory!')
        self.FissYieldOpts_LE.setToolTip('fission_yield_opts (dict of str to option, optional) – Optional arguments to pass to the '+\
                                ' openmc.deplete.helpers.FissionYieldHelper object. \nWill be passed directly on to the helper. \
                                \nPassing a value of None will use the defaults for the associated helper.')
        
        if self.Op_CB.currentText() == 'CoupledOperator':
            self.Nuclides_LE.setToolTip('Dictionary with nuclide names as keys and nuclide concentrations as values.')
            self.Volume_LE.setToolTip('Volume of domain in cc.')
        elif self.Op_CB.currentText() == 'IndependentOperator':
            self.Nuclides_LE.setToolTip('fluxes (list of numpy.ndarray) - Flux in each group in [n-cm/src] for each domain')
            self.Volume_LE.setToolTip('micros (list of MicroXS) - Cross sections in [b] for each domain. If the MicroXS' +\
                                        ' object is empty, a decay-only calculation will be run.')
            self.Keff_LE.setToolTip('keff (2-tuple of float, optional) - keff eigenvalue and uncertainty from transport '+ \
                                    'calculation. Default is None.')


    def Widget_Set(self):
        Widgets = [self.FissYieldMode_CB, self.RR_Opts_LE, self.RRMode_CB, self.label_14, self.label_8, self.label_10, 
                    self.DiffBurnMats_CB, self.label_11, self.Diff_Vol_Meth_CB]
        if self.NormMod_CB.currentIndex() == 2:
            self.Fission_Q_LE.setEnabled(True)
        else:
            self.Fission_Q_LE.setEnabled(False)
        if self.Op_CB.currentText() == 'CoupledOperator':
            for Widget in Widgets:
                Widget.setEnabled(True)
            self.Keff_LE.hide()
            self.From_Nuclide_CB.show()
            self.label_19.hide()
            self.label_17.setText('Nuclides')
            self.label_18.setText('Volume (in cc)')
        elif self.Op_CB.currentText() == 'IndependentOperator':
            for Widget in Widgets:
                Widget.setEnabled(False)
            self.Keff_LE.show()
            self.From_Nuclide_CB.hide()
            self.label_19.show()
            self.label_17.setText('Fluxes')
            self.label_18.setText('MicroXS')
            self.label_19.setText('Keff')

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
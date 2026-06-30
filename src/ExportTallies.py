# -*- coding: utf-8 -*-
import sys
import string
import re
import numpy as np
from PyQt5.QtCore import *
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
from src.syntax_py import Highlighter
from src.PyEdit import TextEdit, NumberBar  
import math
from PyQt5.QtGui import QValidator

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

##########################################################################
#                   CLASSES DEFINING VALIDATORS                          #
##########################################################################

class IntListValidator(QValidator):
    def __init__(self, max_items=3, allow_zero=True, parent=None):
        super().__init__(parent)
        self.max_items = max_items
        self.pattern = re.compile(r'[,\s;:]+')  # space, comma, ; :

    def validate(self, input_str, pos):
        if not input_str.strip():
            return QValidator.Intermediate, input_str, pos

        parts = self.pattern.split(input_str.strip())

        # limit number of elements
        if len(parts) > self.max_items:
            return QValidator.Invalid, input_str, pos

        for part in parts:
            if not part:
                return QValidator.Intermediate, input_str, pos
            try:
                int(part)
            except ValueError:
                return QValidator.Invalid, input_str, pos

        return QValidator.Acceptable, input_str, pos

    def fixup(self, input_str):
        parts = self.pattern.split(input_str.strip())[:self.max_items]
        cleaned = []
        for part in parts:
            try:
                cleaned.append(str(int(part)))
            except:
                pass
        return ' '.join(cleaned)  # normalize to space-separated

class PositiveIntListValidator(QValidator):
    def __init__(self, max_items=None, allow_zero=True, parent=None):
        super().__init__(parent)
        self.max_items = max_items
        self.allow_zero = allow_zero
        self.pattern = re.compile(r'[,\s;:]+')  # separators

    def validate(self, input_str, pos):
        if not input_str.strip():
            return QValidator.Intermediate, input_str, pos

        parts = self.pattern.split(input_str.strip())

        if len(parts) > self.max_items:
            return QValidator.Invalid, input_str, pos

        for part in parts:
            if not part:
                return QValidator.Intermediate, input_str, pos

            # ❌ reject negative sign explicitly
            if part.startswith('-'):
                return QValidator.Invalid, input_str, pos

            # allow intermediate typing like "1 " or "2,"
            if not part.isdigit():
                return QValidator.Invalid, input_str, pos

            value = int(part)

            if not self.allow_zero and value == 0:
                return QValidator.Invalid, input_str, pos

        return QValidator.Acceptable, input_str, pos

    def fixup(self, input_str):
        parts = self.pattern.split(input_str.strip())[:self.max_items]
        cleaned = []
        for part in parts:
            if part.isdigit():
                value = int(part)
                if self.allow_zero or value > 0:
                    cleaned.append(str(value))
        return ' '.join(cleaned)

class FloatListValidator(QValidator):
    def __init__(self, max_items=None, parent=None):
        super().__init__(parent)
        self.max_items = max_items
        self.pattern = re.compile(r'[,\s;:]+')

        # float + scientific notation + partial typing support
        self.float_re = re.compile(
            r'^[+-]?('
            r'(\d+(\.\d*)?)|'      # 1, 1., 1.23
            r'(\.\d+)'             # .5
            r')([eE][+-]?\d*)?$'   # optional exponent (partial allowed)
        )

    def validate(self, input_str, pos):
        if not input_str.strip():
            return QValidator.Intermediate, input_str, pos

        parts = self.pattern.split(input_str.strip())

        # max length check
        if self.max_items is not None and len(parts) > self.max_items:
            return QValidator.Invalid, input_str, pos

        for part in parts:
            if not part:
                return QValidator.Intermediate, input_str, pos

            # allow typing "-" or "+"
            if part in ('-', '+'):
                return QValidator.Intermediate, input_str, pos

            # must match float pattern
            if not self.float_re.match(part):
                return QValidator.Invalid, input_str, pos

            # allow incomplete exponent while typing
            if part.lower().endswith('e') or part.lower().endswith(('e+', 'e-')):
                return QValidator.Intermediate, input_str, pos

            # final numeric check
            try:
                float(part)
            except ValueError:
                return QValidator.Invalid, input_str, pos

        return QValidator.Acceptable, input_str, pos

    def fixup(self, input_str):
        parts = self.pattern.split(input_str.strip())

        if self.max_items is not None:
            parts = parts[:self.max_items]

        cleaned = []
        for part in parts:
            try:
                cleaned.append(str(float(part)))
            except:
                pass

        return ' '.join(cleaned)

class PositiveFloatListValidator(QValidator):
    def __init__(self, max_items=None, allow_zero=True, parent=None):
        super().__init__(parent)
        self.max_items = max_items
        self.allow_zero = allow_zero
        self.pattern = re.compile(r'[,\s;:]+')

        # float with optional scientific notation (allows partial typing)
        self.float_re = re.compile(
            r'^[+]?('
            r'(\d+(\.\d*)?)|'      # 1 or 1. or 1.23
            r'(\.\d+)'             # .5
            r')([eE][+-]?\d*)?$'   # optional exponent
        )

    def validate(self, input_str, pos):
        if not input_str.strip():
            return QValidator.Intermediate, input_str, pos

        parts = self.pattern.split(input_str.strip())

        # max length constraint
        if self.max_items is not None and len(parts) > self.max_items:
            return QValidator.Invalid, input_str, pos

        for part in parts:
            if not part:
                return QValidator.Intermediate, input_str, pos

            # ❌ reject negative values
            if part.startswith('-'):
                return QValidator.Invalid, input_str, pos

            # must match float pattern
            if not self.float_re.match(part):
                return QValidator.Invalid, input_str, pos

            # incomplete exponent → still typing
            if part.lower().endswith('e') or part.lower().endswith(('e+', 'e-')):
                return QValidator.Intermediate, input_str, pos

            # final numeric check
            try:
                value = float(part)
            except ValueError:
                return QValidator.Invalid, input_str, pos

            if not self.allow_zero and value == 0.0:
                return QValidator.Invalid, input_str, pos

        return QValidator.Acceptable, input_str, pos

    def fixup(self, input_str):
        parts = self.pattern.split(input_str.strip())

        if self.max_items is not None:
            parts = parts[:self.max_items]

        cleaned = []
        for part in parts:
            try:
                value = float(part)
                if value >= 0 and (self.allow_zero or value > 0):
                    cleaned.append(str(value))
            except:
                pass

        return ' '.join(cleaned)

class FloatFloatIntValidator(QValidator):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pattern = re.compile(r'[,\s;:]+')

        # regex for partial/complete scientific float
        self.float_re = re.compile(
            r'^[+-]?('
            r'(\d+(\.\d*)?)|'      # 1 or 1. or 1.23
            r'(\.\d+)'             # .5
            r')([eE][+-]?\d*)?$'   # optional exponent (partial allowed)
        )

    def validate(self, input_str, pos):
        if not input_str.strip():
            return QValidator.Intermediate, input_str, pos

        parts = self.pattern.split(input_str.strip())

        if len(parts) > 3:
            return QValidator.Invalid, input_str, pos

        for i, part in enumerate(parts):
            if not part:
                return QValidator.Intermediate, input_str, pos

            # --- First two: floats (with scientific notation) ---
            if i < 2:
                if not self.float_re.match(part):
                    return QValidator.Invalid, input_str, pos

                # if it ends in incomplete exponent → intermediate
                if part.lower().endswith('e') or part.lower().endswith(('e+', 'e-')):
                    return QValidator.Intermediate, input_str, pos

            # --- Third: positive integer ---
            elif i == 2:
                if part.startswith('-'):
                    return QValidator.Invalid, input_str, pos

                if not part.isdigit():
                    return QValidator.Invalid, input_str, pos

                if int(part) <= 0:
                    return QValidator.Invalid, input_str, pos

        if len(parts) < 3:
            return QValidator.Intermediate, input_str, pos

        return QValidator.Acceptable, input_str, pos

    def fixup(self, input_str):
        parts = self.pattern.split(input_str.strip())[:3]
        cleaned = []

        for i in range(min(2, len(parts))):
            try:
                cleaned.append(str(float(parts[i])))
            except:
                pass

        if len(parts) >= 3 and parts[2].isdigit():
            val = int(parts[2])
            if val > 0:
                cleaned.append(str(val))

        return ' '.join(cleaned)

class FloatPiListValidator(QValidator):
    def __init__(self, max_items=None, parent=None):
        super().__init__(parent)
        self.max_items = max_items
        self.pattern = re.compile(r'[,\s;:]+')

        # float OR pi expressions
        self.float_re = re.compile(
            r'^[+-]?('
            r'(\d+(\.\d*)?)|'      # 1, 1.2, 1.
            r'(\.\d+)'             # .5
            r')([eE][+-]?\d*)?$'   # optional scientific
        )

        # pi expressions like: pi, 2pi, pi2, pi/2, 2*pi
        self.pi_re = re.compile(r'^[+-]?(\d*\*?pi|pi\d*|pi(/(\d+(\.\d+)?))?)$')

    def _is_valid_token(self, part):
        part = part.replace(' ', '')

        # allow partial typing of pi expressions
        if part in ('-', '+', 'pi', 'pi/', '2*', '*pi', 'pi2', '2pi'):
            return True

        # float
        if self.float_re.match(part):
            return True

        # pi-based expressions
        if self.pi_re.match(part.lower()):
            return True

        return False

    def _eval_token(self, part):
        part = part.replace(' ', '').lower()

        # pure pi
        if part == 'pi':
            return math.pi

        # 2pi or pi2
        if part == '2pi':
            return 2 * math.pi
        if part == 'pi2':
            return math.pi * 2

        # multiplication forms
        if '*pi' in part:
            return float(part.replace('*pi', '')) * math.pi
        if 'pi*' in part:
            return math.pi * float(part.replace('pi*', ''))

        # division form pi/2
        if 'pi/' in part:
            return math.pi / float(part.split('/')[1])

        # fallback float
        return float(part)

    def validate(self, input_str, pos):
        if not input_str.strip():
            return QValidator.Intermediate, input_str, pos

        parts = self.pattern.split(input_str.strip())

        if self.max_items is not None and len(parts) > self.max_items:
            return QValidator.Invalid, input_str, pos

        for part in parts:
            if not part:
                return QValidator.Intermediate, input_str, pos

            p = part.replace(' ', '').lower()

            # allow typing states
            if p in ('-', '+', '*', '/', 'pi/', 'pi*'):
                return QValidator.Intermediate, input_str, pos

            if not self._is_valid_token(p):
                return QValidator.Invalid, input_str, pos

        return QValidator.Acceptable, input_str, pos

    def fixup(self, input_str):
        parts = self.pattern.split(input_str.strip())

        if self.max_items is not None:
            parts = parts[:self.max_items]

        cleaned = []
        for part in parts:
            try:
                cleaned.append(str(self._eval_token(part)))
            except:
                pass

        return ' '.join(cleaned)
    

################################################################################
#//////////////////////////////////////////////////////////////////////////////#
#            M A I N    C L A S S    E X P O R T T A L L I E S                 #
#\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\#
################################################################################
class ExportTallies(QWidget):
    from .func import resize_ui, showDialog, Exit, Move_Commands_to_End 
    from .class_CheckableComboBox import CheckableComboBox
    from .Validators import UniversalNumericListValidator

    def __init__(self,v_1, Geom, Tallies, available_xs, Tally, Tally_ID, Filter, Filter_ID, Scores, 
                 Scores_ID, Surf_list, Surf_Id_list, Cells_list, Cell_Id_list, 
                 univ, mat, elements, nuclides, mesh, mesh_ID, parent=None):
        super(ExportTallies, self).__init__(parent)
        #sys.stdout = EmittingStream(textWritten=self.normalOutputWritten)
        #sys.stderr = EmittingStream(textWritten=self.normalOutputWritten)
        global UniversalNumericListValidator
        UniversalNumericListValidator = self.UniversalNumericListValidator

        v_1.moveCursor(QtGui.QTextCursor.End)
        uic.loadUi("src/ui/ExportTally.ui", self)
        self.v_1 = v_1
        self._initButtons()

        # validators
        self.Set_Validators()
        
        self.Mesh_LE_1.setToolTip("Only integers separated by ,;: are accepted")
        for item in [self.TallyId_LE, self.FilterId_LE, self.MeshId_LE, self.GrpNumber_LE]:
            item.setValidator(UniversalNumericListValidator(
                schema=("pos_int",), max_items=1, allow_negative=False, allow_pi=False))
            item.setToolTip("Only positive integer is accepted")

        for LineEd in [self.Mesh_LE_2, self.Mesh_LE_3]:
            LineEd.setValidator(UniversalNumericListValidator(
                schema=("float",), max_items=None, allow_negative=False, allow_pi=True))

            LineEd.setToolTip("Only float numbers separated by ,;: are accepted")
            LineEd.setEnabled(True)

        for LineEd in [self.Start_LE, self.End_LE, self.Tally_Trigger_Threshold_LE]:
            LineEd.setValidator(UniversalNumericListValidator(
                schema=("float",), max_items=1, allow_negative=False, allow_pi=False))
            LineEd.setToolTip("Only one float number is accepted")

        self.tally = ''
        self.available_xs = available_xs
        self.Neutron_XS_List = self.available_xs[0]
        self.TSL_XS_List = self.available_xs[1]
        self.Photon_XS_List = self.available_xs[2]

        self.tally_name_list = Tally
        self.tally_id_list = Tally_ID
        self.filter_name_list = Filter
        self.filter_id_list = Filter_ID
        self.score_name_list = Scores
        self.score_id_list = Scores_ID
        self.surface_name_list = Surf_list
        self.surface_id_list = Surf_Id_list
        self.cell_name_list = Cells_list
        self.cell_id_list = Cell_Id_list
        self.mesh_name_list = mesh
        self.mesh_id_list = mesh_ID
        self.Tallies = Tallies
        self.Geom = Geom
        self.Filter_Bins_CB.setEnabled(False)
        self.text_inserted = False

        self.universe_name_list = univ
        self.materials_name_list = mat
        self.Model_Elements_List = [elm for elm in elements]
        self.Model_Nuclides_List = [nucl for nucl in nuclides]
        self.Filter_Bins_List = []
        self.Filter_Bins_List_2 = []
        self.Filters_List = []
        self.Nuclides_Bins_List = []
        self.Scores_List = []
        self.tally_suffix = '_tally'
        self.old_suffix = self.Tally_LE.text().rstrip(string.digits)
        self.title = ''
        self.filter_suffix = '_filter'
        self.mesh_suffix = 'mesh'

        if len(Tally) > 0:
            self.Tally_ID = self.tally_id_list[-1] + 1
        else:
            self.Tally_ID = 1
        self.TallyId_LE.setText(str(self.Tally_ID))
        self.TallyName_LE.clear()        

        if len(mesh) > 0:
            self.Mesh_ID = self.mesh_id_list[-1] + 1
        else:
            self.Mesh_ID = 1
        self.MeshId_LE.setText(str(self.Mesh_ID))   

        if len(Filter) > 0:
            self.Filter_ID = self.filter_id_list[-1] + 1
        else:
            self.Filter_ID = 1
        self.FilterId_LE.setText(str(self.Filter_ID))
        self.Use_AllItems = False

        self.Nuclides_CB.clear()
        self.Create_New_Tally = False

        # define diffrent estimators, filters, meshes, scores, ..
        self.Initialize_Tallies()
        self.update_mesh_dim()
        self.activate_MGXS_Scores_CB()

        for item in [self.Grid_RB, self.MinMax_RB, self.Grid_RB_2, self.MinMax_RB_2, self.Grid_RB_3, self.MinMax_RB_3, 
                     self.MGX_CB, self.label, self.label_8, self.label_10, self.Start_LE, self.End_LE, 
                      self.GrpNumber_LE, self.End_Point_CB]: 
            item.hide()
        W = [self.label_2, self.label_3, self.label_4, self.Origin_LE, self.label_25, 
             self.Mesh_LE_1, self.Mesh_LE_2, self.Mesh_LE_3, self.Origin_LE]
        Ws = [self.From_Domain_CB, self.From_Domain_ComboBox, self.Domain_ComboBox, self.From_Domain_LE]

        for w in W:
            w.setEnabled(False)

        self.Filter_Bins_List_LE.setEnabled(False)

        # from_domain widgets
        for W in Ws:
            W.hide()

        self.From_Domain_CB.setChecked(False)
        self.From_Domain_CB.setEnabled(False)
        # add new editor
        self.plainTextEdit = TextEdit()
        self.plainTextEdit.setWordWrapMode(QTextOption.NoWrap)
        self.numbers = NumberBar(self.plainTextEdit)
        layoutH = QHBoxLayout()
        #layoutH.setSpacing(1.5)
        layoutH.addWidget(self.numbers)
        layoutH.addWidget(self.plainTextEdit)
        self.EditorLayout.addLayout(layoutH, 0, 0)
        # add scores ComboBox for Tally trigger
        self.Trigger_Scores_comboBox = self.CheckableComboBox()
        self.Trig_Scores_GL.addWidget(self.Trigger_Scores_comboBox)
        self.Def_Tallies()
        # Buttons state to be changed each time new tally is created
        self.AddScore_PB.setEnabled(False)
        self.AddFilters_PB.setEnabled(False)
        self.AddNuclides_PB.setEnabled(False)
        self.Add_Trigger_PB.setEnabled(False)
        self.Mesh_1D.setEnabled(False)
        self.Mesh_2D.setEnabled(False)
        self.Mesh_3D.setEnabled(False)
        
        sys.stdout = EmittingStream(textWritten=self.normalOutputWritten)
        # sys.stderr = EmittingStream(textWritten=self.normalOutputWritten)
        # to show window at the middle of the screen and resize it to the screen size
        self.resize_ui()

    def _initButtons(self):
        self.AddTally_PB.clicked.connect(self.Add_Tallies)
        self.CreateMesh_PB.clicked.connect(self.Create_Mesh)
        self.From_Domain_CB.stateChanged.connect(self.From_Domain)
        self.From_Domain_ComboBox.currentIndexChanged.connect(self.Set_From_Domain)
        self.Domain_ComboBox.currentIndexChanged.connect(self.Set_Domain_LE)
        self.MeshType_CB.currentIndexChanged.connect(self.Def_Mesh)
        self.CreateFilter_PB.clicked.connect(self.Create_Filters)
        self.Filter_Bins_CB.currentIndexChanged.connect(self.Show_Hide_Widgets)
        self.Filter_Bins_CB_2.currentIndexChanged.connect(self.Show_Hide_Widgets_MGXS)
        self.MGX_CB.currentIndexChanged.connect(self.Show_Hide_Widgets_1)
        self.MGX_CB.currentIndexChanged.connect(self.Choose_MGX_STR)
        self.MGX_CB_2.currentIndexChanged.connect(self.Choose_MGX_STR_2)
        self.TallyId_LE.textChanged.connect(self.sync_id)
        self.AddTallyId_CB.stateChanged.connect(self.sync_id)
        self.Tally_LE.textChanged.connect(self.sync_name)
        self.FilterId_LE.textChanged.connect(self.sync_filter_id)
        self.AddFilterId_CB.stateChanged.connect(self.sync_filter_id)
        self.FilterName_LE.textChanged.connect(self.sync_filter_name)
        self.MeshId_LE.textChanged.connect(self.sync_mesh_id)
        self.AddMeshId_CB.stateChanged.connect(self.sync_mesh_id)
        self.MeshName_LE.textChanged.connect(self.sync_mesh_name)
        self.Mesh_2D.toggled.connect(self.update_mesh_dim)
        self.Mesh_1D.toggled.connect(self.update_mesh_dim)
        self.MinMax_RB.toggled.connect(self.update_mesh_validator)
        self.MinMax_RB_2.toggled.connect(self.update_mesh_validator)
        self.MinMax_RB_3.toggled.connect(self.update_mesh_validator)
        self.FilterType_CB.currentIndexChanged.connect(self.Update_Filters)
        self.Filter_Bins_CB.currentIndexChanged.connect(self.Update_Filter_Bins)
        self.Filters_List_CB.currentIndexChanged.connect(self.Def_Filters_Bins_To_Tally)
        self.Nuclides_CB.currentIndexChanged.connect(self.Add_Nuclides_Bins_To_Tally)
        self.FluxScores_CB.currentIndexChanged.connect(self.DEF_FluxScores)
        self.RxnRates_CB.currentIndexChanged.connect(self.DEF_RxnRates)
        self.PartProduction_CB.currentIndexChanged.connect(self.DEF_PartProduction)
        self.MiscScores_CB.currentIndexChanged.connect(self.DEF_MiscScores)
        self.MGXS_Lib_CB.stateChanged.connect(self.activate_MGXS_Scores_CB)
        self.MGXS_Scores_CB.currentIndexChanged.connect(self.DEF_MGXS_Scores)
        self.MG_Matrix_XS_CB.currentIndexChanged.connect(self.DEF_MGXS_XS_Matrix)
        self.MG_Levels_XS_CB.currentIndexChanged.connect(self.DEF_MGXS_XS_Levels)
        self.Undo_PB.clicked.connect(lambda: self.Undo(self.Filter_Bins_List, self.Filter_Bins_List_LE))
        self.Undo_PB_2.clicked.connect(lambda: self.Undo(self.Filter_Bins_List_2, self.Filter_Bins_List_LE_2))
        self.Reset_PB.clicked.connect(lambda: self.Reset(self.Filter_Bins_List, self.Filter_Bins_List_LE))
        self.Reset_PB_2.clicked.connect(lambda: self.Reset(self.Filter_Bins_List_2, self.Filter_Bins_List_LE_2))
        self.UndoFilter_PB.clicked.connect(lambda: self.Undo(self.Filters_List, self.Filters_List_LE))
        self.ResetFilter_PB.clicked.connect(lambda: self.Reset(self.Filters_List, self.Filters_List_LE))
        self.UndoNucl_PB.clicked.connect(lambda: self.Undo(self.Nuclides_Bins_List, self.Nuclides_Bins_List_LE))
        self.ResetNucl_PB.clicked.connect(lambda: self.Reset(self.Nuclides_Bins_List, self.Nuclides_Bins_List_LE))
        self.UndoScores_PB.clicked.connect(lambda: self.Undo(self.Scores_List, self.ScoresList_LE))
        self.ResetScores_PB.clicked.connect(lambda: self.Reset(self.Scores_List, self.ScoresList_LE))
        self.AddFilters_PB.clicked.connect(self.Add_Filters_Bins_To_Tally)
        self.AddNuclides_PB.clicked.connect(self.Add_Nuclides)
        self.AddScore_PB.clicked.connect(self.Add_Scores)
        self.ExportData_PB.clicked.connect(self.Export_to_Main_Window)
        self.ClearData_PB.clicked.connect(self.clear_text)
        self.Exit_PB.clicked.connect(self.Exit)
        self.Add_Trigger_PB.clicked.connect(self.Add_Trigger)
        
    def Set_Validators(self):
        self.int_validator = QRegExpValidator(QRegExp(r'[0-9]+'))
        self.dim_validator = QRegExpValidator(QRegExp(r'[0-9 ,;:]+'))
        self.validator = QRegExpValidator(QRegExp("(([+-]?\\d+(\\.\\d*)?|\\.\\d+)([eE][+-]?\\d+)?)"))   
        self.validator_positif = QRegExpValidator(QRegExp("((\\d+(\\.\\d*)?|\\.\\d+)([eE][+-]?\\d+)?)"))   
        float_regexp_list = r"(([+-]?\d+(\.\d*)?|\.\d+)(([ ,;:])|[eE][+-]?\d+)([ ,;:])?)"
        regexp_list = "(float)?( +float)* *".replace("float", float_regexp_list)     
        self.float_validator_list = QRegExpValidator(QRegExp(regexp_list))
        float_regexp_list_positif = r"((\d+(\.\d*)?|\.\d+)(([ ,;:])|[eE][+-]?\d+)([ ,;:])?)"
        regexp_list_positif = "(float)?( +float)* *".replace("float", float_regexp_list_positif)
        self.float_validator_list_positif = QRegExpValidator(QRegExp(regexp_list_positif))    
        float_regexp_list_pi = r"(([+-]?\d+(\.\d*)?|[-][p][i]?|[p][i]?|\.\d+)(([ ,;:])|[eE][+-]?\d+|[*][p][i]?)(([*][p][i]?)|[ ,;:])?)"
        regexp_list_pi = "(float)?( +float)* *".replace("float", float_regexp_list_pi)     
        self.float_validator_list_pi = QRegExpValidator(QRegExp(regexp_list_pi))
        float_regexp_list_pi_positif = r"((\d+(\.\d*)?|[p][i]?|\.\d+)(([ ,;:])|[eE][+-]?\d+|[*][p][i]?)(([*][p][i]?)|[ ,;:])?)"
        regexp_list_pi_positif = "(float)?( +float)* *".replace("float", float_regexp_list_pi_positif)     
        self.float_validator_list_pi_positif = QRegExpValidator(QRegExp(regexp_list_pi_positif))
        #float_regexp_pi_positif = r"((\d+(\.\d*)?|[p][i]?|\.\d+)([eE][+-]?\d+|[*][p][i]?)(([*][p][i]?))?)"
        #regexp__pi_positif = "(float)?( +float)* *".replace("float", float_regexp_pi_positif)     
        self.float_validator_pi = QRegExpValidator(QRegExp("(([+-]?\\d+(\\.\\d*)?|[-][p][i]?|[p][i]?|\\.\\d+)([eE][+-]?\\d+|[*][p][i]?)(([*][p][i]?))?)"))
        self.float_validator_pi_positif = QRegExpValidator(QRegExp("((\\d+(\\.\\d*)?|[p][i]?|\\.\\d+)([eE][+-]?\\d+|[*][p][i]?)(([*][p][i]?))?)"))

        # list of positive floats
        float_pattern = r"((\d+(\.\d*)?|\.\d+)(([ ,;:])|[eE][+-]?\d+)([ ,;:])?)"
        regexp_list = f"^{float_pattern}({float_pattern})*$"
        self.float_validator_list_positif = QRegExpValidator(QRegExp(regexp_list)) 
        # list of floats
        float_pattern = r"(([+-]?\d+(\.\d*)?|\.\d+)(([ ,;:])|[eE][+-]?\d+)([ ,;:])?)"
        regexp_list = f"^{float_pattern}({float_pattern})*$"
        self.float_validator_list = QRegExpValidator(QRegExp(regexp_list))
        # list of floats and pi
        # Number pattern (requires at least one digit)
        number = r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?"

        # Pi with optional number after (for pi*3.2, pi/2, etc.)
        pi_with_number = r"[+-]?pi(?:\*?\d*\.?\d*)?(?:/\d*\.?\d*)?"
        # This matches: pi, -pi, +pi, pi*3.2, pi/2, pi*.5, etc.

        # Number with optional pi after (for 2*pi, pi*2, etc.)
        number_with_pi = rf"{number}(?:[*]?[+-]?pi)?"

        # Combined expression (either number_with_pi OR pi_with_number)
        expression = rf"(?:{number_with_pi}|{pi_with_number})"

        # Full pattern with separators
        full_pattern = rf"^{expression}(?:[\s,;:]+{expression})*$"
        self.float_validator_list_pi = QRegExpValidator(QRegExp(full_pattern))
        
        # floats or pi, one value
        float_pi_pattern = r"^(?:(?:[+-]?\d*\.?\d*(?:[eE][+-]?\d+)?(?:[*]?[+-]?pi(?:/?\d*\.?\d*)?))|(?:[+-]?pi(?:\*?\d*\.?\d*)?))$"
        self.float_validator_pi = QRegExpValidator(QRegExp(float_pi_pattern))

        #
        number = r"(\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?"  
        pi_with_number = r"pi(?:\*?\d*\.?\d*)?(?:/\d*\.?\d*)?"
        number_with_pi = rf"{number}(?:[*]?pi)?"
        expression = rf"(?:{number_with_pi}|{pi_with_number})"
        full_pattern = rf"^{expression}(?:[\s,;:]+{expression})*$"
        self.float_validator_list_pi_positif = QRegExpValidator(QRegExp(full_pattern))
        

    def Define_Tips(self):
        # define Tips of each button  
        self.From_Domain_CB.setToolTip('Create mesh where the corners of the mesh are being set automatically to surround the geometry.')
        self.FluxScores_CB.setToolTip('Flux scores: Total flux, units are particle-cm per source particle.')
        self.FluxScores_CB.setItemData(1,'Total Flux.', QtCore.Qt.ToolTipRole)
        self.MiscScores_CB.setToolTip('Miscellaneous scores: units are indicated for each.')
        self.MiscScores_CB.setItemData(1,'Used in combination with a meshsurface filter: Partial currents ' +
                                         'on the boundaries of each cell in a mesh. It may not be used in ' +
                                         'conjunction with any other score. Only energy and mesh filters may ' +
                                         'be used. Used in combination with a surface filter: Net currents on ' +
                                         'any surface previously defined in the geometry. It may be used along ' +
                                         'with any other filter, except meshsurface filters. Surfaces can ' +
                                         'alternatively be defined with cell from and cell filters thereby ' +
                                         'resulting in tallying partial currents. Units are particles per source particle.', QtCore.Qt.ToolTipRole)
        self.MiscScores_CB.setItemData(2,'Number of scoring events. Units are events per source particle.', QtCore.Qt.ToolTipRole)
        self.MiscScores_CB.setItemData(3,'The flux-weighted inverse velocity where the velocity is in units of centimeters per second.', QtCore.Qt.ToolTipRole)
        self.MiscScores_CB.setItemData(4,'Total nuclear heating in units of eV per source particle. For neutrons, ' +
                                         'this corresponds to MT=301 produced by NJOY’s HEATR module while for photons, ' +
                                         'this is tallied from direct photon energy deposition. See Heating and Energy Deposition.', QtCore.Qt.ToolTipRole)
        self.MiscScores_CB.setItemData(5,'Total nuclear heating in units of eV per source particle assuming energy from secondary ' +
                                         'photons is deposited locally. Note that this score should only be used for incident neutrons.'+
                                         'See Heating and Energy Deposition.', QtCore.Qt.ToolTipRole)
        self.MiscScores_CB.setItemData(6,'The recoverable energy production rate due to fission. The recoverable energy is defined as ' +
                                         'the fission product kinetic energy, prompt and delayed neutron kinetic energies, prompt and delayed '+
                                         'gamma-ray total energies, and the total energy released by the delayed beta particles. The neutrino '+
                                         'energy does not contribute to this response. The prompt and delayed gamma-rays are assumed to deposit '+
                                         'their energy locally. Units are eV per source particle.', QtCore.Qt.ToolTipRole)
        self.MiscScores_CB.setItemData(7,'The prompt fission energy production rate. This energy comes in the form of fission fragment nuclei,'+
                                         'prompt neutrons, and prompt gamma-rays. This value depends on the incident energy and it requires that'+
                                         'the nuclear data library contains the optional fission energy release data. Energy is assumed to be '+
                                         'deposited locally. Units are eV per source particle.', QtCore.Qt.ToolTipRole)
        self.MiscScores_CB.setItemData(8,'The recoverable fission energy production rate. This energy comes in the form of fission fragment nuclei, '+
                                         'prompt and delayed neutrons, prompt and delayed gamma-rays, and delayed beta-rays. This tally differs from '+
                                         'the kappa-fission tally in that it is dependent on incident neutron energy and it requires that the nuclear '+
                                         'data library contains the optional fission energy release data. Energy is assumed to be deposited locally. '+
                                         'Units are eV per source paticle.', QtCore.Qt.ToolTipRole)
        self.MiscScores_CB.setItemData(9,'The delayed-nu-fission-weighted decay rate where the decay rate is in units of inverse seconds.', QtCore.Qt.ToolTipRole)
        self.MiscScores_CB.setItemData(10,'Damage energy production in units of eV per source particle. This corresponds to MT=444 produced by NJOY’s HEATR module.', QtCore.Qt.ToolTipRole)

    def Initialize_Tallies(self):       
        # define diffrent estimators, filters, meshes, scores, ...
        ESTIMATOR_TYPES = ['tracklength', 'collision', 'analog']
        self.Estimator_CB.addItems(ESTIMATOR_TYPES)
        self.PARTICLE_TYPE = ['neutron', 'photon', 'electron', 'positron']
        self.DELAYED_GROUPS = ['1', '2', '3', '4', '5', '6']
        # Possible filters
        FILTER_TYPES = ['UniverseFilter', 'MaterialFilter', 'CellFilter', 'CellFromFilter', 'CellBornFilter',
                        'CellInstanceFilter', 'CollisionFilter', 'SurfaceFilter', 'MeshFilter', 'MeshSurfaceFilter',
                        'EnergyFilter', 'EnergyoutFilter', 'MuFilter', 'PolarFilter', 'AzimuthalFilter',
                        'DistribcellFilter', 'DelayedGroupFilter', 'EnergyFunctionFilter', 'LegendreFilter',
                        'SpatialLegendreFilter', 'SphericalHarmonicsFilter', 'ZernikeFilter', 'ZernikeRadialFilter',
                        'ParticleFilter', 'TimeFilter']
        self.FILTER_SUFFIX = ['Universe_filter', 'Material_filter', 'Cell_filter', 'CellFrom_filter', 'CellBorn_filter',
                        'CellInstance_filter', 'Collision_filter', 'Surface_filter', 'Mesh_filter', 'MeshSurface_filter',
                        'Energy_filter', 'Energyout_filter', 'Mu_filter', 'Polar_filter', 'Azimuthal_filter',
                        'Distribcell_filter', 'DelayedGroup_filter', 'EnergyFunction_filter', 'Legendre_filter',
                        'SpatialLegendre_filter', 'SphericalHarmonics_filter', 'Zernike_filter', 'ZernikeRadial_filter',
                        'Particle_filter', 'Time_filter']
        # Possible meshes
        MESH_TYPES = ['RegularMesh', 'RectilinearMesh', 'CylindricalMesh', 'SphericalMesh', 'UnstructuredMesh']
        # Possible scores
        self.FlUX_SCORES = ['flux']
        self.REACTION_SCORES = ['absorption', 'elastic', 'fission', 'scatter', 'total', '(n,2nd)', '(n,2n)', '(n,3n)',
                                '(n,na)', '(n,n3a)', '(n,2na)', '(n,3na)', '(n,np)', '(n,n2a)', '(n,2n2a)', '(n,nd)',
                                '(n,nt)', '(n,n3He)', '(n,nd2a)', '(n,nt2a)', '(n,4n)', '(n,2np)', '(n,3np)', '(n,n2p)',
                                '(n,n*X*)', '(n,nc)', '(n,gamma)', '(n,p)', '(n,d)', '(n,t)', '(n,3He)', '(n,a)',
                                '(n,2a)', '(n,3a)', '(n,2p)', '(n,pa)', '(n,t2a)', '(n,d2a)', '(n,pd)', '(n,pt)', '(n,da)',
                                'coherent-scatter', 'incoherent-scatter', 'photoelectric', 'pair-production', 'Arbitrary integer']
        self.PARTICLE_PRODUCTION_SCORES = ['delayed-nu-fission', 'prompt-nu-fission', 'nu-fission', 'nu-scatter',
                                           'H1-production', 'H2-production', 'H3-production', 'He3-production', 'He4-production']
        self.MISCELLANEOUS_SCORES = ['current', 'events', 'inverse-velocity', 'heating', 'heating-local', 'kappa-fission',
                                     'fission-q-prompt', 'fission-q-recoverable', 'decay-rate', 'damage-energy', 'pulse-height']

        self.MGXS_LIB_SCORES = ['total', 'transport', 'nu-transport', 'absorption', 'reduced absorption', 'capture', 'fission', 
                        'nu-fission', 'kappa-fission', 'scatter', 'nu-scatter', 'current', 'diffusion-coefficient', 'nu-diffusion-coefficient', 
                        'chi', 'chi-prompt', 'inverse-velocity', 'prompt-nu-fission', 
                        'delayed-nu-fission', 'chi-delayed', 'beta', 'decay-rate', 'heating', 'heating-local','damage-energy',
                        '(n,elastic)', '(n,disappear)', '(n,gamma)','(n,nonelastic)'] 
                             
        self.MGXS_LEVEL_SCORES = ['(n,level)', '(n,2nd)', '(n,2n)', '(n,3n)', '(n,na)', '(n,n3a)', '(n,2na)', '(n,3na)', 
                        '(n,np)', '(n,n2a)', '(n,2n2a)', '(n,nd)', '(n,nt)', '(n,n3He)', '(n,nd2a)', '(n,nt2a)', '(n,4n)', 
                        '(n,2np)', '(n,3np)', '(n,n2p)', '(n,npa)', '(n,nc)', '(n,p)', '(n,d)', 
                        '(n,t)', '(n,3He)', '(n,a)', '(n,2a)', '(n,3a)', '(n,2p)', '(n,pa)', '(n,t2a)', '(n,d2a)', '(n,pd)', 
                        '(n,pt)', '(n,da)', '(n,5n)', '(n,6n)', '(n,2nt)', '(n,ta)', '(n,4np)', '(n,3nd)', '(n,nda)', 
                        '(n,2npa)', '(n,7n)', '(n,8n)', '(n,5np)', '(n,6np)', '(n,7np)', '(n,4na)', '(n,5na)', '(n,6na)', 
                        '(n,7na)', '(n,4nd)', '(n,5nd)', '(n,6nd)', '(n,3nt)', '(n,4nt)', '(n,5nt)', '(n,6nt)', '(n,2n3He)', 
                        '(n,3n3He)', '(n,4n3He)', '(n,3n2p)', '(n,3n2a)', '(n,3npa)', '(n,dt)', '(n,npd)', '(n,npt)', '(n,ndt)', 
                        '(n,np3He)', '(n,nd3He)', '(n,nt3He)', '(n,nta)', '(n,2n2p)', '(n,p3He)', '(n,d3He)', '(n,3Hea)', 
                        '(n,4n2p)', '(n,4n2a)', '(n,4npa)', '(n,3p)', '(n,n3p)', '(n,3n2pa)', '(n,5n2p)', '(n,Xp)', '(n,Xd)', 
                        '(n,Xt)', '(n,X3He)', '(n,Xa)',  '(n,pc)', '(n,dc)', '(n,tc)', '(n,3Hec)', 
                        '(n,ac)', '(n,2nc)',  '(n,n1)', '(n,n2)', '(n,n3)', '(n,n4)', '(n,n5)', '(n,n6)', '(n,n7)', 
                        '(n,n8)', '(n,n9)', '(n,n10)', '(n,n11)', '(n,n12)', '(n,n13)', '(n,n14)', '(n,n15)', '(n,n16)', '(n,n17)', 
                        '(n,n18)', '(n,n19)', '(n,n20)', '(n,n21)', '(n,n22)', '(n,n23)', '(n,n24)', '(n,n25)', '(n,n26)', 
                        '(n,n27)', '(n,n28)', '(n,n29)', '(n,n30)', '(n,n31)', '(n,n32)', '(n,n33)', '(n,n34)', '(n,n35)', '(n,n36)', 
                        '(n,n37)', '(n,n38)', '(n,n39)', '(n,n40)', '(n,p0)', '(n,p1)', '(n,p2)', '(n,p3)', '(n,p4)', '(n,p5)', 
                        '(n,p6)', '(n,p7)', '(n,p8)', '(n,p9)', '(n,p10)', '(n,p11)', '(n,p12)', '(n,p13)', '(n,p14)', '(n,p15)', 
                        '(n,p16)', '(n,p17)', '(n,p18)', '(n,p19)', '(n,p20)', '(n,p21)', '(n,p22)', '(n,p23)', '(n,p24)', '(n,p25)', 
                        '(n,p26)', '(n,p27)', '(n,p28)', '(n,p29)', '(n,p30)', '(n,p31)', '(n,p32)', '(n,p33)', '(n,p34)', '(n,p35)', 
                        '(n,p36)', '(n,p37)', '(n,p38)', '(n,p39)', '(n,p40)', '(n,p41)', '(n,p42)', '(n,p43)', '(n,p44)', '(n,p45)', 
                        '(n,p46)', '(n,p47)', '(n,p48)', '(n,d0)', '(n,d1)', '(n,d2)', '(n,d3)', '(n,d4)', '(n,d5)', '(n,d6)', 
                        '(n,d7)', '(n,d8)', '(n,d9)', '(n,d10)', '(n,d11)', '(n,d12)', '(n,d13)', '(n,d14)', '(n,d15)', '(n,d16)', 
                        '(n,d17)', '(n,d18)', '(n,d19)', '(n,d20)', '(n,d21)', '(n,d22)', '(n,d23)', '(n,d24)', '(n,d25)', '(n,d26)', 
                        '(n,d27)', '(n,d28)', '(n,d29)', '(n,d30)', '(n,d31)', '(n,d32)', '(n,d33)', '(n,d34)', '(n,d35)', '(n,d36)', 
                        '(n,d37)', '(n,d38)', '(n,d39)', '(n,d40)', '(n,d41)', '(n,d42)', '(n,d43)', '(n,d44)', '(n,d45)', '(n,d46)', 
                        '(n,d47)', '(n,d48)', '(n,t0)', '(n,t1)', '(n,t2)', '(n,t3)', '(n,t4)', '(n,t5)', '(n,t6)', '(n,t7)', '(n,t8)', 
                        '(n,t9)', '(n,t10)', '(n,t11)', '(n,t12)', '(n,t13)', '(n,t14)', '(n,t15)', '(n,t16)', '(n,t17)', '(n,t18)', 
                        '(n,t19)', '(n,t20)', '(n,t21)', '(n,t22)', '(n,t23)', '(n,t24)', '(n,t25)', '(n,t26)', '(n,t27)', '(n,t28)', 
                        '(n,t29)', '(n,t30)', '(n,t31)', '(n,t32)', '(n,t33)', '(n,t34)', '(n,t35)', '(n,t36)', '(n,t37)', '(n,t38)', 
                        '(n,t39)', '(n,t40)', '(n,t41)', '(n,t42)', '(n,t43)', '(n,t44)', '(n,t45)', '(n,t46)', '(n,t47)', '(n,t48)', 
                        '(n,3He0)', '(n,3He1)', '(n,3He2)', '(n,3He3)', '(n,3He4)', '(n,3He5)', '(n,3He6)', '(n,3He7)', '(n,3He8)', 
                        '(n,3He9)', '(n,3He10)', '(n,3He11)', '(n,3He12)', '(n,3He13)', '(n,3He14)', '(n,3He15)', '(n,3He16)', 
                        '(n,3He17)', '(n,3He18)', '(n,3He19)', '(n,3He20)', '(n,3He21)', '(n,3He22)', '(n,3He23)', '(n,3He24)', 
                        '(n,3He25)', '(n,3He26)', '(n,3He27)', '(n,3He28)', '(n,3He29)', '(n,3He30)', '(n,3He31)', '(n,3He32)', 
                        '(n,3He33)', '(n,3He34)', '(n,3He35)', '(n,3He36)', '(n,3He37)', '(n,3He38)', '(n,3He39)', '(n,3He40)', 
                        '(n,3He41)', '(n,3He42)', '(n,3He43)', '(n,3He44)', '(n,3He45)', '(n,3He46)', '(n,3He47)', '(n,3He48)', 
                        '(n,a0)', '(n,a1)', '(n,a2)', '(n,a3)', '(n,a4)', '(n,a5)', '(n,a6)', '(n,a7)', '(n,a8)', '(n,a9)', '(n,a10)', 
                        '(n,a11)', '(n,a12)', '(n,a13)', '(n,a14)', '(n,a15)', '(n,a16)', '(n,a17)', '(n,a18)', '(n,a19)', '(n,a20)', 
                        '(n,a21)', '(n,a22)', '(n,a23)', '(n,a24)', '(n,a25)', '(n,a26)', '(n,a27)', '(n,a28)', '(n,a29)', '(n,a30)', 
                        '(n,a31)', '(n,a32)', '(n,a33)', '(n,a34)', '(n,a35)', '(n,a36)', '(n,a37)', '(n,a38)', '(n,a39)', '(n,a40)', 
                        '(n,a41)', '(n,a42)', '(n,a43)', '(n,a44)', '(n,a45)', '(n,a46)', '(n,a47)', '(n,a48)', '(n,2n0)', '(n,2n1)', 
                        '(n,2n2)', '(n,2n3)', '(n,2n4)', '(n,2n5)', '(n,2n6)', '(n,2n7)', '(n,2n8)', '(n,2n9)', '(n,2n10)', '(n,2n11)', 
                        '(n,2n12)', '(n,2n13)', '(n,2n14)', '(n,2n15)']

        self.MGXS_MATRIX_XS = ['scatter matrix', 'nu-scatter matrix', 
                        'multiplicity matrix', 'nu-fission matrix', 'scatter probability matrix', 'consistent scatter matrix', 
                        'consistent nu-scatter matrix', 'prompt-nu-fission matrix', 'delayed-nu-fission matrix', 
                        '(n,nonelastic) matrix', '(n,2nd) matrix', '(n,2n) matrix', 
                        '(n,3n) matrix', '(n,na) matrix', '(n,n3a) matrix', '(n,2na) matrix', '(n,3na) matrix', '(n,np) matrix', 
                        '(n,n2a) matrix', '(n,2n2a) matrix', '(n,nd) matrix', '(n,nt) matrix', '(n,n3He) matrix', '(n,nd2a) matrix', 
                        '(n,nt2a) matrix', '(n,4n) matrix', '(n,2np) matrix', '(n,3np) matrix', '(n,n2p) matrix', '(n,npa) matrix', 
                        '(n,nc) matrix', '(n,5n) matrix', '(n,6n) matrix', '(n,2nt) matrix', '(n,4np) matrix', '(n,3nd) matrix', 
                        '(n,nda) matrix', '(n,2npa) matrix', '(n,7n) matrix', '(n,8n) matrix', '(n,5np) matrix', '(n,6np) matrix', 
                        '(n,7np) matrix', '(n,4na) matrix', '(n,5na) matrix', '(n,6na) matrix', '(n,7na) matrix', '(n,4nd) matrix', 
                        '(n,5nd) matrix', '(n,6nd) matrix', '(n,3nt) matrix', '(n,4nt) matrix', '(n,5nt) matrix', '(n,6nt) matrix', 
                        '(n,2n3He) matrix', '(n,3n3He) matrix', '(n,4n3He) matrix', '(n,3n2p) matrix', '(n,3n2a) matrix', 
                        '(n,3npa) matrix', '(n,npd) matrix', '(n,npt) matrix', '(n,ndt) matrix', '(n,np3He) matrix', 
                        '(n,nd3He) matrix', '(n,nt3He) matrix', '(n,nta) matrix', '(n,2n2p) matrix', '(n,4n2p) matrix', 
                        '(n,4n2a) matrix', '(n,4npa) matrix', '(n,n3p) matrix', '(n,3n2pa) matrix', '(n,5n2p) matrix', 
                        '(n,2nc) matrix', '(n,n1) matrix', '(n,n2) matrix', '(n,n3) matrix', '(n,n4) matrix', '(n,n5) matrix', 
                        '(n,n6) matrix', '(n,n7) matrix', '(n,n8) matrix', '(n,n9) matrix', '(n,n10) matrix', '(n,n11) matrix', 
                        '(n,n12) matrix', '(n,n13) matrix', '(n,n14) matrix', '(n,n15) matrix', '(n,n16) matrix', '(n,n17) matrix', 
                        '(n,n18) matrix', '(n,n19) matrix', '(n,n20) matrix', '(n,n21) matrix', '(n,n22) matrix', '(n,n23) matrix', 
                        '(n,n24) matrix', '(n,n25) matrix', '(n,n26) matrix', '(n,n27) matrix', '(n,n28) matrix', '(n,n29) matrix', 
                        '(n,n30) matrix', '(n,n31) matrix', '(n,n32) matrix', '(n,n33) matrix', '(n,n34) matrix', '(n,n35) matrix', 
                        '(n,n36) matrix', '(n,n37) matrix', '(n,n38) matrix', '(n,n39) matrix', '(n,n40) matrix', '(n,2n0) matrix', 
                        '(n,2n1) matrix', '(n,2n2) matrix', '(n,2n3) matrix', '(n,2n4) matrix', '(n,2n5) matrix', '(n,2n6) matrix', 
                        '(n,2n7) matrix', '(n,2n8) matrix', '(n,2n9) matrix', '(n,2n10) matrix', '(n,2n11) matrix', '(n,2n12) matrix', 
                        '(n,2n13) matrix', '(n,2n14) matrix', '(n,2n15) matrix']

        if self.AddTallyId_CB.isChecked():
            self.Tally_LE.setText(self.tally_suffix + str(self.TallyId_LE.text()))
        else:
            self.Tally_LE.setText(self.tally_suffix)
        if self.AddMeshId_CB.isChecked():
            self.MeshName_LE.setText(self.mesh_suffix + str(self.MeshId_LE.text()))
        else:
            self.MeshName_LE.setText(self.mesh_suffix)

        # instantiate bins lists of filters
        self.Availble_Filters = {'UniverseFilter': self.universe_name_list, 'MaterialFilter': self.materials_name_list,
                              'CellFilter': self.cell_name_list, 'CellFromFilter': self.cell_name_list,
                              'CellBornFilter': self.cell_name_list, 'CellInstanceFilter': self.cell_name_list,
                              'SurfaceFilter': self.surface_name_list, 'MeshFilter': self.mesh_name_list,
                              'MeshSurfaceFilter': self.mesh_name_list, 'DistribcellFilter': self.cell_name_list,
                              'CollisionFilter': [],'EnergyFilter': [], 'EnergyoutFilter': [], 'MuFilter': [],
                              'PolarFilter': [], 'AzimuthalFilter': [], 'DelayedGroupFilter': [],
                              'EnergyFunctionFilter': [], 'LegendreFilter': [], 'SpatialLegendreFilter': [],
                              'SphericalHarmonicsFilter': [], 'ZernikeFilter': [], 'ZernikeRadialFilter': [],
                              'ParticleFilter': [], 'TimeFilter': []}

        self.MGX_GROUP_STRUCTURES_LIST = ['Select Structure', 'CASMO-2', 'CASMO-4', 'CASMO-8', 'CASMO-16', 'CASMO-25', 'CASMO-40', 'CASMO-70', 
                                          'XMAS-172', 'SHEM-361', 'SCALE-44', 'SCALE-252', 'SCALE-999', 
                                          'MPACT-51', 'MPACT-60', 'MPACT-69', 
                                          'ECCO-33', 'ECCO-1968', 
                                          'VITAMIN-J-42', 'VITAMIN-J-175', 'TRIPOLI-315,', 'LLNL-616',
                                          'CCFE-709', 'UKAEA-1102']

        # Filling Available Filters combobox
        self.FilterType_CB.addItems(FILTER_TYPES)
        # Filling Meshes combobox
        self.MeshType_CB.addItems(MESH_TYPES)
        self.MeshType_CB.model().item(5).setEnabled(False)
        # Filling Nuclides combobox
        if self.Model_Nuclides_List:
            self.Nuclides_CB.addItems(['Select Nuclide', 'Add all nuclides'])
            self.Nuclides_CB.addItems(self.Model_Nuclides_List)
        #print(self.Model_Nuclides_List)
        # Filling SCORES combobox
        self.FluxScores_CB.addItems(self.FlUX_SCORES)
        self.RxnRates_CB.addItems(self.REACTION_SCORES)
        self.PartProduction_CB.addItems(self.PARTICLE_PRODUCTION_SCORES)
        self.MiscScores_CB.addItems(self.MISCELLANEOUS_SCORES)
        # filling MG parameters comboboxes 
        self.MGXS_Scores_CB.addItems(self.MGXS_LIB_SCORES)
        self.MG_Matrix_XS_CB.addItems(self.MGXS_MATRIX_XS)
        self.MG_Levels_XS_CB.addItems(self.MGXS_LEVEL_SCORES)
        self.Domain_type_CB.addItems(['material', 'cell', 'distribcell', 'universe', 'mesh'])
        self.Filter_Bins_CB_2.addItems(['Select option', 'Enter data', 'Equal-Step Energies', 'Equal-Lethargy Energies', 'MGX.GRP_STRUCTURES'])
        self.MGX_CB_2.addItems(self.MGX_GROUP_STRUCTURES_LIST)
        self.MGX_CB_2.hide()
         
        self.comboBox.addItems(['histogram', 'linear-linear', 'linear-log', 'log-linear', 'log-log', 'quadratic', 'cubic'])                     
        self.comboBox.hide()

        Widgets = [self.label_16, self.label_17, self.label_15, self.Start_LE_2, self.End_LE_2, self.GrpNumber_LE_2]
        for W in Widgets:
            W.hide()
        self.Start_LE_2.setValidator(UniversalNumericListValidator(
                schema=("float",), max_items=1, allow_negative=False, allow_pi=False))
        self.End_LE_2.setValidator(UniversalNumericListValidator(
                schema=("float",), max_items=1, allow_negative=False, allow_pi=False))
        self.GrpNumber_LE.setValidator(UniversalNumericListValidator(
                schema=("pos_int",), max_items=1, allow_negative=False, allow_pi=False))

        # add tips to scores
        self.Define_Tips()

        self.Filters_List_CB.clear()
        # Filling Filters ComboBox to add to tally
        if self.filter_name_list:
            self.Filters_List_CB.addItems(['Select Filter', 'All filters'])
            self.Filters_List_CB.addItems(self.filter_name_list)

    def sync_name(self):
        import string
        self.title = self.Tally_LE.text().rstrip(string.digits).replace(self.tally_suffix, '')

    def sync_id(self):
        import string
        if self.TallyId_LE.text():
            self.Tally_ID = int(self.TallyId_LE.text())
            if self.AddTallyId_CB.isChecked():
                self.Tally_LE.setText(self.Tally_LE.text().rstrip(string.digits) + str(self.Tally_ID))
            else:
                self.Tally_LE.setText(self.Tally_LE.text().rstrip(string.digits))

    def sync_filter_name(self):
        import string
        self.filter_suffix = self.FilterName_LE.text().rstrip(string.digits)

    def sync_filter_id(self):
        import string
        if self.FilterId_LE.text():
            self.Filter_ID = int(self.FilterId_LE.text())
            if self.AddFilterId_CB.isChecked():
                self.FilterName_LE.setText(self.filter_suffix + str(self.Filter_ID))
                self.filter_suffix = self.FilterName_LE.text().rstrip(string.digits)
            else:
                self.filter_suffix = self.FilterName_LE.text().rstrip(string.digits)
                self.FilterName_LE.setText(self.filter_suffix)

    def sync_mesh_name(self):
        import string
        self.mesh_suffix = self.MeshName_LE.text().rstrip(string.digits)
    
    def update_mesh_dim(self):
        if self.Mesh_1D.isChecked():
            self.label_2.setText('1 Dimension (Nx)')
            self.label_3.setText('Lower Left (x)')
            self.label_4.setText('Upper Right (x)')
            self.Mesh_LE_1.setValidator(UniversalNumericListValidator(
                schema=("pos_int",), max_items=1, allow_negative=False, allow_pi=False, allow_zero=False))
            self.Mesh_LE_2.setValidator(UniversalNumericListValidator(
                schema=("float",), max_items=1, allow_negative=True, allow_pi=False))
            self.Mesh_LE_3.setValidator(UniversalNumericListValidator(
                schema=("float",), max_items=1, allow_negative=True, allow_pi=False))
        elif self.Mesh_2D.isChecked():
            self.Mesh_LE_1.setValidator(UniversalNumericListValidator(
                schema=("pos_int",), max_items=2, allow_negative=False, allow_pi=False, allow_zero=False))
            self.Mesh_LE_2.setValidator(UniversalNumericListValidator(
                schema=("float",), max_items=2, allow_negative=True, allow_pi=False))
            self.Mesh_LE_3.setValidator(UniversalNumericListValidator(
                schema=("float",), max_items=2, allow_negative=True, allow_pi=False))
            self.label_2.setText('2 Dimensions (Nx,Ny)')
            self.label_3.setText('Lower Left (x,y)')
            self.label_4.setText('Upper Right (x,y)')
        elif self.Mesh_3D.isChecked():
            self.Mesh_LE_1.setValidator(UniversalNumericListValidator(
                schema=("pos_int",), max_items=3, allow_negative=False, allow_pi=False, allow_zero=False))
            self.Mesh_LE_2.setValidator(UniversalNumericListValidator(
                schema=("float",), max_items=3, allow_negative=True, allow_pi=False))
            self.Mesh_LE_3.setValidator(UniversalNumericListValidator(
                schema=("float",), max_items=3, allow_negative=True, allow_pi=False))
            self.label_2.setText('3 Dimensions (Nx,Ny,Nz)')
            self.label_3.setText('Lower Left (x,y,z)')
            self.label_4.setText('Upper Right (x,y,z)')

    def update_mesh_validator(self):
        if self.MeshType_CB.currentIndex() == 1:                     # RegularMesh.
            if self.Mesh_1D.isChecked():    
                self.Mesh_LE_1.setValidator(UniversalNumericListValidator(
                    schema=("pos_int",), max_items=1, allow_negative=False, allow_pi=False, allow_zero=False))
                self.Mesh_LE_2.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=1, allow_negative=True, allow_pi=False))
                self.Mesh_LE_3.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=1, allow_negative=True, allow_pi=False))
            elif self.Mesh_2D.isChecked(): 
                self.Mesh_LE_1.setValidator(UniversalNumericListValidator(
                    schema=("pos_int",), max_items=2, allow_negative=False, allow_pi=False, allow_zero=False))
                self.Mesh_LE_2.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=2, allow_negative=True, allow_pi=False))
                self.Mesh_LE_3.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=2, allow_negative=True, allow_pi=False))
            elif self.Mesh_3D.isChecked(): 
                self.Mesh_LE_1.setValidator(UniversalNumericListValidator(
                    schema=("pos_int",), max_items=3, allow_negative=False, allow_pi=False, allow_zero=False))
                self.Mesh_LE_2.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=3, allow_negative=True, allow_pi=False))
                self.Mesh_LE_3.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=3, allow_negative=True, allow_pi=False))
        elif self.MeshType_CB.currentIndex() == 2:                     # RectilinearMesh.
            if self.MinMax_RB.isChecked():
                self.Mesh_LE_1.setValidator(UniversalNumericListValidator(
                    schema=("float", "float", "pos_int"), max_items=3, allow_negative=True, allow_pi=False))
            else:
                self.Mesh_LE_1.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=None, allow_negative=True, allow_pi=False))
            
            if self.MinMax_RB_2.isChecked():
                self.Mesh_LE_2.setValidator(UniversalNumericListValidator(
                    schema=("float", "float", "pos_int"), max_items=3, allow_negative=True, allow_pi=False))
            else:
                self.Mesh_LE_2.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=None, allow_negative=True, allow_pi=False))
            
            if self.MinMax_RB_3.isChecked():
                self.Mesh_LE_3.setValidator(UniversalNumericListValidator(
                    schema=("float", "float", "pos_int"), max_items=3, allow_negative=True, allow_pi=False))
            else:
                self.Mesh_LE_3.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=None, allow_negative=True, allow_pi=False))
        elif self.MeshType_CB.currentIndex() == 3:                     # CylindricalMesh.
            if self.MinMax_RB.isChecked():  # R values
                self.Mesh_LE_1.setValidator(UniversalNumericListValidator(
                    schema=("float", "float", "pos_int"), max_items=3, allow_negative=False, allow_pi=False))
            else:
                self.Mesh_LE_1.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=None, allow_negative=False, allow_pi=False))
            if self.MinMax_RB_2.isChecked(): # Phi values
                self.Mesh_LE_2.setValidator(UniversalNumericListValidator(
                    schema=("float", "float", "pos_int"), max_items=3, allow_negative=False, allow_pi=True))
            else:
                self.Mesh_LE_2.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=None, allow_negative=False, allow_pi=True))
            if self.MinMax_RB_3.isChecked(): # Z values
                self.Mesh_LE_3.setValidator(UniversalNumericListValidator(
                    schema=("float", "float", "pos_int"), max_items=3, allow_negative=True, allow_pi=False))
            else:
                self.Mesh_LE_3.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=None, allow_negative=True, allow_pi=False))
        elif self.MeshType_CB.currentIndex() == 4:                     # SphericalMesh.
            if self.MinMax_RB.isChecked():  # R values
                self.Mesh_LE_1.setValidator(UniversalNumericListValidator(
                    schema=("float", "float", "pos_int"), max_items=3, allow_negative=False, allow_pi=False))
            else:
                self.Mesh_LE_1.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=None, allow_negative=False, allow_pi=False))
            if self.MinMax_RB_2.isChecked(): # Theta values
                self.Mesh_LE_2.setValidator(UniversalNumericListValidator(
                    schema=("float", "float", "pos_int"), max_items=3, allow_negative=False, allow_pi=True))
            else:
                self.Mesh_LE_2.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=None, allow_negative=False, allow_pi=True))
            if self.MinMax_RB_3.isChecked(): # Phi values
                self.Mesh_LE_3.setValidator(UniversalNumericListValidator(
                    schema=("float", "float", "pos_int"), max_items=3, allow_negative=False, allow_pi=True))
            else:
                self.Mesh_LE_3.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=None, allow_negative=False, allow_pi=True))

    def sync_mesh_id(self):
        import string
        if self.MeshId_LE.text():
            self.Mesh_ID = int(self.MeshId_LE.text())
            if self.AddMeshId_CB.isChecked():
                self.MeshName_LE.setText(self.mesh_suffix + str(self.Mesh_ID))
                self.mesh_suffix = self.MeshName_LE.text().rstrip(string.digits)
            else:
                self.mesh_suffix = self.MeshName_LE.text().rstrip(string.digits)
                self.MeshName_LE.setText(self.mesh_suffix)

    def Add_Tallies(self):
        self.Create_New_Tally = True
        self.Def_Tallies()
        if self.MGXS_Lib_CB.isChecked():
            msg = 'MGXS Lib'
            self.tally_suffix = 'lib'
        else:
            msg = 'tally'
            self.tally_suffix = '_tally'
            
        if self.Tally_LE.text() == '':
            self.showDialog('Warning', f'Cannot create {msg}, enter name first !')
            return
        else:
            if self.TallyName_LE.text() == '' and not self.MGXS_Lib_CB.isChecked():
                self.showDialog('Warning', 'No title specification entered !')
            if self.Tally_LE.text() in self.tally_name_list:
                self.showDialog('Warning', f'{msg} name already used, enter new name !')
                return
            elif int(self.TallyId_LE.text()) in self.tally_id_list:
                self.showDialog('Warning', f'{msg} id already used, enter new id !')
                return
            else:
                if self.MGXS_Lib_CB.isChecked():
                    print(f"{self.Tally_LE.text()} = openmc.mgxs.Library({self.Geom})")
                else:
                    if self.Add_id_to_tally_def_CB.isChecked():    
                        text = '\n' + self.Tally_LE.text() + ' = openmc.Tally(tally_id=' + self.TallyId_LE.text() + ', '
                    else:
                        text = '\n' + self.Tally_LE.text() + ' = openmc.Tally('
                    if self.TallyName_LE.text():
                        print(text + "name='" + self.TallyName_LE.text() + "')")
                    else:
                        print(text + "name='" + self.title + "')")

        self.tally = self.Tally_LE.text()
        if self.tally not in self.tally_name_list:
            self.tally_name_list.append(self.tally)
            self.tally_id_list.append(self.TallyId_LE.text())
        
        self.TallyName_LE.clear()
        self.tally_id = int(self.tally_id_list[-1]) + 1
        self.TallyId_LE.setText(str(self.tally_id))
        if self.AddTallyId_CB.isChecked():
            self.Tally_LE.setText(self.tally_suffix + str(self.TallyId_LE.text()))
        else:
            self.Tally_LE.setText(self.tally_suffix)
        self.Reset(self.Scores_List, self.ScoresList_LE)
        self.Reset(self.Nuclides_Bins_List, self.Nuclides_Bins_List_LE)
        self.Reset(self.Filters_List, self.Filters_List_LE)

        # Buttons state to be changed each time new tally is created
        self.AddScore_PB.setEnabled(True)
        self.AddFilters_PB.setEnabled(True)
        self.AddNuclides_PB.setEnabled(True)
        self.Add_Trigger_PB.setEnabled(True)

    def Set_From_Domain(self):
        self.From_Domain_LE.clear()
        self.Domain_ComboBox.clear()

        if self.From_Domain_ComboBox.currentText() == 'openmc.Cell':
            self.Domain_ComboBox.addItem('select cell')
            self.Domain_ComboBox.addItems(self.cell_name_list)
        elif self.From_Domain_ComboBox.currentText() == 'openmc.Region':
            self.Domain_ComboBox.addItem('provide region')
        elif self.From_Domain_ComboBox.currentText() == 'openmc.Universe':
            self.Domain_ComboBox.addItem('select universe')
            self.Domain_ComboBox.addItems(self.universe_name_list)
        elif self.From_Domain_ComboBox.currentText() == 'openmc.Geometry':
            self.Domain_ComboBox.addItem(self.Geom)
            self.From_Domain_LE.setText(self.Geom)

    def Set_Domain_LE(self):
        if self.From_Domain_ComboBox.currentText() in ['openmc.Cell', 'openmc.Universe']:
            self.From_Domain_LE.setText(self.Domain_ComboBox.currentText())

    def From_Domain(self):
        radios = [self.Grid_RB, self.MinMax_RB, self.Grid_RB_2, self.MinMax_RB_2, self.Grid_RB_3, self.MinMax_RB_3]
        Widgets = [self.From_Domain_LE, self.From_Domain_ComboBox, self.Domain_ComboBox]
        if self.From_Domain_CB.isChecked():
            self.Mesh_LE_1.setValidator(UniversalNumericListValidator(
                    schema=("pos_int",), max_items=3, allow_negative=False, allow_pi=False, allow_zero=False))
            self.label_4.setEnabled(False)
            self.label_25.setEnabled(False)
            self.Mesh_3D.setChecked(True)
            self.Mesh_1D.setEnabled(False)
            self.Mesh_2D.setEnabled(False)
            self.label_2.setText('Dimensions')
            self.Origin_LE.setToolTip('')

            if self.MeshType_CB.currentIndex() == 1:                     # RegularMesh.
                self.Mesh_LE_1.setToolTip('dimension (Iterable of int | int) – The number of mesh cells in total or number of mesh cells in each direction (x, y, z). \
                                          \nIf a single integer is provided, the domain will will be divided into that many mesh cells with roughly equal lengths in \
                                          \neach direction (cubes).')
                self.From_Domain_ComboBox.setToolTip('domain ({openmc.Cell, openmc.Region, openmc.Universe, openmc.Geometry}) – \
                                                      \nThe object passed in will be used as a template for this mesh. \
                                                      \nThe bounding box of the property of the object passed will be used \
                                                      \nto set the lower_left and upper_right and of the mesh instance')
                self.Mesh_LE_2.setToolTip('')
                self.Mesh_LE_3.setToolTip('')
                self.Mesh_LE_2.setEnabled(False)
                self.Mesh_LE_3.setEnabled(False)
                self.label_3.setEnabled(False)
            elif self.MeshType_CB.currentIndex() == 3:                     # CylindricalMesh.
                self.Mesh_LE_2.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=2, allow_negative=False, allow_pi=True, allow_zero=True))
                self.Mesh_LE_1.setToolTip('dimension (Iterable of int) – The number of equally spaced mesh cells in each direction (r_grid, phi_grid, z_grid)')
                self.Mesh_LE_2.setToolTip('phi_grid_bounds (numpy.ndarray) – Mesh bounds points along the phi-axis in radians. The default value is (0, 2π), i.e., the full phi range.')
                self.From_Domain_CB.setToolTip('domain (openmc.Cell or openmc.Region or openmc.Universe or openmc.Geometry) – \
                                                \nThe object passed in will be used as a template for this mesh. The bounding box \
                                                \nof the property of the object passed will be used to set the r_grid, z_grid ranges.')
                self.Mesh_LE_3.setToolTip('')
                self.label_3.setText('\u03C6_grid bounds')
                self.Mesh_LE_2.setEnabled(True)
                self.label_3.setEnabled(True)
                self.Mesh_LE_3.setEnabled(False)
            elif self.MeshType_CB.currentIndex() == 4:                     # SphericalMesh.
                self.Mesh_LE_2.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=2, allow_negative=False, allow_pi=True, allow_zero=True))
                self.Mesh_LE_3.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=2, allow_negative=False, allow_pi=True, allow_zero=True))

                self.Mesh_LE_1.setToolTip('dimension (Iterable of int) – The number of equally spaced mesh cells in each direction (r_grid, phi_grid, theta_grid). \
                                          \nSpacing is in angular space (radians) for phi and theta, and in absolute space for r.')
                self.Mesh_LE_2.setToolTip('phi_grid_bounds (numpy.ndarray) – Mesh bounds points along the phi-axis in radians. The default value is (0, 2π), i.e., the full phi range.')
                self.Mesh_LE_3.setToolTip('theta_grid_bounds (numpy.ndarray) – Mesh bounds points along the theta-axis in radians. The default value is (0, π), i.e., the full theta range.')
                self.From_Domain_CB.setToolTip('domain (openmc.Cell or openmc.Region or openmc.Universe or openmc.Geometry) – \
                                                \nThe object passed in will be used as a template for this mesh. The bounding box \
                                                \nof the property of the object passed will be used to set the r_grid, z_grid ranges.')
                self.label_3.setText('\u03C6_grid bounds')
                self.label_4.setText('\u0398_grid bounds')
                self.Mesh_LE_2.setEnabled(True)
                self.label_3.setEnabled(True)
                self.Mesh_LE_3.setEnabled(True)
                self.label_4.setEnabled(True)
            else:
                self.Mesh_LE_2.setEnabled(False)
                self.label_3.setEnabled(False)
                self.Mesh_LE_3.setEnabled(False)
            
            self.Origin_LE.setEnabled(False)

            for W in Widgets:
                W.show()
                W.setEnabled(True)

            for radio in radios:
                radio.hide()            
            
            self.From_Domain_ComboBox.addItems(['openmc.Cell', 'openmc.Region', 'openmc.Universe', 'openmc.Geometry'])
            if 'openmc.Universe' not in self.v_1.toPlainText():
                self.From_Domain_ComboBox.model().item(self.From_Domain_ComboBox.findText('openmc.Universe')).setEnabled(False)
        else:
            self.Def_Mesh()

            for W in Widgets:
                W.hide()

            if self.MeshType_CB.currentIndex() == 1:   # Regular mesh
                self.Mesh_LE_2.setEnabled(True)
                self.Mesh_1D.setEnabled(True)
                self.Mesh_2D.setEnabled(True)
            elif self.MeshType_CB.currentIndex() == 3:      # Cylindrical mesh
                self.Mesh_LE_1.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=None, allow_negative=False, allow_pi=False))
           
                for radio in radios:
                    radio.show()

            self.Mesh_LE_3.setEnabled(True)
            self.From_Domain_ComboBox.clear()
            self.From_Domain_ComboBox.addItem('select domain')
            if self.MeshType_CB.currentIndex() in [3, 4]:      # Cylindrical and spherical meshes
                self.Origin_LE.setEnabled(True)
            self.label_3.setEnabled(True)
            self.label_4.setEnabled(True)
            self.label_25.setEnabled(True)

    def Def_Mesh(self):
        self.From_Domain_CB.setChecked(False)
        self.Mesh_3D.setChecked(True)
        self.From_Domain_ComboBox.clear()
        self.From_Domain_ComboBox.addItem('select domain')
        self.Origin_LE.clear()
        W = [self.label_2, self.label_3, self.label_4, self.label_25, 
             self.Mesh_LE_1, self.Mesh_LE_2, self.Mesh_LE_3, self.Origin_LE]
        Ws = [self.From_Domain_CB, self.From_Domain_ComboBox, self.Domain_ComboBox, self.From_Domain_LE]
        radios = [self.Grid_RB, self.MinMax_RB, self.Grid_RB_2, self.MinMax_RB_2, self.Grid_RB_3, self.MinMax_RB_3]

        for Rd in [self.Grid_RB, self.Grid_RB_2, self.Grid_RB_3]:
            Rd.setChecked(True)

        self.Origin_LE.setValidator(UniversalNumericListValidator(
            schema=("float",), max_items=3, allow_negative=True, allow_pi=False, allow_zero=True))

        if self.MeshType_CB.currentIndex() == 0:
            self.Mesh_1D.setEnabled(False)
            self.Mesh_2D.setEnabled(False)
            self.Mesh_3D.setEnabled(False)
            for radio in radios:
                radio.hide()
            for w in W + Ws:
                w.setEnabled(False)
            self.MinMax_RB.hide()
            self.From_Domain_CB.setEnabled(False)
        elif self.MeshType_CB.currentIndex() == 1:                  # RegularMesh
            self.Mesh_LE_1.setToolTip("dimension (Iterable of int) – The number of mesh cells in each direction (x, y, z).")
            self.Mesh_LE_2.setToolTip("lower_left (Iterable of float) – The lower-left corner of the structured mesh. \
                                      \nIf only two coordinate are given, it is assumed that the mesh is an x-y mesh.")
            self.Mesh_LE_3.setToolTip("upper_right (Iterable of float) – The upper-right corner of the structured mesh. \
                                      \nIf only two coordinate are given, it is assumed that the mesh is an x-y mesh.")
            self.From_Domain_CB.show()
            self.From_Domain_CB.setEnabled(True)
            self.Mesh_1D.setEnabled(True)
            self.Mesh_2D.setEnabled(True)
            self.Mesh_3D.setEnabled(True)
            for radio in radios:
                radio.hide()
            for w in W + Ws:
                w.setEnabled(True)
            self.label_2.setText('3 Dimensions (Nx,Ny,Nz)')
            self.label_3.setText('Lower Left (x,y,z)')
            self.label_4.setText('Upper Right (x,y,z)')
            self.Mesh_LE_1.setValidator(UniversalNumericListValidator(
                schema=("pos_int",), max_items=3, allow_negative=False, allow_pi=False, allow_zero=False))
            self.Mesh_LE_2.setValidator(UniversalNumericListValidator(
                schema=("float",), max_items=3, allow_negative=True, allow_pi=False))
            self.Mesh_LE_3.setValidator(UniversalNumericListValidator(
                schema=("float",), max_items=3, allow_negative=True, allow_pi=False))
            self.Origin_LE.setEnabled(False)
            self.label_25.setEnabled(False)
        elif self.MeshType_CB.currentIndex() == 2:                  # RectiLinearMesh
            self.Mesh_LE_1.setToolTip("1-D array of mesh boundary points along the x-axis or (min, max, dim)")
            self.Mesh_LE_2.setToolTip("1-D array of mesh boundary points along the y-axis or (min, max, dim)")
            self.Mesh_LE_3.setToolTip("1-D array of mesh boundary points along the z-axis or (min, max, dim)")
            self.From_Domain_CB.setEnabled(False)
            self.Mesh_1D.setEnabled(False)
            self.Mesh_2D.setEnabled(False)
            self.Mesh_3D.setEnabled(True)
            for radio in radios:
                radio.show()
            for w in W:
                w.setEnabled(True)
            self.label_2.setText('x_grid | min, max, N')
            self.label_3.setText('y_grid | min, max, N')
            self.label_4.setText('z_grid | min, max, N')
            self.Mesh_LE_1.setValidator(UniversalNumericListValidator(
                schema=("float",), max_items=None, allow_negative=True, allow_pi=False))
            self.Mesh_LE_2.setValidator(UniversalNumericListValidator(
                schema=("float",), max_items=None, allow_negative=True, allow_pi=False))
            self.Mesh_LE_3.setValidator(UniversalNumericListValidator(
                schema=("float",), max_items=None, allow_negative=True, allow_pi=False))
            self.Origin_LE.setEnabled(False)
            self.label_25.setEnabled(False)
        elif self.MeshType_CB.currentIndex() == 3:                     # CylindricalMesh
            self.Mesh_LE_1.setToolTip("1-D array of mesh boundary points along the r-axis Requirement is r >= 0. or (min, max, dim)")
            self.Mesh_LE_3.setToolTip("1-D array of mesh boundary points along the z-axis relative to the origin or (min, max, dim)")
            if self.From_Domain_CB.isChecked():
                self.Mesh_LE_2.setToolTip("1-D array of phi boundary points in radians. \nThe default value is [0, 2π] (pi could be used).")
            else:
                self.Mesh_LE_2.setToolTip("1-D array of mesh boundary points along the phi-axis in radians. \nThe default value is [0, 2π] (pi could be used) or (min, max, dim)")

            self.Mesh_LE_1.setValidator(UniversalNumericListValidator(
                schema=("float",), max_items=None, allow_negative=False, allow_pi=False))
            self.Mesh_LE_2.setValidator(UniversalNumericListValidator(
                schema=("float",), max_items=None, allow_negative=False, allow_pi=True))
            self.Mesh_LE_3.setValidator(UniversalNumericListValidator(
                schema=("float",), max_items=None, allow_negative=True, allow_pi=False))      
            self.From_Domain_CB.show()
            self.From_Domain_CB.setEnabled(True)
            self.Mesh_1D.setEnabled(False)
            self.Mesh_2D.setEnabled(False)
            self.Mesh_3D.setEnabled(True)
            for radio in radios:
                radio.show()
            for w in W:
                w.setEnabled(True)
            self.label_2.setText('r_grid | min, max, N')
            if self.From_Domain_CB.isChecked():    
                self.label_3.setText('\u03C6 boundaries')
            else:
                self.label_3.setText('\u03C6_grid | min,max,N')
            self.label_4.setText('z_grid | min, max, N')
        elif self.MeshType_CB.currentIndex() == 4:                     # SphericalMesh
            self.Mesh_LE_1.setToolTip("1-D array of mesh boundary points along the r-axis Requirement is r >= 0. or (min, max, dim)")
            self.Mesh_LE_2.setToolTip("1-D array of mesh boundary points along the \u0398-axis in radians. \nThe default value is [0, π] (pi could be used) or (min, max, dim)")
            self.Mesh_LE_3.setToolTip("1-D array of mesh boundary points along the phi-axis in radians. \nThe default value is [0, 2π] (pi could be used) or (min, max, dim)")
            self.From_Domain_CB.show()
            self.From_Domain_CB.setEnabled(True)
            self.Mesh_1D.setEnabled(False)
            self.Mesh_2D.setEnabled(False)
            self.Mesh_3D.setEnabled(True)
            for radio in radios:
                radio.show()
            for w in W:
                w.setEnabled(True)
            self.label_2.setText('r_grid | min, max, N')
            self.label_3.setText('\u0398_grid | min,max,N')
            self.label_4.setText('\u03C6_grid | min,max,N')
            self.Mesh_LE_1.setValidator(UniversalNumericListValidator(
                schema=("float",), max_items=None, allow_negative=False, allow_pi=False))
            self.Mesh_LE_2.setValidator(UniversalNumericListValidator(
                schema=("float",), max_items=None, allow_negative=False, allow_pi=True))
            self.Mesh_LE_3.setValidator(UniversalNumericListValidator(
                schema=("float",), max_items=None, allow_negative=False, allow_pi=True))
        elif self.MeshType_CB.currentIndex() == 5:                     # UnstructuredMesh
            for w in W:
                w.setEnabled(False)
            for w in Ws:
                w.hide()
            for radio in radios:
                radio.hide()
            self.showDialog('Warning', 'Not coded yet !')
        
    def Create_Mesh(self):
        self.Def_Tallies()
        if self.MeshType_CB.currentIndex() == 0:
            self.showDialog('Warning', 'Select Mesh type first !')
            self.sync_mesh_id()
            return
        if self.MeshName_LE.text() == '':
            self.showDialog('Warning', 'Cannot create mesh, select name first !')
            return
        if self.MeshId_LE.text() == '':
            self.showDialog('Warning', 'Cannot create mesh, select id first !')
            return
        if self.MeshName_LE.text() in self.mesh_name_list:
            self.showDialog('Warning', 'Mesh name already used, select new name or change the id value!')
            return
        if int(self.MeshId_LE.text()) in self.mesh_id_list:
            self.showDialog('Warning', 'Mesh id already used, select new id !')
            return
        if self.Mesh_LE_1.text() == '':
            self.showDialog('Warning', 'Mesh data are missing ! Complete the form !')
            return
        if not self.From_Domain_CB.isChecked():
            if self.Mesh_LE_2.text() == '' or self.Mesh_LE_3.text() == '':
                self.showDialog('Warning', 'Mesh data are missing ! Complete the form !')
                return

        if self.MeshType_CB.currentIndex() == 1:
            self.RegularMesh()
        elif self.MeshType_CB.currentIndex() == 2:
            self.RectiLinearMesh()
        elif self.MeshType_CB.currentIndex() == 3:
            self.CylindricalMesh()
        elif self.MeshType_CB.currentIndex() == 4:
            self.SphericalMesh()           
        elif self.MeshType_CB.currentIndex() == 5:
            self.UnstructuredMesh()
        if self.No_Error:
            self.mesh_name_list.append(self.MeshName_LE.text())
            self.mesh_id_list.append(self.MeshId_LE.text())
            self.Mesh_ID = int(self.mesh_id_list[-1]) + 1
            self.MeshId_LE.setText(str(self.Mesh_ID))
            if self.AddMeshId_CB.isChecked():
                self.MeshName_LE.setText(self.mesh_suffix + str(self.MeshId_LE.text()))
            else:
                self.MeshName_LE.setText(self.mesh_suffix)

            self.Mesh_LE_1.clear()
            self.Mesh_LE_2.clear()
            self.Mesh_LE_3.clear()
            #self.Mesh_1D.setChecked(True)
            self.MeshType_CB.setCurrentIndex(0)
            self.FilterType_CB.setCurrentIndex(0)
            self.Filter_Bins_List_LE.clear()
            self.From_Domain_ComboBox.setCurrentIndex(0)
            self.From_Domain_LE.clear()
            self.Add_Id_Mesh_Par_CB.setChecked(False)

    def RegularMesh(self):
        self.No_Error = True
        dimension = list(map(int, self.LE_to_List1(self.Mesh_LE_1)))
        if not self.From_Domain_CB.isChecked():
            LL = list(map(float, self.LE_to_List1(self.Mesh_LE_2)))
            UR = list(map(float, self.LE_to_List1(self.Mesh_LE_3)))

            for i in range(len(LL)):
                if LL[i] == UR[i]:
                    self.showDialog('Warning', 'Mesh cannot have zero thickness in any dimension!')
                    self.No_Error = False
                    return
                elif LL[i] > UR[i]:
                    self.showDialog('Warning', 'The <upper_right> coordinates must be greater than the <lower_left> coordinates on a tally mesh!')
                    self.No_Error = False
                    return
            
        if self.Mesh_1D.isChecked():
            if len(dimension) != 1:
                self.showDialog('Warning', 'Length of dimension list is not compatible with 1D mesh !')
                self.No_Error = False
                return
            if not self.From_Domain_CB.isChecked():
                if len(LL) != 1 or len(UR) != 1:
                    self.showDialog('Warning', 'Lower_left and Upper_right coordinates number must be equal to 1 !')
                    self.No_Error = False
                    return
        elif self.Mesh_2D.isChecked():
            if len(dimension) != 2:
                self.showDialog('Warning', 'Length of dimension list is not compatible with 2D mesh !')
                self.No_Error = False
                return
            if not self.From_Domain_CB.isChecked():
                if len(LL) != 2 or len(UR) != 2:
                    self.showDialog('Warning', 'Lower_left and Upper_right coordinates number must be equal to 2 !')
                    self.No_Error = False
                    return
        elif self.Mesh_3D.isChecked():
            if self.From_Domain_CB.isChecked():
                if len(dimension) == 2:
                    self.showDialog('Warning', 'Length of dimension list is not compatible with 3D mesh !\
                                    \nEnter one value for total number of mesh cells or 3 integers for each direction.')
                    self.No_Error = False
                    return    
            else:
                if len(dimension) != 3:
                    self.showDialog('Warning', 'Length of dimension list is not compatible with 3D mesh !')
                    self.No_Error = False
                    return
                if len(LL) != 3 or len(UR) != 3:
                    self.showDialog('Warning', 'Lower_left or Upper_right coordinates number must be equal to 3 !')
                    self.No_Error = False
                    return
                
        if self.Add_Id_Mesh_Par_CB.isChecked():
            Mesh_Id = 'mesh_id=' + self.MeshId_LE.text() + ', '
        else:
            Mesh_Id = ''

        if self.From_Domain_CB.isChecked():   # the corners of the mesh are being set automatically to surround the geometry
            if self.From_Domain_ComboBox.currentIndex() == 0:
                self.showDialog('Warning', 'Select domain type first!')
                self.No_Error = False
                return      
                  
            if self.Domain_ComboBox.currentIndex() == 0:
                if self.From_Domain_ComboBox.currentText() == 'openmc.Region' and self.From_Domain_LE.text() == '':
                    self.showDialog('Warning', 'provide region first!')
                    self.No_Error = False
                    return
                
                if self.From_Domain_ComboBox.currentText() not in ['openmc.Geometry', 'openmc.Region']:
                    self.showDialog('Warning', 'Select domain first!')
                    self.No_Error = False
                    return

            Line1 = f"{self.MeshName_LE.text()} = openmc.RegularMesh.from_domain({self.From_Domain_LE.text()}," 
            Line2 = f" dimension={str(dimension)}, {Mesh_Id}name='{self.MeshName_LE.text()}')\n"
            print(Line1 + Line2)
        else:
            print(f"\n{self.MeshName_LE.text()} = openmc.{self.MeshType_CB.currentText()}({Mesh_Id}name='{self.MeshName_LE.text()}')\n")
            print(self.MeshName_LE.text() + '.dimension = ' + str(dimension))
            print(self.MeshName_LE.text() + '.lower_left = ' + str(LL))
            print(self.MeshName_LE.text() + '.upper_right = ' + str(UR))

    def RectiLinearMesh(self):
        self.No_Error = True
        Swapped = False
        mesh_name = self.MeshName_LE.text()
        if self.MinMax_RB.isChecked():
            List = self.LE_to_List(self.Mesh_LE_1, False)
            if len(List) != 3:
                self.showDialog('Warning', 'Number of entries must be equal to 3 or check the x_grid radio button !')
                self.No_Error = False
                return
            
            if List[1] < List[0]:
                Swapped = True
                List[0], List[1] = List[1], List[0]

            x_Lower = float(List[0])
            x_Upper = float(List[1])
            x_Dim   = int(List[2])
            msg_x = f"{mesh_name}.x_grid = np.linspace({x_Lower}, {x_Upper}, {x_Dim})"
        else:
            List = self.LE_to_List(self.Mesh_LE_1, True)
            List = [float(e) for e in List]
            msg_x = f"{mesh_name}.x_grid = {List}"
            
        if self.MinMax_RB_2.isChecked():
            List = self.LE_to_List(self.Mesh_LE_2, False)
            if len(List) != 3:
                self.showDialog('Warning', 'Number of entries must be equal to 3 !')
                self.No_Error = False
                return
            
            if List[1] < List[0]:
                Swapped = True
                List[0], List[1] = List[1], List[0]

            y_Lower = float(List[0])
            y_Upper = float(List[1])
            y_Dim = int(List[2])
            msg_y = f"{mesh_name}.y_grid = np.linspace({y_Lower}, {y_Upper}, {y_Dim})"
        else:
            List = self.LE_to_List(self.Mesh_LE_2, True)
            List = [float(e) for e in List]
            msg_y = f"{mesh_name}.y_grid = {List}"
           
        if self.MinMax_RB_3.isChecked():
            List = self.LE_to_List(self.Mesh_LE_3, False)
            if len(List) != 3:
                self.No_Error = False
                self.showDialog('Warning', 'Number of entries must be equal to 3 !')
                return
            
            if List[1] < List[0]:
                Swapped = True
                List[0], List[1] = List[1], List[0]

            z_Lower = float(List[0])
            z_Upper = float(List[1])
            z_Dim = int(List[2])
            msg_z = f"{mesh_name}.z_grid = np.linspace({z_Lower}, {z_Upper}, {z_Dim})"
        else:
            List = self.LE_to_List(self.Mesh_LE_3, True)
            List = [float(e) for e in List]
            msg_z = f"{mesh_name}.z_grid = {List}"
        
        if Swapped:
            self.showDialog('Warning', 'Upper limit must be greater than Lower limit !\nEntries will be swapped')

        if self.Add_Id_Mesh_Par_CB.isChecked():
            Mesh_Id = 'mesh_id=' + self.MeshId_LE.text() + ', '
        else:
            Mesh_Id = ''   
        
        print(f"\n{mesh_name} = openmc.{self.MeshType_CB.currentText()}({Mesh_Id}name='{self.MeshName_LE.text()}')\n")
        print(msg_x)
        print(msg_y)
        print(msg_z)

    def CylindricalMesh(self):
        Swapped = False
        self.No_Error = True
        if self.MinMax_RB.isChecked():
            List = self.LE_to_List(self.Mesh_LE_1, False) 

            if len(List) != 3:
                self.showDialog('Warning', 'Number of entries must be equal to 3 !')
                self.No_Error = False
                return
            
            if List[1] < List[0]:
                Swapped = True
                List[0], List[1] = List[1], List[0]

            r_Lower = float(List[0])
            r_Upper = float(List[1])
            r_Dim   = int(float(List[2]))
            msg_r = f"r_grid = np.linspace({r_Lower}, {r_Upper}, {r_Dim})"
        else:
            List = self.LE_to_List(self.Mesh_LE_1, True)
            List = [float(e) for e in List]
            msg_r = f"r_grid = {List}"  
        
        if self.From_Domain_CB.isChecked():
            if self.From_Domain_ComboBox.currentIndex() == 0:
                self.showDialog('Warning', 'Select domain type first!')
                self.No_Error = False
                return            
            
            if self.Domain_ComboBox.currentIndex() == 0:
                if self.From_Domain_ComboBox.currentText() == 'openmc.Region' and self.From_Domain_LE.text() == '':
                    self.showDialog('Warning', 'provide region first!')
                    self.No_Error = False
                    return
                
                if self.From_Domain_ComboBox.currentText() not in ['openmc.Geometry', 'openmc.Region']:
                    self.showDialog('Warning', 'Select domain first!')
                    self.No_Error = False
                    return
                
            List = self.LE_to_List(self.Mesh_LE_2, False)
            
            if len(List) == 0:   
                Line3 = ''
            elif len(List) == 2:
                if eval(List[1]) < eval(List[0]):
                    Swapped = True
                    List[0], List[1] = List[1], List[0]
            
                if 'pi' in List[0]:
                    phi_Lower = List[0]  
                else:
                    phi_Lower = float(List[0])
                
                if 'pi' in List[1]:
                    phi_Upper = List[1]  
                else:
                    phi_Upper = float(List[1])
                
                Line3 = f", phi_grid_bounds=({phi_Lower}, {phi_Upper})"
            else:
                self.showDialog('Warning', '2 values must be given : Lower limit and Upper limit of phi \nor keep blank for default values 0 and 2pi !')
                return

        if self.MinMax_RB_2.isChecked():
            List = self.LE_to_List(self.Mesh_LE_2, False)
            
            if len(List) != 3:
                self.showDialog('Warning', 'Number of entries must be equal to 3 !')
                self.No_Error = False
                return

            if 'pi' in List[0]:
                phi_Lower = self.Replace_PI_N(List[0])  
            else:
                phi_Lower = List[0]
            
            if 'pi' in List[1]:
                phi_Upper = self.Replace_PI_N(List[1])  
            else:
                phi_Upper = List[1]

            if eval(phi_Upper) < eval(phi_Lower):
                Swapped = True
                phi_Lower, phi_Upper = phi_Upper, phi_Lower

            try:
                phi_Lower = float(phi_Lower)
            except:
                pass

            try:
                phi_Upper = float(phi_Upper)
            except:
                pass
            
            phi_Dim = int(List[2])
            e = f"({phi_Lower}, {phi_Upper}, {phi_Dim})"
            msg_phi = f"phi_grid = np.linspace({e})"
        else:
            List = self.LE_to_List(self.Mesh_LE_2, True)
            List = [float(e) if 'pi' not in e else e for e in List]
            msg_phi = re.sub(r'["\']', '', f"phi_grid = {List}")
        
        if self.MinMax_RB_3.isChecked():
            List = self.LE_to_List(self.Mesh_LE_3, False)
            
            if len(List) != 3:
                self.No_Error = False
                self.showDialog('Warning', 'Number of entries must be equal to 3 !')
                return
            
            if List[1] < List[0]:
                Swapped = True
                List[0], List[1] = List[1], List[0]

            z_Lower = float(List[0])
            z_Upper = float(List[1])
            z_Dim = int(float(List[2]))

            if z_Lower > z_Upper :
                self.No_Error = False
                return
            msg_z = f"z_grid = np.linspace({z_Lower}, {z_Upper}, {z_Dim})"
        else:
            List = self.LE_to_List(self.Mesh_LE_3, True)
            List = [float(e) for e in List]
            msg_z = f"z_grid = {List}"

        self.Find_string(self.plainTextEdit, "import numpy")
        if self.Insert_Header:
            self.Find_string(self.v_1, "import numpy")
            if self.Insert_Header:
                print('import numpy as np')
        
        if Swapped:
            self.showDialog('Warning', 'Upper limit must be greater than Lower limit !\nEntries will be swapped')

        if self.Add_Id_Mesh_Par_CB.isChecked():
            msg_mesh_id = 'mesh_id=' + self.MeshId_LE.text() + ', '
        else:
            msg_mesh_id = ''
        
        if self.From_Domain_CB.isChecked():   # the corners of the mesh are being set automatically to surround the geometry
            List = self.LE_to_List(self.Mesh_LE_1, False)
            dimension = list(map(int, List))
            if len(dimension) != 3:
                self.showDialog('Warning', 'Length of dimension list is not compatible with 3D mesh !')
                return
            Line1 = f"\n{self.MeshName_LE.text()} = openmc.CylindricalMesh.from_domain({self.From_Domain_LE.text()}," 
            Line2 = f" dimension={str(dimension)}" 
            Line4 = f", {msg_mesh_id}name='{self.MeshName_LE.text()}')"
            print(Line1 + Line2 + Line3 + Line4)
        else:
            print(msg_r)
            print(msg_phi)
            print(msg_z)
            Origin = self.Def_Origin()
            print(f"\n{self.MeshName_LE.text()} = openmc.{self.MeshType_CB.currentText()}(r_grid=r_grid, z_grid=z_grid, phi_grid=phi_grid{Origin}, {msg_mesh_id}name='{self.MeshName_LE.text()}')\n")

    def SphericalMesh(self):
        self.No_Error = True
        Swapped = False

        if self.From_Domain_CB.isChecked():
            if self.From_Domain_ComboBox.currentIndex() == 0:
                self.showDialog('Warning', 'Select domain type first!')
                self.No_Error = False
                return            
            
            if self.Domain_ComboBox.currentIndex() == 0:
                if self.From_Domain_ComboBox.currentText() == 'openmc.Region' and self.From_Domain_LE.text() == '':
                    self.showDialog('Warning', 'provide region first!')
                    self.No_Error = False
                    return
                
                if self.From_Domain_ComboBox.currentText() not in ['openmc.Geometry', 'openmc.Region']:
                    self.showDialog('Warning', 'Select domain first!')
                    self.No_Error = False
                    return
                
            List = self.LE_to_List(self.Mesh_LE_2, False)
            if len(List) == 0:   # default (0, 2pi)
                Line3 = ')\n'
            elif len(List) == 2:
                if eval(List[1]) < eval(List[0]):
                    Swapped = True
                    List[0], List[1] = List[1], List[0]
            
                if 'pi' in List[0]:
                    phi_Lower = List[0]  
                else:
                    phi_Lower = float(List[0])

                if 'pi' in List[1]:
                    phi_Upper = List[1]   
                else:
                    phi_Upper = float(List[1])

                Line3 = f", phi_grid_bounds=({phi_Lower}, {phi_Upper})"
            else:
                self.showDialog('Warning', '2 values must be given : Lower limit and Upper limit of phi \nor keep blank for default values 0 and 2pi !')
                return

            List = self.LE_to_List(self.Mesh_LE_3, False)
            
            if len(List) == 0:   # default (0, 2pi)
                Line4 = ')\n'
            elif len(List) == 2:
                if eval(List[1]) < eval(List[0]):
                    Swapped = True
                    List[0], List[1] = List[1], List[0]
            
                if 'pi' in List[0]:
                    theta_Lower = List[0] 
                else:
                    theta_Lower = float(List[0])
                
                if 'pi' in List[1] or '*' in List[1]:
                    theta_Upper = List[1]   
                else:
                    theta_Upper = float(List[1])

                Line4 = f", theta_grid_bounds=({theta_Lower}, {theta_Upper}))\n"
            else:
                self.showDialog('Warning', '2 values must be given : Lower limit and Upper limit of phi \nor keep blank for default values 0 and 2pi !')
                return
        else:
            if self.MinMax_RB.isChecked():
                List = self.LE_to_List(self.Mesh_LE_1, False) 

                if len(List) != 3:
                    self.showDialog('Warning', 'Number of entries must be equal to 3 !')
                    self.No_Error = False
                    return
                
                if List[1] < List[0]:
                    Swapped = True
                    List[0], List[1] = List[1], List[0]

                r_Lower = float(List[0])
                r_Upper = float(List[1])
                r_Dim   = int(List[2])
                msg_r = f"r_grid = np.linspace({r_Lower}, {r_Upper}, {r_Dim})"
            else:
                List = self.LE_to_List(self.Mesh_LE_1, True)
                List = [float(e) for e in List]
                msg_r = f"r_grid = {List}"
            
            if self.MinMax_RB_2.isChecked():
                List = self.LE_to_List(self.Mesh_LE_2, False)
                
                if len(List) != 3:
                    self.showDialog('Warning', 'Number of entries must be equal to 3 !')
                    self.No_Error = False
                    return

                if 'pi' in List[0]:
                    theta_Lower = self.Replace_PI_N(List[0])
                else:
                    theta_Lower = List[0]
                
                if 'pi' in List[1]:
                    theta_Upper = self.Replace_PI_N(List[1])
                else:
                    theta_Upper = List[1]
                
                if eval(theta_Upper) < eval(theta_Lower):
                    Swapped = True
                    theta_Lower, theta_Upper = theta_Upper, theta_Lower

                try:
                    theta_Lower = float(theta_Lower)
                except:
                    pass

                try:
                    theta_Upper = float(theta_Upper)
                except:
                    pass

                theta_Dim = int(List[2])
                e = f"({theta_Lower}, {theta_Upper}, {theta_Dim})"
                msg_theta = f"theta_grid = np.linspace({e})"
            else:
                List = self.LE_to_List(self.Mesh_LE_2, True)
                List = [float(e) if 'pi' not in e else e for e in List]
                msg_theta = re.sub(r'["\']', '', f"theta_grid = {List}")        
        
            if self.MinMax_RB_3.isChecked():
                List = self.LE_to_List(self.Mesh_LE_3, False)
                
                if len(List) != 3:
                    self.showDialog('Warning', 'Number of entries must be equal to 3 !')
                    self.No_Error = False
                    return

                if 'pi' in List[0]:
                    phi_Lower = self.Replace_PI_N(List[0])   
                else:
                    phi_Lower = List[0]
                
                if 'pi' in List[1]:
                    phi_Upper = self.Replace_PI_N(List[1])  
                else:
                    phi_Upper = List[1]

                if eval(phi_Upper) < eval(phi_Lower):
                    Swapped = True
                    phi_Lower, phi_Upper = phi_Upper, phi_Lower

                try:
                    phi_Lower = float(phi_Lower)
                except:
                    pass

                try:
                    phi_Upper = float(phi_Upper)
                except:
                    pass

                phi_Dim = int(List[2])
                e = f"({phi_Lower}, {phi_Upper}, {phi_Dim})"
                msg_phi = f"phi_grid = np.linspace({e})"
            else:
                List = self.LE_to_List(self.Mesh_LE_3, True)
                List = [float(e) if 'pi' not in e else e for e in List]
                msg_phi = re.sub(r'["\']', '', f"phi_grid = {List}")

        if self.Add_Id_Mesh_Par_CB.isChecked():
            Mesh_Id = 'mesh_id=' + self.MeshId_LE.text() + ', '
        else:
            Mesh_Id = ''   
        
        if Swapped:
            self.showDialog('Warning', 'Upper limit must be greater than Lower limit !\nEntries will be swapped')

        if self.From_Domain_CB.isChecked():   # the corners of the mesh are being set automatically to surround the geometry
            List = self.LE_to_List(self.Mesh_LE_1, False)
            dimension = list(map(int, List))
            if len(dimension) != 3:
                self.showDialog('Warning', 'Length of dimension list is not compatible with 3D mesh !')
                return
            Line1 = f"\n{self.MeshName_LE.text()} = openmc.SphericalMesh.from_domain({self.From_Domain_LE.text()}," 
            Line2 = f" {Mesh_Id}name='{self.MeshName_LE.text()}', dimension={str(dimension)}"
            #print(Line1 + Line2 + Line3.replace("'", '') + Line4.replace("'", ''))
            print(Line1 + Line2 + Line3 + Line4)
        else:
            print(msg_r)
            print(msg_theta)
            print(msg_phi)
            Origin = self.Def_Origin()
            print(f"\n{self.MeshName_LE.text()} = openmc.{self.MeshType_CB.currentText()}(r_grid=r_grid, phi_grid=phi_grid, theta_grid=theta_grid{Origin}, {Mesh_Id}name='{self.MeshName_LE.text()}')\n")

    def Def_Origin(self):
        # origin definition
        List = self.LE_to_List1(self.Origin_LE)
        if len(List) == 0:
            msg_origin = ''
        elif len(List) < 3:
            self.No_Error = False
            self.showDialog('Warning', 'Number of entries for origin must be equal to 3 !')
            return
        elif len(List) == 3:
            if all(x == '0' for x in List):
                msg_origin = ''
            else: 
                msg_origin = f", origin={float(List[0]), float(List[1]), float(List[2])}"
        
        if msg_origin != '':
                msg_origin = msg_origin.replace("'", "")

        return msg_origin

    def UnstructuredMesh(self):
        self.No_Error = True
        self.showDialog('Warning', 'Under construction !')

    def Create_Filters(self):
        self.Def_Tallies()
        if self.FilterType_CB.currentIndex() == 0:
            self.showDialog('Warning', 'Select Filter type first !')
            self.sync_filter_id()
            return        
        if self.FilterName_LE.text() == '':
            self.showDialog('Warning', 'Cannot create filter, select name first !')
            return
        if self.FilterId_LE.text() == '':
            self.showDialog('Warning', 'Cannot create filter, select id first !')
            return
        if self.FilterName_LE.text() in self.filter_name_list:
            self.showDialog('Warning', 'Filter name already used, select new name !')
            return
        elif int(self.FilterId_LE.text()) in self.filter_id_list:
            self.showDialog('Warning', 'Filter id already used, select new id !')
            return
        if self.FilterType_CB.currentIndex() != 24:
            bins = self.Filter_Bins_List_LE.text().replace("'", "").replace('[', '').replace(']', '')
            self.Filter_Bins_List_LE.setText(bins)

        if self.Add_ID_Filter_Par_CB.isChecked():    
            FILTER_ID = ', filter_id=' + self.FilterId_LE.text()
        else:
            FILTER_ID = ''
        if self.FilterType_CB.currentIndex() in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 16, 25]:
            if self.Filter_Bins_List_LE.text() == '':
                self.showDialog('Warning', 'No filter bins selected')
                return
            else:
                bins = self.LE_to_List(self.Filter_Bins_List_LE, False)
                if self.FilterType_CB.currentIndex() in [7, 25]:
                    bins = list(set(map(int, bins)))
                else:
                    difference = list(set(bins) - set(self.Allowed_Filter_Bins))
                    if difference:
                        self.showDialog('Warning', 'The following bins ' + str(difference).replace("'", '') + ' are not in actual bins !')
                        remaining = list(set(bins) - set(difference))
                        if remaining:
                            self.Filter_Bins_List_LE.setText(str(sorted(remaining)))
                        else:
                            self.Filter_Bins_List_LE.clear()
                        return
                
            if self.FilterType_CB.currentIndex() not in [6, 9, 16]:
                print(self.FilterName_LE.text() + ' = openmc.' + self.FilterType_CB.currentText() + '(' + str(
                      bins).replace("'", "") + FILTER_ID + ')')
            elif self.FilterType_CB.currentIndex() == 6:
                instances = ''
                for cell in self.Filter_Bins_List:
                    instance = '[(' + cell + ', i) for i in range(' + cell + '.num_instances)]'
                    if len(self.Filter_Bins_List) == 1:
                        instances += '(' + instance + ')'
                    elif cell == self.Filter_Bins_List[0]:
                        instances += '(' + instance + ' +\n'
                    elif cell == self.Filter_Bins_List[-1]:
                        instances += '             ' + instance + ')'
                    else:
                        instances += '             ' + instance + ' +\n'
                Path_str = f"{self.Geom}.determine_paths()"
                if Path_str not in self.v_1.toPlainText():
                    print(Path_str)
                print('instances = ' + instances)
                print(self.FilterName_LE.text() + ' = openmc.' + self.FilterType_CB.currentText() + '(instances ' + FILTER_ID + ')')
            elif self.FilterType_CB.currentIndex() in [9, 16]:
                if len(self.Filter_Bins_List) != 1:
                    self.showDialog('Warning', 'Only first bin will be considered !')
                print(self.FilterName_LE.text() + ' = openmc.' + self.FilterType_CB.currentText() + '(' +
                      self.Filter_Bins_List[0] + FILTER_ID + ')')

        elif self.FilterType_CB.currentIndex() in [11, 12, 13, 14, 15]:
            if self.Filter_Bins_CB.currentIndex() == 0:
                self.showDialog('Warning', 'Select option first !')
                return
            elif self.Filter_Bins_CB.currentIndex() in [1, 2]:
                if self.Filter_Bins_List_LE.text() == '':
                    self.showDialog('Warning', 'No filter bins selected !')
                    return
                else:
                    bins = self.LE_to_List(self.Filter_Bins_List_LE, True)

                    print(self.FilterName_LE.text() + ' = openmc.' + self.FilterType_CB.currentText() + '(' + str(
                          bins).replace("'", "") + FILTER_ID + ')')

            elif self.Filter_Bins_CB.currentIndex() in [3, 4]:
                if self.Start_LE.text() == '' or self.End_LE.text() == '' or self.GrpNumber_LE.text() == '':
                    self.showDialog('Warning', 'Groups number, Start Value and End Value must be given !')
                    return
                else:
                    if int(self.GrpNumber_LE.text()) == 0:
                        self.showDialog('Warning', 'Groups number value must be different from 0 !')
                        return
                    if self.Filter_Bins_CB.currentIndex() == 3:
                        self.Create_Equal_Step_Grid()
                    elif self.Filter_Bins_CB.currentIndex() == 4:
                        self.Create_Equal_Lethargy_Energy_Grid()
            elif self.Filter_Bins_CB.currentIndex() == 5:
                if self.MGX_CB.currentIndex() == 0:
                    self.showDialog('Warning', 'Select MGX Structure first !')
                    return
                else:
                    self.MGX_GROUP_STRUCTURES()
        elif self.FilterType_CB.currentIndex() == 17:
                bins = self.LE_to_List(self.Filter_Bins_List_LE, True)
                bins = list(set(map(int, bins)))
                bins.sort()
                for item in bins:
                    if item not in [1, 2, 3, 4, 5, 6]:
                        self.showDialog('Warning', 'Input groups may not be compatible with ENDF/B-VII.1 which uses 6 precursor groups !')
                        print(f"# Group {item} is is not compatible with 6 groups used in ENDF/B-VII.1")
                print(self.FilterName_LE.text() + ' = openmc.' + self.FilterType_CB.currentText() + '(' + str(
                    bins).replace("'", "") + FILTER_ID + ')')
        elif self.FilterType_CB.currentIndex() == 18:
            if self.Start_LE.text() == '':
                self.showDialog('Warning', 'No grid of energy values entered!')
                return
            elif self.End_LE.text() == '':
                self.showDialog('Warning', 'No grid of interpolant values  entered!')
                return
            else:
                bins_1 = self.LE_to_List(self.Start_LE, True)
                #bins_1 = list(set(map(float, bins_1)))
                bins_2 = self.LE_to_List(self.End_LE, True)
                #bins_2 = list(set(map(float, bins_2)))
                print('energy = ' + str(bins_1).replace("'", ""))
                print('y = ' + str(bins_2).replace("'", ""))
                print(self.FilterName_LE.text() + ' = openmc.' + self.FilterType_CB.currentText() + '(energy, y, ' + 
                        "interpolation='" + self.comboBox.currentText() + "'" + FILTER_ID + ')')
        elif self.FilterType_CB.currentIndex() in [19, 21]:
            print(self.FilterName_LE.text() + ' = openmc.' + self.FilterType_CB.currentText() + '(order= ' + self.GrpNumber_LE.text()
                  + FILTER_ID + ')')
        elif self.FilterType_CB.currentIndex() == 20:
            if self.MGX_CB.currentIndex() == 0:
                self.showDialog('Warning', 'Select axis first !')
                return
            print(self.MGX_CB.currentText() + 'min = ', self.Start_LE.text())
            print(self.MGX_CB.currentText() + 'max = ', self.End_LE.text())
            print(self.FilterName_LE.text() + ' = openmc.' + self.FilterType_CB.currentText() + '(order= ' + self.GrpNumber_LE.text()
                  + ", '" + self.MGX_CB.currentText() + "', axis=" + self.MGX_CB.currentText() + 'minimum= min' + ', ' 
                  + self.MGX_CB.currentText() + 'maximum= max' + FILTER_ID + ')')
        elif self.FilterType_CB.currentIndex() in [22, 23]:
            if self.Start_LE.text() == '' or self.End_LE.text() == '' or self.GrpNumber_LE.text() == '' or self.Filter_Bins_List_LE.text() == '':
                self.showDialog('Warning', 'Enter data first !')
                return
            else:
                print(self.FilterName_LE.text() + ' = openmc.' + self.FilterType_CB.currentText() + '(order= ' + self.Filter_Bins_List_LE.text()
                    + ", x= " + self.Start_LE.text() + ", y= " + self.End_LE.text() + ', r= ' + self.GrpNumber_LE.text() +
                      FILTER_ID + ')')
        elif self.FilterType_CB.currentIndex() == 24:
            print(self.FilterName_LE.text() + ' = openmc.' + self.FilterType_CB.currentText() + '(' +
                str(self.Filter_Bins_List_LE.text()) + FILTER_ID + ')')
        index = self.Filters_List_CB.findText('Select Filter')
        if index == -1:
            self.Filters_List_CB.addItems(['Select Filter', 'All filters'])
            self.Filters_List_CB.addItems(self.filter_name_list)
        self.Filters_List_CB.addItem(self.FilterName_LE.text())
        self.filter_name_list.append(self.FilterName_LE.text())
        self.filter_id_list.append(self.FilterId_LE.text())
        self.Filter_ID = int(self.filter_id_list[-1]) + 1
        self.FilterId_LE.setText(str(self.Filter_ID))
        self.FilterType_CB.setCurrentIndex(0)
        self.FilterName_LE.setText('_filter')
        self.Filter_Bins_List_LE.clear()
        self.Filter_Bins_List_LE.setEnabled(False)
        self.GrpNumber_LE.clear()
        self.Start_LE.clear()
        self.End_LE.clear()
        self.sync_filter_id()
        self.Show_Hide_Widgets()

    def Update_Filters(self):
        self.Filter_Bins_List = []
        self.Allowed_Filter_Bins = []
        if self.FilterType_CB.currentIndex() in [1, 2, 3, 4, 5, 6, 8, 9, 10, 16]:
            self.Filter_Bins_CB.setEnabled(True)
            self.Filter_Bins_List_LE.setValidator(None)
        elif self.FilterType_CB.currentIndex() == 7:
            self.Filter_Bins_List_LE.setEnabled(True)
        elif self.FilterType_CB.currentIndex() in [11, 12]:
            self.Filter_Bins_CB.setEnabled(True)
            self.Filter_Bins_CB.clear()
            self.Filter_Bins_CB.addItems(['Select option', 'Enter data', 'Load text file', 'Equal-Step Energies', 'Equal-Lethargy Energies', 'MGX.GRP_STRUCTURES'])
        elif self.FilterType_CB.currentIndex() in [13, 14, 15]:
            self.Filter_Bins_CB.setEnabled(True)
            self.Filter_Bins_CB.clear()
            if self.FilterType_CB.currentIndex() == 13:
                self.Filter_Bins_CB.addItems(['Select option', 'Enter data', 'Load text file', 'Equal-Step Mu'])
            elif self.FilterType_CB.currentIndex() == 14:
                self.Filter_Bins_CB.addItems(['Select option', 'Enter data', 'Load text file', 'Equal-Step polar angle'])
            elif self.FilterType_CB.currentIndex() == 15:
                self.Filter_Bins_CB.addItems(['Select option', 'Enter data', 'Load text file', 'Equal-Step azimutal angle'])
        else:
            self.Filter_Bins_CB.setEnabled(False)
            self.Filter_Bins_List_LE.clear()
        
        if self.FilterType_CB.currentIndex() == 0:
            self.FilterName_LE.setText('_filter')
            self.Filter_Bins_CB.clear()
        elif self.FilterType_CB.currentIndex() not in [11, 12, 13, 14, 15]:
            self.FilterName_LE.setText(self.FILTER_SUFFIX[self.FilterType_CB.currentIndex() - 1].replace("'", ''))
            self.Filter_Bins_CB.clear()
            self.Filter_Bins_CB.addItem('Select bins')
            if self.FilterType_CB.currentIndex() in [1, 2, 3, 4, 5, 8, 10]:  # !!!!!!!!!!!!!!!!!!!!!!
                self.Filter_Bins_CB.addItem('All bins')
            if self.FilterType_CB.currentIndex() in [1, 2, 3, 4, 5, 6, 8, 9, 10, 16]:
                self.Allowed_Filter_Bins = self.Availble_Filters[self.FilterType_CB.currentText()]
                self.Filter_Bins_CB.addItems(self.Allowed_Filter_Bins)
        
        if self.FilterType_CB.currentIndex() in [18]:
            self.GrpNumber_LE.hide()
            self.comboBox.show()  
            self.label.setText('Interpolation scheme') 
        else:
            self.comboBox.hide()
        
        if self.FilterType_CB.currentIndex() == 0:
            self.FilterName_LE.setText('_filter')
        elif self.FilterType_CB.currentIndex() in [17, 24]:
            self.Filter_Bins_CB.addItem('All bins')
            if self.FilterType_CB.currentIndex() == 17:
                self.Filter_Bins_CB.addItems(self.DELAYED_GROUPS)
            else:
                self.Filter_Bins_CB.addItems(self.PARTICLE_TYPE)
            self.Filter_Bins_CB.setEnabled(True)
        else:
            self.FilterName_LE.setText(self.FILTER_SUFFIX[self.FilterType_CB.currentIndex() - 1].replace("'", ''))

        self.sync_filter_id()

    def Import_Grid_List(self, LineEd):
        file = QtWidgets.QFileDialog.getOpenFileName(self, 'Open File', "~", "*;; *.inp;; *.dat;; *.txt")[0]
        x = []
        if file:
            f = open(file, "r")
            lines = f.readlines()
            for line in lines:
                for separator in [',', ';', ':', ' ']:
                    if separator in line:
                        line.replace(separator, ' ')
                x.append(line.split())
            f.close()
            LineEd.setText(str(x).replace("'", ""))

    def Create_Equal_Step_Grid(self):
        List = []
        if self.Add_ID_Filter_Par_CB.isChecked():    
            FILTER_ID = ', filter_id=' + self.FilterId_LE.text()
        else:
            FILTER_ID = ''
        self.Find_string(self.plainTextEdit, "import numpy") 
        
        if self.Insert_Header:
            self.Find_string(self.v_1, "import numpy")
            if self.Insert_Header:
                print('import numpy as np')
        
        variable = self.FilterType_CB.currentText().replace('Filter', '')
        List.append(self.LE_to_List(self.Start_LE, False)[0])
        List.append(self.LE_to_List(self.End_LE, False)[0]) 

        if 'pi' in List[0]:    
            Start = self.Replace_PI_N(List[0])
        else:   
            Start = List[0]
        
        if 'pi' in List[1]:    
            End = self.Replace_PI_N(List[1])
        else:   
            End = List[1]

        if eval(End) < eval(Start):
            Swapped = True
            Start, End = End, Start

        try:
            Start = float(Start)
        except:
            pass

        try:
            End = float(End)
        except:
            pass
        
        if self.End_Point_CB.isChecked():
            EndPoint = ', endpoint=True'
        else:
            EndPoint = ', endpoint=False'

        if self.Tallies_Tab.currentIndex() == 0:
            variable = f"np.linspace({Start}, {End}, {self.GrpNumber_LE.text()}{EndPoint})"
            print(f"{self.FilterName_LE.text()} = openmc.{self.FilterType_CB.currentText()}({variable}{FILTER_ID})")
        else:
            print(f"groups = np.linspace({self.Start_LE_2.text()}, {self.End_LE_2.text()}, {self.GrpNumber_LE_2.text()}, endpoint=True)")
            print(f"{self.tally_name_list[-1]}.energy_groups = openmc.mgxs.EnergyGroups(groups)")

    def Create_Equal_Lethargy_Energy_Grid(self):
        List = []

        if self.Add_ID_Filter_Par_CB.isChecked():    
            FILTER_ID = ', filter_id=' + self.FilterId_LE.text()
        else:
            FILTER_ID = ''
        self.Find_string(self.plainTextEdit, "import numpy")
        
        if self.Insert_Header:
            self.Find_string(self.v_1, "import numpy")
            if self.Insert_Header:
                print('import numpy as np')
        
        List.append(self.LE_to_List(self.Start_LE, False)[0])
        List.append(self.LE_to_List(self.End_LE, False)[0]) 

        if List[1] < List[0]:
            Swapped = True
            List[0], List[1] = List[1], List[0]

        Start = float(List[0])
        End = float(List[1])

        if self.Tallies_Tab.currentIndex() == 0:
            variable = self.FilterType_CB.currentText().replace('Filter', '')
            #print(variable + ' = np.logspace(np.log10(' + str(Start) + '), np.log10(' + str(End) + '), ' + self.GrpNumber_LE.text() + ')')
            #print(self.FilterName_LE.text() + ' = openmc.' + self.FilterType_CB.currentText() + '(' + variable + FILTER_ID + ')')
            variable = f"np.logspace({Start}, {End}, {self.GrpNumber_LE.text()}, endpoint=True)"
            print(f"{self.FilterName_LE.text()} = openmc.{self.FilterType_CB.currentText()}({variable}{FILTER_ID})")

        else:
            print(f"groups = np.logspace(np.log10({self.Start_LE_2.text()}), np.log10({self.End_LE_2.text()}), {self.GrpNumber_LE_2.text()})")
            print(f"{self.tally_name_list[-1]}.energy_groups = openmc.mgxs.EnergyGroups(groups)")

    def MGX_GROUP_STRUCTURES(self):
        if self.Add_ID_Filter_Par_CB.isChecked():    
            FILTER_ID = ', filter_id=' + self.FilterId_LE.text()
        else:
            FILTER_ID = ''
        if self.Tallies_Tab.currentIndex() == 0:
            print(self.FilterName_LE.text() + ' = openmc.' + self.FilterType_CB.currentText() + "(openmc.mgxs.GROUP_STRUCTURES['" + self.MGX_CB.currentText() + "']" + FILTER_ID + ')')
        else:    
            print(f"groups = openmc.mgxs.GROUP_STRUCTURES['{self.MGX_CB_2.currentText()}']")
            print(f"{self.tally_name_list[-1]}.energy_groups = openmc.mgxs.EnergyGroups(groups)")  

    def Update_Filter_Bins(self):
        if self.Filter_Bins_CB.currentIndex() == 0:
            self.Filter_Bins_List_LE.setEnabled(False)
        else:
            self.Filter_Bins_List_LE.setEnabled(True)

        self.Filter_Bins_List_LE.clear()
        if self.FilterType_CB.currentIndex() in [1, 2, 3, 4, 5, 6, 8, 9, 10, 16]:
            self.Filter_Bins_List_LE.setValidator(None)
        elif self.FilterType_CB.currentIndex() == 7:        
            self.Filter_Bins_List_LE.setEnabled(True)
            self.Filter_Bins_List_LE.setValidator(UniversalNumericListValidator(
                schema=("pos_int",), max_items=None, allow_negative=False, allow_pi=False))
        elif self.FilterType_CB.currentIndex() in [11, 12]:   # EnergyFilter
            self.Filter_Bins_List_LE.setToolTip("")
            if self.Filter_Bins_CB.currentIndex() == 1:
                self.Filter_Bins_List_LE.setValidator(UniversalNumericListValidator(
                schema=("float",), max_items=None, allow_negative=False, allow_pi=False))
                self.Filter_Bins_List_LE.setToolTip("values (Iterable of Real) – A list of values for which each successive pair constitutes" \
                        "\na range of energies in [eV] for a single bin. Entries must be positive and ascending.")
            elif self.Filter_Bins_CB.currentIndex() in [3, 4]:
                self.Filter_Bins_List_LE.setEnabled(False)
                self.Filter_Bins_List_LE.setToolTip("")
                for LE in [self.Start_LE, self.End_LE]:
                    LE.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=1, allow_negative=False, allow_pi=False))
                self.Start_LE.setToolTip("Energy/Lethargy range lower bound")
                self.End_LE.setToolTip("Energy/Lethargy range upper bound")
            elif self.Filter_Bins_CB.currentIndex() == 5:    
                self.Filter_Bins_List_LE.setToolTip("group_structure (str) – Name of the group structure. /" \
                        "\nMust be a valid key of openmc.mgxs.GROUP_STRUCTURES dictionary.")
                self.Filter_Bins_List_LE.setValidator(None)
            else:
                self.Filter_Bins_List_LE.setValidator(None)
        elif self.FilterType_CB.currentIndex() == 13:      #  MuFilter
            if self.Filter_Bins_CB.currentIndex() == 1:
                self.Filter_Bins_List_LE.setToolTip("values (int or Iterable of Real) – A grid of scattering angles which events will binned into. " \
                "\nValues represent the cosine of the scattering angle. If an iterable is given, the values will be used explicitly " \
                "\nas grid points. If a single int is given, the range [-1, 1] will be divided up equally into that number of bins.")
                self.Filter_Bins_List_LE.setValidator(UniversalNumericListValidator(
                schema=("float",), max_items=None, allow_negative=True, allow_pi=False))
            elif self.Filter_Bins_CB.currentIndex() == 3:
                self.Filter_Bins_List_LE.setEnabled(False)
                self.Filter_Bins_List_LE.setToolTip("")
                for LE in [self.Start_LE, self.End_LE]:
                    LE.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=1, allow_negative=True, allow_pi=False))
                self.Start_LE.setToolTip("Cosine of the scattering angle range lower bound")
                self.End_LE.setToolTip("Cosine of the scattering angle range upper bound")
            else:
                self.Filter_Bins_List_LE.setValidator(None)
        elif self.FilterType_CB.currentIndex() == 14:     # polarFilter
            if self.Filter_Bins_CB.currentIndex() == 1:
                self.Filter_Bins_List_LE.setToolTip("values (int or Iterable of Real) – A grid of polar angles which events will binned into." \
                                                    "\nValues represent an angle in radians relative to the z-axis. If an iterable is given, "\
                                                    "\nthe values will be used explicitly as grid points. If a single int is given, the range [0, pi] "\
                                                    "\nwill be divided up equally into that number of bins.")
                self.Filter_Bins_List_LE.setValidator(UniversalNumericListValidator(
                schema=("float",), max_items=None, allow_negative=False, allow_pi=True))
            elif self.Filter_Bins_CB.currentIndex() == 3:
                self.Filter_Bins_List_LE.setEnabled(False)
                self.Filter_Bins_List_LE.setToolTip("")
                for LE in [self.Start_LE, self.End_LE]:
                    LE.setValidator(UniversalNumericListValidator(
                        schema=("float",), max_items=1, allow_negative=False, allow_pi=True))
                self.Start_LE.setToolTip("Polar angle range lower bound")
                self.End_LE.setToolTip("Polar angle range upper bound")
            else:
                self.Filter_Bins_List_LE.setToolTip("")
                self.Filter_Bins_List_LE.setValidator(None)
        elif self.FilterType_CB.currentIndex() == 15:      # azimutalFilter
            if self.Filter_Bins_CB.currentIndex() == 1:
                self.Filter_Bins_List_LE.setToolTip("values (int or Iterable of Real) – A grid of azimuthal angles "\
                                                    "\nwhich events will binned into. Values represent an angle in radians "\
                                                    "\nrelative to the x-axis and perpendicular to the z-axis. If an iterable "\
                                                    "\nis given, the values will be used explicitly as grid points. If a single "\
                                                    "\nint is given, the range [-pi, pi) will be divided up equally into that number of bins.")
                self.Filter_Bins_List_LE.setValidator(UniversalNumericListValidator(
                schema=("float",), max_items=None, allow_negative=True, allow_pi=True))
            elif self.Filter_Bins_CB.currentIndex() == 3:
                self.Filter_Bins_List_LE.setEnabled(False)
                self.Filter_Bins_List_LE.setToolTip("")
                for LE in [self.Start_LE, self.End_LE]:
                    LE.setValidator(UniversalNumericListValidator(
                        schema=("float",), max_items=1, allow_negative=True, allow_pi=True))
            else:
                self.Filter_Bins_List_LE.setValidator(None)
        elif self.FilterType_CB.currentIndex() == 18:   # EnergyFunctionFilter
            for LE in [self.Start_LE, self.End_LE]:
                LE.setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=None, allow_negative=False, allow_pi=False))

        if self.FilterType_CB.currentIndex() not in [6, 9, 11, 12, 13, 14, 15, 16]:
            if self.Filter_Bins_CB.currentIndex() not in [0, 1] and self.Filter_Bins_CB.currentText() not in self.Filter_Bins_List:
                self.Filter_Bins_List.append(self.Filter_Bins_CB.currentText())
            
            if self.Filter_Bins_CB.currentIndex() == 0:
                pass
            elif self.Filter_Bins_CB.currentIndex() == 1:
                self.Use_AllItems = True
                self.Filter_Bins_List = [self.Filter_Bins_CB.itemText(i) for i in range(self.Filter_Bins_CB.count())][2:]
                self.Filter_Bins_List_LE.setText(str(self.Filter_Bins_List))
            else:
                if self.Use_AllItems:
                    self.Filter_Bins_List_LE.clear()
                    self.Use_AllItems = False
                self.Filter_Bins_List_LE.setText(str(self.Filter_Bins_List))
        elif self.FilterType_CB.currentIndex() in [11, 12, 13, 14, 15]:
            if self.Filter_Bins_CB.currentIndex() == 2:
                self.Import_Grid_List(self.Filter_Bins_List_LE)
            elif self.Filter_Bins_CB.currentIndex() == 5:
                self.MGX_CB.clear()
                self.MGX_CB.addItems(self.MGX_GROUP_STRUCTURES_LIST)
        else:
            if self.Filter_Bins_CB.currentIndex() != 0 and self.Filter_Bins_CB.currentText() not in self.Filter_Bins_List:
                self.Filter_Bins_List.append(self.Filter_Bins_CB.currentText())
                self.Filter_Bins_List_LE.setText(str(self.Filter_Bins_List))


        if self.FilterType_CB.currentIndex() == 0:
            self.Filter_Bins_List_LE.clear()
        
    def Choose_MGX_STR(self):
        if self.MGX_CB.currentIndex() != 0:
            self.Filter_Bins_List_LE.clear()
            self.Filter_Bins_List_LE.setText(self.MGX_CB.currentText())

    def Choose_MGX_STR_2(self):
        if self.MGX_CB_2.currentIndex() != 0:
            self.Filter_Bins_List_LE_2.clear()
            self.Filter_Bins_List_LE_2.setText(self.MGX_CB_2.currentText())

    def Show_Hide_Widgets_MGXS(self):
        Widgets = [self.label_16, self.label_17, self.label_15, self.Start_LE_2, self.End_LE_2, self.GrpNumber_LE_2]
        self.Filter_Bins_List_LE_2.clear()
        self.Start_LE_2.clear()
        self.End_LE_2.clear()
        self.GrpNumber_LE_2.clear()
        if self.Filter_Bins_CB_2.currentIndex() in [0, 1]:
            for item in Widgets:
                item.hide()
            self.MGX_CB_2.hide()
            self.Filter_Bins_List_LE_2.setValidator(self.float_validator_list_positif)
        elif self.Filter_Bins_CB_2.currentIndex() in [2, 3]:
            for item in Widgets:
                item.show()
            self.MGX_CB_2.hide()
            self.Filter_Bins_List_LE_2.setValidator(None)
        elif self.Filter_Bins_CB_2.currentIndex() == 4:
            self.MGX_CB_2.show()
            self.Filter_Bins_List_LE_2.setValidator(None)
            for item in Widgets:
                item.hide()

    def Show_Hide_Widgets(self):
        Ws = [self.label, self.label_8, self.label_10, self.Start_LE, self.End_LE, self.GrpNumber_LE, self.End_Point_CB]
        self.Filter_Bins_List_LE.show()
        self.Filter_Bins_List_LE.clear()
        
        if self.FilterType_CB.currentIndex() in [11, 12]:
            if self.Filter_Bins_CB.currentIndex() == 5:
                self.MGX_CB.show()
            else:
                self.MGX_CB.hide()
        elif self.FilterType_CB.currentIndex() == 20:
            self.MGX_CB.show()
        else:
            self.MGX_CB.hide()

        if self.FilterType_CB.currentIndex() in [18, 19, 20, 21, 22, 23]:
            self.Filter_Bins_CB.setEnabled(False)
            for item in [self.label, self.label_8, self.label_10, self.Start_LE, self.End_LE, self.GrpNumber_LE]:
                item.show()
                item.setEnabled(True)
        elif self.FilterType_CB.currentIndex() in [11, 12, 13, 14, 15]:
            self.Filter_Bins_CB.setEnabled(True)
            if self.Filter_Bins_CB.currentIndex() in [3, 4]:
                for item in Ws:
                    item.show()
                    item.setEnabled(True)
            else:
                for item in Ws:
                    item.hide()
        else:
            for item in Ws:
                item.hide()
            if self.FilterType_CB.currentIndex() in [7, 25]:  
                self.Filter_Bins_CB.setEnabled(False)
            else:
                self.Filter_Bins_CB.setEnabled(True)

        if self.FilterType_CB.currentIndex() in [11, 12, 13, 14, 15]:   # Energy, mu, polar, azimutal
            self.label_8.setText('Start Value')
            self.label_10.setText('End Value')
            self.label.setText('Groups number')
            """if self.Filter_Bins_CB.currentIndex() in [3, 4]:
                self.Start_LE.setValidator(self.validator)
                self.End_LE.setValidator(self.validator)
                for LE in [self.Start_LE, self.End_LE]:
                    LE.setValidator(setValidator(UniversalNumericListValidator(
                    schema=("float",), max_items=1, allow_negative=False, allow_pi=False)))"""
        elif self.FilterType_CB.currentIndex() == 17:   # DelayedGroup
            self.Filter_Bins_CB.setEnabled(True)
        elif self.FilterType_CB.currentIndex() == 18:    # EnergyFunction
            for item in [self.label_8, self.label_10, self.Start_LE, self.End_LE]:
                item.setEnabled(True)
            self.label_8.setText('Energy values in [eV]')
            self.label_10.setText('Interpolant values y in [eV]')
            """for LineEd in [self.Start_LE, self.End_LE]:
                LineEd.setValidator(self.float_validator_list)"""
            self.Start_LE.setToolTip("energy (Iterable of Real) – A grid of energy values in [eV]")
            self.End_LE.setToolTip("y (iterable of Real) – A grid of interpolant values in [eV]")
            self.comboBox.setToolTip("interpolation (str) – Interpolation scheme: {‘histogram’, "\
                                    "\n‘linear-linear’, ‘linear-log’, ‘log-linear’, ‘log-log’, ‘quadratic’, ‘cubic’}")
        elif self.FilterType_CB.currentIndex() in [19, 21]:  # Legendre SpatialLegendre
            for item in [self.label, self.GrpNumber_LE]:
                item.setEnabled(True)
            for item in [self.label_8, self.label_10, self.Start_LE, self.End_LE]:
                item.setEnabled(False)
            if self.FilterType_CB.currentIndex() == 19:   # Legendre
                self.label.setText('Legend order')
            elif self.FilterType_CB.currentIndex() == 21:   # SphericalHarmonics
                self.label.setText('Spherical Harmonics order')
            self.GrpNumber_LE.setValidator(self.int_validator)
            self.Start_LE.setToolTip("")
            self.End_LE.setToolTip("")
        elif self.FilterType_CB.currentIndex() == 20:    # SpatialLegendre
            for item in Ws:
                item.setEnabled(True)
            self.MGX_CB.clear()
            self.MGX_CB.addItems(['Select axis', 'x', 'y', 'z'])
            """self.GrpNumber_LE.setValidator(self.int_validator)
            self.Start_LE.setValidator(self.validator)
            self.End_LE.setValidator(self.validator)"""
        elif self.FilterType_CB.currentIndex() in [22, 23]:   # Zernike
            self.label_8.setText('x')
            self.label_10.setText('y')
            self.label.setText('radius')
            for item in [self.label_8, self.label_10, self.Start_LE, self.End_LE, self.GrpNumber_LE]:
                item.setEnabled(True)
            self.Filter_Bins_List_LE.setValidator(self.int_validator)
            #self.GrpNumber_LE.setValidator(QDoubleValidator(self))
        
        if self.FilterType_CB.currentIndex() in [22, 23]:
            self.label_7.setText('Zernike polynomials order')
        else:
            self.label_7.setText('Filter Bins')
            self.Filter_Bins_List_LE.setValidator(None)

    def Show_Hide_Widgets_1(self):
        if self.MGX_CB.currentIndex() == 0:
            self.label_8.setText('min')
            self.label_10.setText('max')
            self.label.setText('Legend order')
        else:
            self.label_8.setText(self.MGX_CB.currentText() + 'min')
            self.label_10.setText(self.MGX_CB.currentText() + 'max')
            self.label.setText('Legend order')


    def Add_Nuclides_Bins_To_Tally(self):
        if self.Nuclides_CB.currentIndex() not in [0, 1] and self.Nuclides_CB.currentText() not in self.Nuclides_Bins_List:
            self.Nuclides_Bins_List.append(self.Nuclides_CB.currentText())
        if self.Nuclides_CB.currentIndex() == 0:
            pass
        elif self.Nuclides_CB.currentIndex() == 1:
            self.Use_AllItems = True
            AllItems = [self.Nuclides_CB.itemText(i) for i in range(self.Nuclides_CB.count())][2:]
            self.Nuclides_Bins_List = AllItems
            self.Nuclides_Bins_List_LE.setText(str(self.Nuclides_Bins_List))
        else:
            if self.Use_AllItems:
                self.Nuclides_Bins_List_LE.clear()
                self.Use_AllItems = False
            self.Nuclides_Bins_List_LE.setText(str(self.Nuclides_Bins_List))
        self.Nuclides_CB.setCurrentIndex(0)

    def Def_Filters_Bins_To_Tally(self):
        if self.Filters_List_CB.currentIndex() not in [0, 1] and self.Filters_List_CB.currentText() not in self.Filters_List:
            self.Filters_List.append(self.Filters_List_CB.currentText())
        if self.Filters_List_CB.currentIndex() == 0:
            pass
        elif self.Filters_List_CB.currentIndex() == 1:
            self.Use_AllItems = True
            AllItems = [self.Filters_List_CB.itemText(i) for i in range(self.Filters_List_CB.count())][2:]
            self.Filters_List = AllItems
            self.Filters_List_LE.setText(str(self.Filters_List))
        else:
            if self.Use_AllItems:
                self.Filters_List_LE.clear()
                self.Use_AllItems = False
            self.Filters_List_LE.setText(str(self.Filters_List))
        self.Filters_List_CB.setCurrentIndex(0)

    def Add_Filters_Bins_To_Tally(self):
        if self.Filters_List_LE.text():
            if not self.Create_New_Tally and self.tally_name_list:
                qm = QMessageBox
                ret = qm.question(self, 'Warning', 'No new tally created. Tally ' + self.tally_name_list[-1] +  ' will be modified! proceed?', qm.Yes | qm.No)
                if ret == qm.No:
                    return

            if self.tally_name_list:
                text = self.tally_name_list[-1] + ".filters"
                if text in self.plainTextEdit.toPlainText(): self.Update_Document(text)
                print('\n' + text + ' = ' + self.Filters_List_LE.text().replace("'", ""))
                text = self.Tallies + '.append(' + self.tally_name_list[-1] + ')'
                if text in self.plainTextEdit.toPlainText(): self.Update_Document(text)
                print('\n' + text)
            else:
                self.showDialog('Warning', 'Add tally first !')
        else:
            self.showDialog('Warning', 'Choose filters to add first !')
            return
        self.Filters_List_CB.setCurrentIndex(0)
        self.Filters_List_LE.clear()
        #self.Reset(self.Filters_List, self.Filters_List_LE)

    def LE_to_List1(self, LineEdit):
        List = []
        text = LineEdit.text().replace('(', '').replace(')', '')
        for separator in [',', ';', ':', ' ']:
            if separator in text:
                text = str(' '.join(text.replace(separator, ' ').split()))
        List = text.split()
        return List
    
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
        return e   #re.sub(r'["\']', '', e)

    def LE_to_List(self, LineEdit1, Sorting):
        text1 = LineEdit1.text().replace('np.', '')
        if '[' in text1 and ']' in text1:
            text1 = text1.strip('[]')   
        else:
            text1 = text1.replace('[', '').replace(']', '')

        for separator in [',', ';', ':', ' ']:
            if separator in text1:
                text1 = str(' '.join(text1.replace(separator, ' ').split()))

        List1 = self.parse_list(text1)
       
        if Sorting:
            # Sort with the fixed parser
            x_sorted = sorted(List1, key=lambda pair: self.parse_pi_expression(pair))
        else:
            x_sorted = [x for x in List1]

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
        x_sorted = [re.sub(r'pi', 'np.pi', e) if 'pi' in e else e for e in x_sorted]

        return x_sorted

    def Add_Nuclides(self):
        if self.Nuclides_Bins_List_LE.text() == '':
            self.showDialog('Warning', 'No Nuclide selected !')
            return
        if not self.Create_New_Tally and self.tally_name_list:
            qm = QMessageBox
            ret = qm.question(self, 'Warning', 'No new tally created. Tally ' + self.tally_name_list[-1] +  ' will be modified! proceed?', qm.Yes | qm.No)
            if ret == qm.No:
                return

        Nuclides = self.Nuclides_Bins_List_LE.text()
        nuclides_list = Nuclides[Nuclides.find("[") + 1: Nuclides.find("]")].replace("'","").replace(" ","").split(',')
        
        if self.tally_name_list:
            text = self.tally_name_list[-1] + '.nuclides'
            if text in self.plainTextEdit.toPlainText(): self.Update_Document(text)
            for item in nuclides_list:
                if item not in self.Model_Nuclides_List:
                    self.showDialog('Warning', item + ' not in list of nuclides in the model!')
                    return
            print('\n' + text + ' = ' + Nuclides)
            text = self.Tallies + '.append(' + self.tally_name_list[-1] + ')'
            if text in self.plainTextEdit.toPlainText(): self.Update_Document(text)
            print('\n' + text)
            self.Nuclides_Bins_List_LE.clear()
        else:
            self.showDialog('Warning', 'Add tally first !')
            return
        #self.Reset(self.Nuclides_Bins_List, self.Nuclides_Bins_List_LE)

    def Add_Scores(self):
        if self.MGXS_Lib_CB.isChecked():
            self.Add_MGXS()
            return
        if self.ScoresList_LE.text() == '':
            self.showDialog('Warning', 'No score to add !')
            return
        if not self.Create_New_Tally and self.tally_name_list:
            qm = QMessageBox
            ret = qm.question(self, 'Warning', 'No new tally created. Tally ' + self.tally_name_list[-1] +  ' will be modified! proceed?', qm.Yes | qm.No)
            if ret == qm.No:
                return

        scores = self.ScoresList_LE.text()
        if self.tally_name_list:
            text = self.tally_name_list[-1] + '.scores = '
            if text in self.plainTextEdit.toPlainText(): self.Update_Document(text)
            print('\n' + text + scores )
            if self.Estimator_CB.currentIndex()!= 0:
                print(self.tally_name_list[-1] + '.estimator = ' + "'" + str(self.Estimator_CB.currentText() + "'"))
            text = self.Tallies + '.append(' + self.tally_name_list[-1] + ')'
            if text in self.plainTextEdit.toPlainText(): self.Update_Document(text)
            print('\n' + text)
            self.ScoresList_LE.clear()
            self.FluxScores_CB.setCurrentIndex(0)
            self.RxnRates_CB.setCurrentIndex(0)
            self.PartProduction_CB.setCurrentIndex(0)
            self.MiscScores_CB.setCurrentIndex(0)
        else:
            self.showDialog('Warning', 'Add tally first !')
            return
        self.Trigger_Scores_comboBox.clear()
        self.Trigger_Scores_comboBox.addItem('Check scores')
        self.Scores_List.insert(0, 'All')
        self.Trigger_Scores_comboBox.addItems(self.Scores_List)
        self.Trigger_Scores_comboBox.model().item(0).setEnabled(False)

    def Add_MGXS(self):
        if self.ScoresList_LE.text() == '':
            self.showDialog('Warning', 'No score to add !')
            return
        if self.Domain_type_CB.currentIndex() == 0:
            self.showDialog('Warning', 'Select domain type !')
            return
        if self.Filter_Bins_CB_2.currentIndex() == 0:
            self.showDialog('Warning', 'Select energy groups structure !')
            return
                
        if self.Filter_Bins_CB_2.currentIndex() == 1:     # enter data list
            if self.Filter_Bins_List_LE_2.text() == '':   
                self.showDialog('Warning', 'Enter energy groups edges !')
                return
            
            List = self.LE_to_List(self.Filter_Bins_List_LE_2, True)
            if len(List) < 2:
                self.showDialog('Warning', 'At least 2 edges are needed !')
                return
            groups = [float(E) for E in List]
            print(f"groups = {groups}")
            print(f"{self.tally_name_list[-1]}.energy_groups = openmc.mgxs.EnergyGroups(groups)")
        elif self.Filter_Bins_CB_2.currentIndex() in [2, 3]:    # start energy, end energy and groups number
            if self.Start_LE_2.text() == '' or self.End_LE_2.text() == '' or self.GrpNumber_LE_2.text() == '':
                self.showDialog('Warning', 'Three fields must be filled !')
                return
            if float(self.Start_LE_2.text()) >= float(self.End_LE_2.text()):
                self.showDialog('Warning', 'Start energy must be lower than End energy !')
                return
            if float(self.GrpNumber_LE_2.text()) == 0:
                self.showDialog('Warning', 'Number of energy groups must be non null !')
                return
            if self.Filter_Bins_CB_2.currentIndex() == 2:
                self.Create_Equal_Step_Grid()
            else:
                self.Create_Equal_Lethargy_Energy_Grid()
        elif self.Filter_Bins_CB_2.currentIndex() == 4:     # MGXS groups structure
            if self.MGX_CB_2.currentIndex() == 0:
                self.showDialog('Warning', 'Select energy groups structure !')
                return
            self.MGX_GROUP_STRUCTURES()
        print(f"{self.tally_name_list[-1]}.domain_type = '{self.Domain_type_CB.currentText()}'")
        print(f"{self.tally_name_list[-1]}.mgxs_types = {self.ScoresList_LE.text()}")

        if self.Nu_CB.isChecked():
            pass
        else:
            pass

        if self.By_Nuclides_CB.isChecked():
            print(f"{self.tally_name_list[-1]}.by_nuclide = True")
        else:
            print(f"{self.tally_name_list[-1]}.by_nuclide = False")
        print(f"{self.tally_name_list[-1]}.build_library()")
        print(f"{self.tally_name_list[-1]}.add_to_tallies_file({self.Tallies})")

        self.ScoresList_LE.clear()
        self.Filter_Bins_List_LE_2.clear()
        self.Start_LE_2.clear()
        self.End_LE_2.clear()
        self.GrpNumber_LE_2.clear()
        self.GrpNumber_LE_2.clear()
        self.MG_Matrix_XS_CB.setCurrentIndex(0)
        self.Filter_Bins_CB_2.setCurrentIndex(0)
        self.MGX_CB_2.setCurrentIndex(0)
        self.Domain_type_CB.setCurrentIndex(0)
        self.Nu_CB.setChecked(False)
        self.By_Nuclides_CB.setChecked(False)
        # Button is disabled before creating new tally
        self.AddScore_PB.setEnabled(False)


    def Add_Trigger(self):
        if self.Tally_Trigger_Threshold_LE.text() == '':
            self.showDialog('Warning', ' Enter Trigger threshold value!')
            return
        if self.Tally_Trigger_Type.currentIndex() == 0:
            self.showDialog('Warning', ' Select Trigger type first!')
            return
        if self.Trigger_Scores_comboBox.checkedItems():
            self.Checked_Scores = [self.Scores_List[i-1] for i in self.Trigger_Scores_comboBox.checkedItems()]
        else: 
            self.Checked_Scores = []
        if 'All' in self.Checked_Scores:
            self.Checked_Scores = ['all']

        if self.Ignore_Zeroes_CB.isChecked():
            Ignore_Zeros = ', ignore_zeros=True'
        else:
            Ignore_Zeros = ''
        
        Type = 'trigger_type=' + self.Tally_Trigger_Type.currentText()
        Threshold = ', threshold=' + self.Tally_Trigger_Threshold_LE.text()
        Trigger = 'tally_trigger = openmc.Trigger(' + Type + Threshold + Ignore_Zeros +')'
        Scores = 'tally_trigger.scores = ' + str(self.Checked_Scores)
        text1 = self.tally_name_list[-1] + '.triggers = [tally_trigger]'
        if text1 in self.plainTextEdit.toPlainText(): self.Update_Document(text1)
        print('\n' + Trigger + '\n' + Scores + '\n' + text1 )
        self.Trigger_Scores_comboBox.setCurrentIndex(0)

    def Update_Document(self, text):
        document = self.plainTextEdit.toPlainText()
        lines = document.splitlines()
        for line in lines:
            if (text in line):
                lines.remove(line)
                document = self.plainTextEdit.toPlainText().replace(line,"")
        self.plainTextEdit.clear()
        self.plainTextEdit.insertPlainText(document)

        lines = document.splitlines()
        self.plainTextEdit.clear()
        doc = [x for x in lines if x.strip() != ""]   # reduces empty lines to ''
        self.plainTextEdit.insertPlainText('\n'.join(doc))

    def DEF_FluxScores(self):
        self.Use_AllItems = False
        if self.FluxScores_CB.currentText() not in self.Scores_List:
            if self.FluxScores_CB.currentIndex() != 0:
                self.Scores_List.append(self.FluxScores_CB.currentText())
            self.Update_Scores_LE()

    def DEF_RxnRates(self):
        self.Use_AllItems = False
        if self.RxnRates_CB.currentText() not in self.Scores_List:
            if self.RxnRates_CB.currentIndex() != 0:
                self.Scores_List.append(self.RxnRates_CB.currentText())
            self.Update_Scores_LE()

    def DEF_PartProduction(self):
        self.Use_AllItems = False
        if self.PartProduction_CB.currentText() not in self.Scores_List:
            if self.PartProduction_CB.currentIndex() != 0:
                self.Scores_List.append(self.PartProduction_CB.currentText())
            self.Update_Scores_LE()

    def DEF_MiscScores(self):
        self.Use_AllItems = False
        if self.MiscScores_CB.currentText() not in self.Scores_List:
            if self.MiscScores_CB.currentIndex() != 0:
                self.Scores_List.append(self.MiscScores_CB.currentText())
            self.Update_Scores_LE()

    def DEF_MGXS_Scores(self):
        self.Use_AllItems = False
        if self.MGXS_Scores_CB.currentText() not in self.Scores_List:
            if self.MGXS_Scores_CB.currentIndex() != 0:
                self.Scores_List.append(self.MGXS_Scores_CB.currentText())
            self.Update_Scores_LE()

    def DEF_MGXS_XS_Matrix(self):
        self.Use_AllItems = False
        if self.MG_Matrix_XS_CB.currentText() not in self.Scores_List:
            if self.MG_Matrix_XS_CB.currentIndex() != 0:
                self.Scores_List.append(self.MG_Matrix_XS_CB.currentText())
            self.Update_Scores_LE()

    def DEF_MGXS_XS_Levels(self):
        self.Use_AllItems = False
        if self.MG_Levels_XS_CB.currentText() not in self.Scores_List:
            if self.MG_Levels_XS_CB.currentIndex() != 0:
                self.Scores_List.append(self.MG_Levels_XS_CB.currentText())
            self.Update_Scores_LE()
    
    def activate_MGXS_Scores_CB(self):
        CBS = [self.MGXS_Scores_CB, self.MG_Matrix_XS_CB, self.MG_Levels_XS_CB, self.Domain_type_CB, self.Nu_CB, self.By_Nuclides_CB]
        Widgets = [self.Add_id_to_tally_def_CB, self.TallyName_LE, self.label_12]
        if self.MGXS_Lib_CB.isChecked():
            self.groupBox_5.hide()
            self.groupBox_6.hide()
            self.groupBox.hide()
            self.groupBox_2.hide()
            self.Tally_Trigger_GB.hide()
            self.groupBox_7.hide()
            self.groupBox_8.show()
            self.tally_suffix = 'lib'
            """if self.AddTallyId_CB.isChecked():
                Tally_str = self.tally_suffix + self.TallyId_LE.text()
            else:
                Tally_str = self.tally_suffix"""
            self.AddScore_PB.setText('Add Lib')
            self.AddTally_PB.setText('Create Lib')
            for W in Widgets:
                W.setEnabled(False)
            for CB in CBS:
                CB.setEnabled(True)
        else:
            self.tally_suffix = '_tally'
            self.groupBox_5.show()
            self.groupBox_6.show()
            self.groupBox.show()
            self.groupBox_2.show()
            self.Tally_Trigger_GB.show()
            self.groupBox_7.show()
            self.groupBox_8.hide()
            self.AddScore_PB.setText('Add Scores')
            self.AddTally_PB.setText('Create Tally')
            for W in Widgets:
                W.setEnabled(True)
            for CB in CBS:
                CB.setEnabled(False)

        if self.AddTallyId_CB.isChecked():
            Tally_str = self.tally_suffix + self.TallyId_LE.text()
        else:
            Tally_str = self.tally_suffix
        self.Tally_LE.setText(Tally_str)

    def Update_Scores_LE(self):
        self.ScoresList_LE.clear()
        self.ScoresList_LE.setText(str(self.Scores_List))
        self.FluxScores_CB.setCurrentIndex(0)
        self.RxnRates_CB.setCurrentIndex(0)
        self.PartProduction_CB.setCurrentIndex(0)
        self.MiscScores_CB.setCurrentIndex(0)
        self.MGXS_Scores_CB.setCurrentIndex(0)
        self.MG_Matrix_XS_CB.setCurrentIndex(0)
        self.MG_Levels_XS_CB.setCurrentIndex(0)

    def Find_Tallies(self):
        self.Find_Filters()
        self.Find_Scores()
        self.Store_Tallies_Info(self.Tally, self.Tally_ID)

    def Store_Tallies_Info(self, Tally, Tally_Id):
        # new dictionary filling : parent
        self.Tallies_In_Model[Tally] = {}
        self.Tallies_In_Model[Tally]['id'] = Tally_Id
        self.Tallies_In_Model[Tally]['name'] = Tally
        self.Tallies_In_Model[Tally]['title'] = self.TallyName

    def Def_Tallies(self):
        self.Find_string(self.plainTextEdit, "import openmc")
        if self.Insert_Header:
            self.Find_string(self.v_1, "import openmc")
            if self.Insert_Header:
                cursor = self.v_1.textCursor()
                cursor.movePosition(QTextCursor.Start)
                cursor.insertText('import openmc\n')

        self.Find_string(self.v_1, "openmc.Tallies")
        if self.Insert_Header:
            self.Find_string(self.plainTextEdit, "openmc.Tallies")
            if self.Insert_Header:
                print('\n###############################################################################\n'
                        '#                 Exporting to OpenMC tallies.xml file \n'
                        '###############################################################################')
                print(self.Tallies + " = openmc.Tallies()\n")
            else:
                pass

    def Export_to_Main_Window(self):
        if not self.MGXS_Lib_CB.isChecked():
            try:
                if self.Tallies_Tab.currentIndex() == 1 and self.tally_name_list[-1] + '.scores' not in self.plainTextEdit.toPlainText():
                    self.showDialog('Warning', 'will not create XML for Tally ID=' + self.tally_id_list[-1] + ' since it does not contain any score')
                    return
            except:
                if not self.MGXS_Lib_CB.isChecked():
                    self.showDialog('Warning', 'Some thing went wrong in tallies list!')
                    return
                else:
                    pass
        if 'import numpy' in self.plainTextEdit.toPlainText():
            self.Suppress_Line('import numpy', self.plainTextEdit)
        
        self.v_1.moveCursor(QTextCursor.End)
        string_to_find = self.Tallies + ".export_to_xml()"
        self.Find_string(self.v_1, string_to_find)
        cursor = self.v_1.textCursor()
        self.plainTextEdit.moveCursor(QTextCursor.End)
        if self.Insert_Header:
            if self.Tallies_Tab.currentIndex() == 1:
                print('\n' + string_to_find)
            cursor.insertText(self.plainTextEdit.toPlainText())
        else:
            print('\n' + string_to_find)
            document = self.v_1.toPlainText().replace(string_to_find, self.plainTextEdit.toPlainText())
            self.v_1.clear()
            cursor = self.v_1.textCursor()
            cursor.insertText(document)
            self.text_inserted = True
            #self.plainTextEdit.clear()
            self.Create_New_Tally = False
        
        document = self.v_1.toPlainText()
        document = self.Move_Commands_to_End(document)
        cursor = self.v_1.textCursor()
        self.v_1.clear()
        cursor.insertText(document)
        self.plainTextEdit.clear()

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
                
    def Find_string(self, text_window, string_to_find):
        self.list_of_items = []
        self.current_line = ''
        self.line_number = 0
        self.Insert_Header = True
        document = text_window.toPlainText()
        for line in document.split('\n'):
            self.line_number += 1
            if string_to_find in line:
                self.current_line = line
                self.list_of_items.append(line[0:len(line) -1])
                self.Insert_Header = False

    def Undo(self, List, LineEdit):
        if len(List) == 0 and len(LineEdit.text()) != 0:
            List = self.LE_to_List(LineEdit, False)
        if List:
            if self.Use_AllItems:
                List.clear()
                LineEdit.clear()
            else:
                List.pop()
            LineEdit.setText(str(List).replace('[', '').replace(']', ''))
            if not List:
                LineEdit.clear()
            return List
        self.Use_AllItems = False

    def Reset(self, List, LineEdit):
        List.clear()
        LineEdit.clear()
        return List
        self.Use_AllItems = False

    def clear_text(self, text):
        if text != "\n":
            if self.text_inserted:
                self.plainTextEdit.clear()
            else:
                qm = QMessageBox
                ret = qm.question(self, 'Warning', 'Do you really want to clear data ?', qm.Yes | qm.No)
                if ret == qm.Yes:
                    self.plainTextEdit.clear()
                elif ret == qm.No:
                    pass

    def normalOutputWritten(self,text):
        self.highlighter = Highlighter(self.plainTextEdit.document())
        cursor = self.plainTextEdit.textCursor()
        cursor.insertText(text)

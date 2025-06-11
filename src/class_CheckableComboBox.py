import PyQt5
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *

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
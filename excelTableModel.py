from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt5.QtGui import QColor


class CustomTableModel(QAbstractTableModel):
    def __init__(self, data=None):
        QAbstractTableModel.__init__(self)
        self.load_data(data)

    def load_data(self, data):
        self.data= data

        self.column_count = 6
        self.row_count = len(self.data['questions'])

    def rowCount(self, parent=QModelIndex()):
        return self.row_count

    def columnCount(self, parent=QModelIndex()):
        return self.column_count

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return ("question","prop1","prop2","prop3","prop4","correct")[section]
        else:
            return "{}".format(section)

    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        
        if role == Qt.DisplayRole:
            if column == 0:                
                return self.data['questions'][row]
            elif column == 1:
                return self.data['prop1'][row]
            elif column == 2:
                return self.data['prop2'][row]
            elif column == 3:
                return self.data['prop3'][row]
            elif column == 4:
                return self.data['prop4'][row]
            elif column == 5:
                return str(self.data['correct'][row])
        elif role == Qt.BackgroundRole:
            return QColor(Qt.white)
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignRight

        return None
    
    def setData(self, index, value, role):
        if role == Qt.EditRole:
            if index.column() == 0:
                self.data['questions'][index.row()] = value
            elif index.column() == 1:
                self.data['prop1'][index.row()] = value
            elif index.column() == 2:
                self.data['prop2'][index.row()] = value
            elif index.column() == 3:
                self.data['prop3'][index.row()] = value
            elif index.column() == 4:
                self.data['prop1'][index.row()] = value
            elif index.column() == 5:
                self.data['correct'][index.row()] = value
            return True

    def flags(self, index):
        return Qt.ItemIsSelectable|Qt.ItemIsEnabled|Qt.ItemIsEditable
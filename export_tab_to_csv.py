# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ExportTabToCSV
                                 A QGIS plugin
 Esporta la tabella del layer vettoriale selezionato su un file CSV
 ***************************************************************************/ 
"""

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QFileDialog
from qgis.core import QgsProject, Qgis
from .resources import *
from .export_tab_to_csv_dialog import ExportTabToCSVDialog
import os.path

class ExportTabToCSV:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor."""
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'ExportTabToCSV_{}.qm'.format(locale))
        
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        self.actions = []
        self.menu = self.tr(u'&Esporta Tab su file CSV')
        self.first_start = None

    def tr(self, message):
        """Get the translation for a string using Qt translation API."""
        return QCoreApplication.translate('ExportTabToCSV', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):

        icon_path = f'{self.plugin_dir}/icon.png'
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(self.menu, action)

        self.actions.append(action)
        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        icon_path = ':/plugins/export_tab_to_csv/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Esporta Tab in file CSV'),
            callback=self.run,
            parent=self.iface.mainWindow())
        self.first_start = True

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginVectorMenu(self.tr(u'&Esporta Tab su file CSV'), action)
            self.iface.removeToolBarIcon(action)

    def select_output_file(self):
        filename, _filter = QFileDialog.getSaveFileName(self.dlg, "Select output file", "", '*.csv')
        self.dlg.lineEdit.setText(filename)

    def run(self):
        """Run method that performs all the real work"""
        if self.first_start:
            self.first_start = False
            self.dlg = ExportTabToCSVDialog()
            self.dlg.pushButton.clicked.connect(self.select_output_file)
            self.dlg.cmbox_col.addItems([";", ","])
            self.dlg.cmbox_decim.addItems([",", "."])

            # Imposta progress bar per 0%
            self.dlg.progressBar.setValue(0)

            def update_combo_boxes():
                col_sep = self.dlg.cmbox_col.currentText()
                dec_sep = self.dlg.cmbox_decim.currentText()
                if col_sep == dec_sep:
                    if self.dlg.cmbox_col.hasFocus():
                        self.dlg.cmbox_decim.setCurrentIndex(1 if col_sep == "," else 0)
                    elif self.dlg.cmbox_decim.hasFocus():
                        self.dlg.cmbox_col.setCurrentIndex(1 if dec_sep == ";" else 0)

            self.dlg.cmbox_col.currentIndexChanged.connect(update_combo_boxes)
            self.dlg.cmbox_decim.currentIndexChanged.connect(update_combo_boxes)

        layers = QgsProject.instance().layerTreeRoot().children()
        self.dlg.cmbox_vector.clear()
        self.dlg.lineEdit.clear()
        self.dlg.cmbox_vector.addItems([layer.name() for layer in layers])

        self.dlg.show()
        result = self.dlg.exec_()

        if result:
            column_separator = self.dlg.cmbox_col.currentText()
            decimal_symbol = self.dlg.cmbox_decim.currentText()
            filename = self.dlg.lineEdit.text()

            selectedLayerIndex = self.dlg.cmbox_vector.currentIndex()
            selectedLayer = layers[selectedLayerIndex].layer()
            fieldnames = [field.name() for field in selectedLayer.fields()]

            with open(filename, 'w') as output_file:
                line = column_separator.join(fieldnames) + '\n'
                output_file.write(line)

                features = list(selectedLayer.getFeatures())
                total_features = len(features)
                
                # Imposta progress bar per 0% e massimo
                self.dlg.progressBar.setValue(0)
                self.dlg.progressBar.setMaximum(total_features)

                for i, f in enumerate(features):
                    values = [str(f[name]).replace('.', decimal_symbol) for name in fieldnames]
                    line = column_separator.join(values) + '\n'
                    output_file.write(line)
                    
                    # Aggiorna la progress bar
                    self.dlg.progressBar.setValue(i + 1)

            self.iface.messageBar().pushMessage(
                "Successo", "Il file CSV è stato scritto correttamente in " + filename,
                level=Qgis.Success, duration=3)
            
            # Reset della progress bar
            self.dlg.progressBar.setValue(0)

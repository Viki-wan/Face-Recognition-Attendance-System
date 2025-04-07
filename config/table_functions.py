import sqlite3
from PyQt5.QtWidgets import (QTableWidget, QTableWidgetItem, QAbstractItemView,
                           QPushButton, QHeaderView, QMessageBox, QWidget, QHBoxLayout,
                           QMenu, QAction, QApplication)
from PyQt5.QtCore import Qt, pyqtSignal

class TableFunctions:
    """Utility class for handling table operations including context menu, selection and batch deletion."""
    
    @staticmethod
    def setup_selection_features(table_widget, delete_callback=None, parent=None):
        """Configure table for advanced selection features and context menu"""
        # Enable selection settings
        table_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        
        # Enable context menu
        table_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        table_widget.customContextMenuRequested.connect(
            lambda pos: TableFunctions.show_context_menu(
                table_widget, pos, delete_callback, parent
            )
        )
        
        return table_widget
    
    @staticmethod
    def show_context_menu(table_widget, position, delete_callback=None, parent=None):
        """Display context menu with selection and deletion options"""
        menu = QMenu()
        
        # Get selection info
        selected_rows = len(table_widget.selectionModel().selectedRows())
        total_rows = table_widget.rowCount()
        
        # Add Select All action
        select_all_action = QAction("Select All", parent)
        select_all_action.triggered.connect(lambda: table_widget.selectAll())
        menu.addAction(select_all_action)
        
        # Add Unselect All if there are selections
        if selected_rows > 0:
            unselect_action = QAction("Unselect All", parent)
            unselect_action.triggered.connect(lambda: table_widget.clearSelection())
            menu.addAction(unselect_action)
        
        # Add separator
        menu.addSeparator()
        
        # Add Delete action if rows are selected and delete_callback is provided
        if selected_rows > 0 and delete_callback:
            delete_action = QAction(f"Delete Selected ({selected_rows})", parent)
            delete_action.triggered.connect(
                lambda: TableFunctions.delete_selected_rows(table_widget, delete_callback, parent)
            )
            menu.addAction(delete_action)
        
        # Show the menu
        menu.exec_(table_widget.viewport().mapToGlobal(position))
    
    @staticmethod
    def delete_selected_rows(table_widget, delete_callback, parent=None):
        """Delete all selected rows using the provided callback"""
        selected_rows = table_widget.selectionModel().selectedRows()
        
        if not selected_rows:
            return
        
        # Extract row IDs - We need to find which column has the actual ID
        # In most admin tables, ID is usually the first column, but let's make it robust
        # by checking the header labels to find the one named "ID"
        
        id_column = 0  # Default to first column
        
        # Try to find the column labeled "ID"
        for col in range(table_widget.columnCount()):
            header_item = table_widget.horizontalHeaderItem(col)
            if header_item and header_item.text() == "ID":
                id_column = col
                break
        
        selected_ids = []
        for index in selected_rows:
            row = index.row()
            id_item = table_widget.item(row, id_column)
            if id_item:
                try:
                    selected_ids.append(int(id_item.text()))
                except ValueError:
                    # If conversion fails, print a warning
                    print(f"Warning: Could not convert '{id_item.text()}' to an integer ID at row {row}, column {id_column}")
        
        if not selected_ids:
            QMessageBox.warning(
                parent, "Selection Error", 
                "Could not identify valid IDs from the selected rows."
            )
            return
        
        # Confirm deletion
        confirm = QMessageBox.question(
            parent, "Confirm Batch Deletion", 
            f"Are you sure you want to delete {len(selected_ids)} selected items?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            # Save current scroll position
            scrollbar = table_widget.verticalScrollBar()
            current_pos = scrollbar.value()
            
            # Call the delete callback with the list of IDs
            delete_callback(selected_ids)
            
            # Restore scroll position
            QApplication.processEvents()
            scrollbar.setValue(current_pos)
            
    @staticmethod
    def maintain_scroll_position(table_widget, operation_func):
        """Maintain scroll position when performing operations on the table"""
        # Save current scroll position
        scrollbar = table_widget.verticalScrollBar()
        current_pos = scrollbar.value()
        
        # Save selected rows
        selected_rows = [index.row() for index in table_widget.selectionModel().selectedRows()]
        
        # Perform the operation
        result = operation_func()
        
        # Restore selection if possible
        table_widget.clearSelection()
        for row in selected_rows:
            if row < table_widget.rowCount():
                table_widget.selectRow(row)
        
        # Restore scroll position
        QApplication.processEvents()
        scrollbar.setValue(current_pos)
        
        return result
    
    @staticmethod
    def setup_sorting(table_widget):
        """Configure table for custom sorting behavior"""
        table_widget.setSortingEnabled(True)
        header = table_widget.horizontalHeader()
        header.sectionClicked.connect(lambda index: 
                                     TableFunctions.sort_by_column(table_widget, index))
    
    @staticmethod
    def sort_by_column(table_widget, column_index):
        """Custom sorting function that preserves selection and scroll position"""
        # Toggle sort order
        if table_widget.horizontalHeader().sortIndicatorSection() == column_index:
            order = Qt.AscendingOrder if table_widget.horizontalHeader().sortIndicatorOrder() == Qt.DescendingOrder else Qt.DescendingOrder
        else:
            order = Qt.AscendingOrder
            
        # Disable sorting temporarily to avoid automatic sort
        table_widget.setSortingEnabled(False)
        
        # Save current selections and scroll position
        scrollbar = table_widget.verticalScrollBar()
        current_pos = scrollbar.value()
        selected_rows = [index.row() for index in table_widget.selectionModel().selectedRows()]
        
        # Perform the sort
        table_widget.sortItems(column_index, order)
        
        # Re-enable sorting
        table_widget.setSortingEnabled(True)
        
        # Restore scroll position
        QApplication.processEvents()
        scrollbar.setValue(current_pos)
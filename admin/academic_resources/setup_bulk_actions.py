import csv
import sqlite3
from PyQt5.QtWidgets import (QGroupBox, QHBoxLayout, QPushButton, 
                            QMessageBox, QFileDialog)
from config.utils_constants import DATABASE_PATH

def setup_bulk_actions(session_manager):
    """Add a new section for bulk actions to the session manager
    
    """
    # Create a group box for bulk actions
    bulk_group = QGroupBox("Bulk Actions")
    bulk_layout = QHBoxLayout()
    
    # Export button
    export_button = QPushButton("Export to CSV")
    export_button.clicked.connect(lambda: export_sessions_to_csv(session_manager))
    bulk_layout.addWidget(export_button)
    
    # Bulk delete button (with filter criteria)
    bulk_delete_button = QPushButton("Delete Filtered Sessions")
    bulk_delete_button.clicked.connect(lambda: confirm_bulk_delete(session_manager))
    bulk_layout.addWidget(bulk_delete_button)
    
    # Add to layout
    bulk_group.setLayout(bulk_layout)
    
    # Insert before the buttons layout
    layout = session_manager.layout()
    layout.insertWidget(layout.count() - 1, bulk_group)

def export_sessions_to_csv(session_manager):
    """Export the currently filtered sessions to a CSV file
    
    Args:
        session_manager: The SessionManager instance containing filter settings
    """
    try:
        # Get the filtered sessions
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get date filter
        date_clause, date_params = session_manager.get_date_filter_criteria()
        
        # Base query
        query = f"""
            SELECT s.session_id, c.class_name, co.course_name, s.date, 
                  s.start_time, s.end_time, s.status
            FROM class_sessions s
            JOIN classes c ON s.class_id = c.class_id
            JOIN courses co ON c.course_code = co.course_code
            WHERE {date_clause}
        """
        params = date_params
        
        # Apply class filter
        if session_manager.class_filter.currentData():
            query += " AND s.class_id = ?"
            params.append(session_manager.class_filter.currentData())
        
        # Apply status filter
        if session_manager.status_filter.currentText() != "All Statuses":
            query += " AND s.status = ?"
            params.append(session_manager.status_filter.currentText())
        
        # Order by class, date and start time
        query += " ORDER BY c.class_name, s.date, s.start_time"
        
        cursor.execute(query, params)
        sessions = cursor.fetchall()
        conn.close()
        
        if not sessions:
            QMessageBox.information(session_manager, "Export", "No sessions to export")
            return
        
        # Ask for save location
        file_path, _ = QFileDialog.getSaveFileName(
            session_manager, "Save CSV File", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return  # User cancelled
            
        # Add .csv extension if not present
        if not file_path.lower().endswith('.csv'):
            file_path += '.csv'
        
        # Write to CSV
        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(['Session ID', 'Class', 'Course', 'Date', 'Start Time', 'End Time', 'Status'])
            
            # Write data
            for session in sessions:
                writer.writerow(session)
                
        QMessageBox.information(session_manager, "Export Successful", f"Exported {len(sessions)} sessions to {file_path}")
        
    except Exception as e:
        print(f"❌ Error exporting sessions: {e}")
        QMessageBox.warning(session_manager, "Export Error", f"Could not export sessions: {e}")

def confirm_bulk_delete(session_manager):
    """Confirm and perform bulk deletion of filtered sessions
    
    Args:
        session_manager: The SessionManager instance containing filter settings
    """
    # Build description of what will be deleted
    description = "Delete all sessions with the following filters:\n\n"
    
    # Date filter
    if session_manager.today_radio.isChecked():
        description += "- Date: Today only\n"
    elif session_manager.this_week_radio.isChecked():
        description += "- Date: This week\n"
    else:
        selected_date = session_manager.date_filter.date().toString('yyyy-MM-dd')
        description += f"- Date: {selected_date}\n"
    
    # Class filter
    if session_manager.class_filter.currentData():
        class_text = session_manager.class_filter.currentText()
        description += f"- Class: {class_text}\n"
    else:
        description += "- Class: All classes\n"
    
    # Status filter
    status = session_manager.status_filter.currentText()
    description += f"- Status: {status}\n"
    
    # Confirmation dialog
    reply = QMessageBox.warning(
        session_manager,
        "Confirm Bulk Delete",
        description + "\nThis action cannot be undone. Are you sure?",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No
    )
    
    if reply != QMessageBox.Yes:
        return
    
    # Perform the bulk delete
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get date filter
        date_clause, date_params = session_manager.get_date_filter_criteria()
        
        # Base query
        query = f"""
            DELETE FROM class_sessions
            WHERE {date_clause}
        """
        params = date_params
        
        # Apply class filter
        if session_manager.class_filter.currentData():
            query += " AND class_id = ?"
            params.append(session_manager.class_filter.currentData())
        
        # Apply status filter
        if session_manager.status_filter.currentText() != "All Statuses":
            query += " AND status = ?"
            params.append(session_manager.status_filter.currentText())
        
        # Execute the delete
        cursor.execute(query, params)
        rows_deleted = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        # Reload sessions
        session_manager.load_sessions()
        
        QMessageBox.information(session_manager, "Bulk Delete", f"Successfully deleted {rows_deleted} sessions")
        
    except Exception as e:
        print(f"❌ Error during bulk delete: {e}")
        QMessageBox.warning(session_manager, "Database Error", f"Could not delete sessions: {e}")

def bulk_update_status(self):
        """Update status for all selected sessions"""
        selected_sessions = []
        for row in range(self.sessions_table.rowCount()):
            checkbox = self.sessions_table.cellWidget(row, 0)
            if checkbox and checkbox.findChild(QCheckBox).isChecked():
                session_id = int(self.sessions_table.item(row, 1).text())
                selected_sessions.append(session_id)
        
        if not selected_sessions:
            QMessageBox.warning(self, "No Selection", "Please select at least one session")
            return
        
        new_status = self.bulk_status_combo.currentText()
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            for session_id in selected_sessions:
                cursor.execute(
                    "UPDATE class_sessions SET status = ? WHERE session_id = ?", 
                    (new_status, session_id)
                )
                
            conn.commit()
            conn.close()
            
            self.load_sessions()
            QMessageBox.information(self, "Success", f"Updated {len(selected_sessions)} sessions")
            
        except Exception as e:
            print(f"❌ Error updating sessions: {e}")
            QMessageBox.warning(self, "Database Error", f"Could not update sessions: {e}")

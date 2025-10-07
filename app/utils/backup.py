"""
Utilidades para backup de base de datos
"""
import os
import subprocess
from datetime import datetime

def create_backup(database_name, output_folder='backups'):
    """Crea un backup de la base de datos"""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{database_name}_{timestamp}.sql"
    filepath = os.path.join(output_folder, filename)
    
    try:
        # Para MySQL
        command = f"mysqldump -u root {database_name} > {filepath}"
        subprocess.run(command, shell=True, check=True)
        return filepath
    except Exception as e:
        print(f"Error creando backup: {e}")
        return None
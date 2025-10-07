"""
Validadores personalizados
"""
import os
from werkzeug.utils import secure_filename

def allowed_file(filename, allowed_extensions):
    """Verifica si el archivo tiene extensión permitida"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_upload_file(file, upload_folder, allowed_extensions):
    """Guarda un archivo de forma segura"""
    if file and allowed_file(file.filename, allowed_extensions):
        filename = secure_filename(file.filename)
        # Agregar timestamp para evitar colisiones
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        return filename
    return None
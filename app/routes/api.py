"""
API RESTful para la aplicación
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models.transaccion import Transaccion

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/transacciones', methods=['GET'])
@login_required
def get_transacciones():
    """Obtiene transacciones del usuario"""
    transacciones = Transaccion.query.filter_by(
        usuario_id=current_user.id
    ).limit(50).all()
    
    return jsonify({
        'success': True,
        'data': [t.to_dict() for t in transacciones]
    })

@bp.route('/transacciones', methods=['POST'])
@login_required
def create_transaccion():
    """Crea una nueva transacción"""
    data = request.get_json()
    
    try:
        transaccion = Transaccion(
            usuario_id=current_user.id,
            cuenta_id=data['cuenta_id'],
            categoria_id=data['categoria_id'],
            tipo=data['tipo'],
            monto=data['monto'],
            descripcion=data.get('descripcion', '')
        )
        
        db.session.add(transaccion)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Transacción creada',
            'data': transaccion.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
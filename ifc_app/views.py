from flask import Blueprint, render_template, flash, redirect, url_for, request, send_file
from flask_login import login_required, current_user
from ifc_app.db import get_db

bp = Blueprint('ifc', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/history')
@login_required
def history():
    db = get_db()
    histories = db.execute(
        'SELECT id, input_file, output_format, status, created_at'
        ' FROM conversion_history'
        ' WHERE user_id = ?'
        ' ORDER BY created_at DESC',
        (current_user.id,)
    ).fetchall()
    return render_template('history.html', histories=histories)

@bp.route('/download/<int:history_id>')
@login_required
def download(history_id):
    db = get_db()
    history = db.execute(
        'SELECT * FROM conversion_history WHERE id = ? AND user_id = ?',
        (history_id, current_user.id)
    ).fetchone()
    
    if history is None:
        flash('指定された変換履歴が見つかりません。', 'error')
        return redirect(url_for('ifc.history'))
        
    if history['status'] != 'completed':
        flash('変換が完了していないファイルはダウンロードできません。', 'error')
        return redirect(url_for('ifc.history'))
    
    # TODO: 実際のファイルダウンロードの実装
    # output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], history['output_file'])
    # return send_file(output_path, as_attachment=True)
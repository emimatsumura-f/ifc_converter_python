from flask import Blueprint, render_template, flash, redirect, url_for, request, send_file, jsonify, current_app, make_response, session
from flask_login import login_required, current_user
from ifc_app.db import get_db
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import ifcopenshell
import logging

# ロガーの設定
logger = logging.getLogger(__name__)

# Blueprintの定義
bp = Blueprint('ifc', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    # セッション確認
    if not current_user.is_authenticated:
        return jsonify({'error': 'ログインが必要です'}), 401
    if 'file' not in request.files:
        return jsonify({'error': 'ファイルが選択されていません'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'ファイルが選択されていません'}), 400
        
    if not file.filename.endswith('.ifc'):
        return jsonify({'error': 'IFCファイルのみアップロード可能です'}), 400

    try:
        # アップロードフォルダの存在確認
        upload_folder = current_app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder, exist_ok=True)
            
        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_folder, filename)
        
        # ファイルを保存
        file.save(file_path)
        
        # データベースに登録
        db = get_db()
        cursor = db.execute(
            'INSERT INTO conversion_history (user_id, filename, processed_date, element_count) VALUES (?, ?, ?, ?)',
            (current_user.id, filename, datetime.now(), 0)
        )
        upload_id = cursor.lastrowid
        db.commit()

        # IFCファイルの解析処理
        try:
            elements = process_ifc_file(file_path)
        except Exception as e:
            logger.error(f"IFCファイルの解析中にエラーが発生: {str(e)}")
            return jsonify({'error': 'IFCファイルの解析中にエラーが発生しました'}), 500
        
        # element_countを更新
        db.execute(
            'UPDATE conversion_history SET element_count = ? WHERE id = ?',
            (len(elements), upload_id)
        )
        db.commit()
        
        return jsonify({
            'redirect': url_for('ifc.preview', upload_id=upload_id)
        }), 200
    except Exception as e:
        logger.error(f"Unexpected error during file upload: {str(e)}")
        return jsonify({'error': 'ファイルのアップロード中にエラーが発生しました'}), 500

@bp.route('/preview/<int:upload_id>')
@login_required
def preview(upload_id):
    db = get_db()
    upload = db.execute(
        'SELECT * FROM conversion_history WHERE id = ? AND user_id = ?',
        (upload_id, current_user.id)
    ).fetchone()
    
    if upload is None:
        flash('指定された変換履歴が見つかりません。', 'error')
        return redirect(url_for('ifc.history'))

    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], upload['filename'])
    
    try:
        elements = process_ifc_file(file_path)
    except Exception as e:
        logger.error(f"プレビュー生成中にエラーが発生: {str(e)}")
        flash('IFCファイルの解析中にエラーが発生しました。', 'error')
        return redirect(url_for('ifc.history'))
    
    return render_template('preview.html', upload=upload, elements=elements)

@bp.route('/history')
@login_required
def history():
    db = get_db()
    uploads = db.execute(
        'SELECT * FROM conversion_history WHERE user_id = ? ORDER BY processed_date DESC',
        (current_user.id,)
    ).fetchall()
    return render_template('history.html', uploads=uploads)

@bp.route('/download_csv/<int:upload_id>')
@login_required
def download_csv(upload_id):
    db = get_db()
    upload = db.execute(
        'SELECT * FROM conversion_history WHERE id = ? AND user_id = ?',
        (upload_id, current_user.id)
    ).fetchone()
    
    if upload is None:
        flash('指定された変換履歴が見つかりません。', 'error')
        return redirect(url_for('ifc.history'))
    
    # TODO: 実際のCSVダウンロード処理を実装
    return "CSV download not implemented yet", 501

# IFCファイル処理関数
def process_ifc_file(filepath):
    """
    IFCファイルを処理して部材情報を抽出する
    """
    try:
        ifc_file = ifcopenshell.open(filepath)
        elements = []
        # BeamとColumnの要素を取得
        beams = ifc_file.by_type('IfcBeam')
        columns = ifc_file.by_type('IfcColumn')
        
        # Beamの情報を処理
        for beam in beams:
            try:
                properties = {
                    "type": "Beam",
                    "name": beam.Name if hasattr(beam, 'Name') else "未定義",
                    "size": "400x600",  # テスト用の仮の値
                    "weight": "960kg",   # テスト用の仮の値
                    "length": "6000mm"   # テスト用の仮の値
                }
                elements.append(properties)
            except Exception as e:
                logger.warning(f"Beam {beam.id()} の処理中にエラーが発生: {str(e)}")
                continue
                
        # Columnの情報を処理
        for column in columns:
            try:
                properties = {
                    "type": "Column",
                    "name": column.Name if hasattr(column, 'Name') else "未定義",
                    "size": "400x400",   # テスト用の仮の値
                    "weight": "1200kg",  # テスト用の仮の値
                    "length": "4000mm"   # テスト用の仮の値
                }
                elements.append(properties)
            except Exception as e:
                logger.warning(f"Column {column.id()} の処理中にエラーが発生: {str(e)}")
                continue
                
        return elements
    except Exception as e:
        logger.error(f"IFCファイルの処理中にエラーが発生: {str(e)}")
        raise
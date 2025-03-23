from flask import Blueprint, render_template, flash, redirect, url_for, request, send_file, jsonify, current_app, make_response, session
from flask_login import login_required, current_user
from ifc_app.db import get_db
from ifc_app.ifc_processor import process_ifc_file
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import logging
import io
import csv

# ロガーの設定
logger = logging.getLogger(__name__)

# Blueprintの定義
bp = Blueprint('ifc', __name__)

@bp.route('/')
@login_required  # ログイン要求を追加
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
    
    try:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], upload['filename'])
        elements = process_ifc_file(file_path)
        
        # CSVデータを生成
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=['type', 'name', 'description', 'size', 'weight', 'length'])
        writer.writeheader()
        writer.writerows(elements)
        
        # CSVファイルをレスポンスとして返す
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = f"attachment; filename=ifc_elements_{upload_id}.csv"
        response.headers["Content-type"] = "text/csv; charset=utf-8"
        return response
        
    except Exception as e:
        logger.error(f"CSVファイルの生成中にエラーが発生: {str(e)}")
        flash('CSVファイルの生成中にエラーが発生しました。', 'error')
        return redirect(url_for('ifc.history'))
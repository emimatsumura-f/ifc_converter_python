from flask import Blueprint, render_template, flash, redirect, url_for, request, send_file, jsonify, current_app, make_response, session
from flask_login import login_required, current_user
from ifc_app.db import get_db
from ifc_app.ifc_processor import process_ifc_file
import os
import shutil
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
    if not current_user.is_authenticated:
        return jsonify({'error': 'アップロード中にエラーが発生しました'}), 401

    if 'file' not in request.files:
        return jsonify({'error': 'アップロード中にエラーが発生しました'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'アップロード中にエラーが発生しました'}), 400
        
    if not file.filename.endswith('.ifc'):
        return jsonify({'error': 'IFCファイルのみアップロード可能です'}), 400

    try:
        db = get_db()
        # まず変換履歴レコードを作成
        cursor = db.execute(
            'INSERT INTO conversion_history (user_id, filename, processed_date, element_count, status) VALUES (?, ?, ?, ?, ?)',
            (current_user.id, secure_filename(file.filename), datetime.now(), 0, 'processing')
        )
        upload_id = cursor.lastrowid

        # アップロード情報を保存
        chunk_size = 1024 * 1024  # 1MB chunks
        file.seek(0, 2)  # ファイルの末尾に移動
        file_size = file.tell()  # ファイルサイズを取得
        file.seek(0)  # ファイルポインタを先頭に戻す
        
        chunks_total = (file_size + chunk_size - 1) // chunk_size

        db.execute(
            'INSERT INTO file_uploads (user_id, upload_id, filename, file_size, chunk_size, chunks_total, upload_status) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (current_user.id, upload_id, secure_filename(file.filename), file_size, chunk_size, chunks_total, 'pending')
        )
        db.commit()

        # アップロード用ディレクトリの作成
        upload_folder = current_app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder, exist_ok=True)

        return jsonify({
            'upload_id': upload_id,
            'chunks_total': chunks_total,
            'chunk_size': chunk_size
        }), 200

    except Exception as e:
        logger.error(f"Unexpected error during file upload initialization: {str(e)}")
        return jsonify({'error': 'アップロード中にエラーが発生しました'}), 500

@bp.route('/upload/<int:upload_id>/chunk/<int:chunk_number>', methods=['POST'])
@login_required
def upload_chunk(upload_id, chunk_number):
    if not current_user.is_authenticated:
        return jsonify({'error': 'アップロード中にエラーが発生しました'}), 401

    if 'chunk' not in request.files:
        return jsonify({'error': 'アップロード中にエラーが発生しました'}), 400

    try:
        db = get_db()
        # アップロード情報の取得と検証
        upload = db.execute(
            'SELECT * FROM file_uploads WHERE upload_id = ? AND user_id = ?',
            (upload_id, current_user.id)
        ).fetchone()

        if upload is None:
            return jsonify({'error': 'アップロード中にエラーが発生しました'}), 404

        if chunk_number >= upload['chunks_total']:
            return jsonify({'error': '不正なチャンク番号です'}), 400

        # チャンクの保存
        chunk = request.files['chunk']
        temp_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], f'temp_{upload_id}')
        os.makedirs(temp_dir, exist_ok=True)
        chunk_path = os.path.join(temp_dir, f'chunk_{chunk_number}')
        chunk.save(chunk_path)

        # アップロード状態の更新
        db.execute(
            'UPDATE file_uploads SET chunks_uploaded = chunks_uploaded + 1, upload_status = ? WHERE upload_id = ?',
            ('uploading', upload_id)
        )
        db.commit()

        # 全チャンクがアップロードされた場合、ファイルの結合を行う
        updated_upload = db.execute(
            'SELECT * FROM file_uploads WHERE upload_id = ?', 
            (upload_id,)
        ).fetchone()

        if updated_upload['chunks_uploaded'] == updated_upload['chunks_total']:
            try:
                final_path = os.path.join(current_app.config['UPLOAD_FOLDER'], upload['filename'])
                with open(final_path, 'wb') as outfile:
                    for i in range(updated_upload['chunks_total']):
                        chunk_path = os.path.join(temp_dir, f'chunk_{i}')
                        with open(chunk_path, 'rb') as infile:
                            outfile.write(infile.read())

                # 一時ファイルの削除
                shutil.rmtree(temp_dir)

                # IFCファイルの解析処理
                elements = process_ifc_file(final_path)
                
                # element_countとステータスを更新
                db.execute(
                    'UPDATE conversion_history SET element_count = ?, status = ? WHERE id = ?',
                    (len(elements), 'completed', upload_id)
                )
                db.execute(
                    'UPDATE file_uploads SET upload_status = ? WHERE upload_id = ?',
                    ('completed', upload_id)
                )
                db.commit()

                return jsonify({
                    'status': 'completed',
                    'redirect': url_for('ifc.preview', upload_id=upload_id)
                }), 200

            except Exception as e:
                logger.error(f"Error processing completed file: {str(e)}")
                db.execute(
                    'UPDATE conversion_history SET status = ? WHERE id = ?',
                    ('failed', upload_id)
                )
                db.execute(
                    'UPDATE file_uploads SET upload_status = ? WHERE upload_id = ?',
                    ('failed', upload_id)
                )
                db.commit()
                return jsonify({'error': 'アップロード中にエラーが発生しました'}), 500

        return jsonify({
            'status': 'uploading',
            'chunks_uploaded': updated_upload['chunks_uploaded'],
            'chunks_total': updated_upload['chunks_total']
        }), 200

    except Exception as e:
        logger.error(f"Error handling chunk upload: {str(e)}")
        return jsonify({'error': 'アップロード中にエラーが発生しました'}), 500

@bp.route('/preview/<int:upload_id>')
@login_required
def preview(upload_id):
    db = get_db()
    logger.info(f"プレビューページにアクセスしました。upload_id: {upload_id}")
    
    upload = db.execute(
        'SELECT * FROM conversion_history WHERE id = ? AND user_id = ?',
        (upload_id, current_user.id)
    ).fetchone()
    
    if upload is None:
        logger.warning(f"変換履歴が見つかりません。upload_id: {upload_id}, user_id: {current_user.id}")
        flash('指定された変換履歴が見つかりません。', 'error')
        return redirect(url_for('ifc.history'))

    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], upload['filename'])
    
    try:
        elements = process_ifc_file(file_path)
        if not elements:
            logger.warning(f"解析可能な部材が見つかりませんでした。filename: {upload['filename']}")
            flash('IFCファイルから部材情報を抽出できませんでした。', 'warning')
            return render_template('preview.html', upload=upload, elements=[])
            
        logger.info(f"IFCファイルの解析が完了しました。filename: {upload['filename']}")
        return render_template('preview.html', upload=upload, elements=elements)
        
    except FileNotFoundError as e:
        logger.error(f"IFCファイルが見つかりません: {str(e)}")
        flash('IFCファイルが見つかりません。', 'error')
        return redirect(url_for('ifc.history'))
    except RuntimeError as e:
        logger.error(f"IFCファイルの解析中にエラーが発生: {str(e)}")
        flash('IFCファイルの解析中にエラーが発生しました。', 'error')
        return redirect(url_for('ifc.history'))
    except Exception as e:
        logger.error(f"予期せぬエラーが発生: {str(e)}", exc_info=True)
        flash('予期せぬエラーが発生しました。', 'error')
        return redirect(url_for('ifc.history'))

@bp.route('/history')
@login_required
def history():
    db = get_db()
    histories = db.execute(
        'SELECT * FROM conversion_history WHERE user_id = ? ORDER BY processed_date DESC',
        (current_user.id,)
    ).fetchall()
    return render_template('history.html', histories=histories)

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

@bp.route('/history/<int:history_id>/delete', methods=['POST'])
@login_required
def delete_history(history_id):
    db = get_db()
    history = db.execute(
        'SELECT * FROM conversion_history WHERE id = ? AND user_id = ?',
        (history_id, current_user.id)
    ).fetchone()

    if history is None:
        flash('履歴が見つかりません', 'error')
        return redirect(url_for('ifc.history'))

    try:
        # ファイルを削除
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], history['filename'])
        if os.path.exists(file_path):
            os.remove(file_path)

        # 一時ファイルディレクトリも削除（もし存在していれば）
        temp_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], f'temp_{history_id}')
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

        # データベースから履歴を削除
        db.execute('DELETE FROM conversion_history WHERE id = ?', (history_id,))
        # file_uploadsテーブルからも削除
        db.execute('DELETE FROM file_uploads WHERE upload_id = ?', (history_id,))
        db.commit()
        
        flash('履歴を削除しました', 'success')
        return redirect(url_for('ifc.history'))

    except Exception as e:
        db.rollback()
        logger.error(f"履歴削除中にエラーが発生: {str(e)}")
        flash('削除中にエラーが発生しました', 'error')
        return redirect(url_for('ifc.history'))

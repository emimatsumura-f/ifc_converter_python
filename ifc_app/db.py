# このファイルはFlaskアプリケーションのデータベース接続と管理を担当します
# SQLiteデータベースを使用し、アプリケーションのコンテキスト内でデータベース接続を管理します

import sqlite3
import click
from flask import current_app, g
from flask.cli import with_appcontext

def get_db():
    # データベース接続を取得する関数
    # g は Flask の特別なオブジェクトで、リクエストごとに新しく作成され、
    # リクエスト中のデータを保存するために使用されます
    if 'db' not in g:
        # データベースが接続されていない場合は新しい接続を作成
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],  # アプリケーション設定からデータベースのパスを取得
            detect_types=sqlite3.PARSE_DECLTYPES  # SQLiteの型を自動的に検出
        )
        g.db.row_factory = sqlite3.Row  # 取得結果を辞書形式で返すように設定

    return g.db

def close_db(e=None):
    # データベース接続を閉じる関数
    # リクエスト終了時に自動的に呼び出されます
    db = g.pop('db', None)  # g オブジェクトからデータベース接続を取得して削除

    if db is not None:
        db.close()  # データベース接続が存在する場合は閉じる

def init_db():
    # データベースを初期化する関数
    # schema.sqlファイルを読み込んでテーブルを作成します
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

@click.command('init-db')
@with_appcontext
def init_db_command():
    # データベース初期化のためのCLIコマンド
    # `flask init-db` コマンドで実行できます
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    # Flaskアプリケーションにデータベース機能を登録する関数
    # アプリケーション終了時にデータベース接続を閉じ、
    # init-dbコマンドを使用可能にします
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
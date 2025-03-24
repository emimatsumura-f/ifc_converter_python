# ユーザー認証に必要なデータベース操作を行うためのモジュールをインポート
from ifc_app.db import get_db

# ユーザー情報を管理するためのクラス
# Flask-Loginで必要とされる認証関連のメソッドも実装しています
class User:
    # ユーザーインスタンスの初期化
    # id: データベース上のユーザーID
    # username: ユーザーの表示名
    def __init__(self, id, username):
        self.id = id
        self.username = username

    # 指定されたIDのユーザーをデータベースから取得するクラスメソッド
    # @staticmethod デコレータにより、インスタンス化せずに使用可能
    @staticmethod
    def get(id):
        # データベース接続を取得
        db = get_db()
        # SQLクエリでユーザー情報を取得
        user = db.execute(
            'SELECT * FROM user WHERE id = ?', (id,)
        ).fetchone()
        # ユーザーが存在しない場合はNoneを返す
        if not user:
            return None
        # ユーザーが存在する場合は、新しいUserインスタンスを作成して返す
        return User(user['id'], user['username'])

    # Flask-Login用のメソッド：ユーザーが認証済みかどうかを返す
    # このアプリでは常にTrueを返す（ログイン済みユーザーのみインスタンス化される）
    def is_authenticated(self):
        return True

    # Flask-Login用のメソッド：ユーザーアカウントがアクティブかどうかを返す
    # このアプリでは常にTrueを返す（アカウントの無効化機能は未実装）
    def is_active(self):
        return True

    # Flask-Login用のメソッド：匿名ユーザーかどうかを返す
    # このアプリでは常にFalseを返す（全てのユーザーは登録済みユーザー）
    def is_anonymous(self):
        return False

    # Flask-Login用のメソッド：ユーザーIDを文字列で返す
    # セッション管理などで使用される
    def get_id(self):
        return str(self.id)
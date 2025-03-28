# IFC Converter

IFCファイル（Building Information Modeling）をCSVファイルに変換するWebアプリケーションです。

## 主な機能

- ユーザー認証（登録・ログイン）
- IFCファイルのアップロード（チャンク分割による大容量ファイル対応）
- IFCファイルの内容プレビュー表示
  - 部材情報（Beam、Column）の詳細表示
  - プロファイル情報の自動抽出
  - 重量・長さ情報の表示
- CSVファイルへの変換とダウンロード
- 変換履歴の管理と閲覧
- 解析結果のキャッシュ機能による高速表示

## 技術スタック

- Python 3.9
- Flask (Webフレームワーク)
- Flask-Login (ユーザー認証)
- IfcOpenShell (IFCファイル処理)
- SQLite (データベース)
- Bootstrap 5 (フロントエンドUI)

## セットアップ

1. Python 3.9以上をインストール

2. 仮想環境の作成と有効化
```bash
python -m venv ifc_env
source ifc_env/bin/activate  # Unix系
# または
ifc_env\Scripts\activate  # Windows
```

3. 必要なパッケージのインストール
```bash
pip install -r requirements.txt
```

4. データベースの初期化
```bash
flask --app ifc_app init-db
```

5. 開発サーバーの起動
```bash
flask --app ifc_app run
```

本番環境では、Gunicornを使用してサーバーを起動します：
```bash
gunicorn -c gunicorn.conf.py "ifc_app:create_app()"
```

## 使用方法

1. アカウントを作成してログイン
2. ホーム画面からIFCファイルをアップロード
3. アップロード完了後、自動的にファイルの内容がプレビュー表示
4. プレビュー画面でCSVファイルとしてダウンロード可能
5. 履歴画面で過去の変換履歴を確認可能

## ライセンス

[IfcOpenShell](https://github.com/IfcOpenShell/IfcOpenShell)のライセンスに準拠します。

## 開発者向け情報

- `ifc_app/`: メインアプリケーションコード
  - `models.py`: データモデルの定義
  - `views.py`: ルーティングとビューの定義
  - `ifc_processor.py`: IFCファイル処理ロジック
  - `auth/`: 認証関連の機能
  - `static/`: CSS、JavaScriptファイル
  - `templates/`: HTMLテンプレート

- `instance/`: データベースとアップロードされたファイル
- `src/ifcopenshell/`: IFCファイル処理ライブラリ
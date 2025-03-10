import os
import sys
import json
import ifcopenshell
import http.server
import socketserver
import webbrowser
from urllib.parse import urlparse, parse_qs

# 処理したIFCファイルの情報を保存するディレクトリ
DATA_DIR = "data"

# IFCファイル処理クラス
class IFCProcessor:
    def __init__(self):
        """IFCファイル処理クラスの初期化"""
        # 処理結果を保存するディレクトリがなければ作成
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
    
    def process_file(self, file_path):
        """IFCファイルを処理する関数
        
        引数:
            file_path (str): 処理するIFCファイルのパス
            
        戻り値:
            dict: 処理結果のデータ
        """
        try:
            # IFCファイルを読み込む
            ifc_file = ifcopenshell.open(file_path)
            print(f"IFCファイルを読み込みました: {file_path}")
            
            # IFCファイルから情報を抽出
            result = self._extract_info(ifc_file)
            
            # 結果をJSONとして保存
            file_name = os.path.basename(file_path)
            json_path = os.path.join(DATA_DIR, f"{os.path.splitext(file_name)[0]}.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"処理結果をJSONとして保存しました: {json_path}")
            return result
            
        except Exception as e:
            print(f"エラーが発生しました: {str(e)}")
            return {"error": str(e)}
    
    def _extract_info(self, ifc_file):
        """IFCファイルから情報を抽出する関数
        
        引数:
            ifc_file: ifcopenshellで開いたIFCファイル
            
        戻り値:
            dict: 抽出した情報
        """
        # 抽出する情報の初期化
        info = {
            "project_info": {},
            "building_elements": [],
            "properties": {},
            "materials": []
        }
        
        # プロジェクト情報を取得
        projects = ifc_file.by_type("IfcProject")
        if projects:
            project = projects[0]
            info["project_info"] = {
                "name": project.Name or "名称なし",
                "description": project.Description or "説明なし",
                "global_id": project.GlobalId
            }
        
        # 建物要素（壁、床、柱など）を取得
        for element_type in ["IfcWall", "IfcSlab", "IfcColumn", "IfcBeam", "IfcDoor", "IfcWindow"]:
            elements = ifc_file.by_type(element_type)
            for element in elements:
                element_info = {
                    "id": element.id(),
                    "type": element_type,
                    "name": element.Name or "名称なし",
                    "global_id": element.GlobalId
                }
                info["building_elements"].append(element_info)
        
        # 材料情報を取得
        materials = ifc_file.by_type("IfcMaterial")
        for material in materials:
            material_info = {
                "id": material.id(),
                "name": material.Name or "名称なし"
            }
            info["materials"].append(material_info)
        
        # プロパティセット情報を取得
        psets = ifc_file.by_type("IfcPropertySet")
        for pset in psets:
            property_dict = {}
            for prop in pset.HasProperties:
                if hasattr(prop, "NominalValue") and prop.NominalValue:
                    property_dict[prop.Name] = prop.NominalValue.wrappedValue
                else:
                    property_dict[prop.Name] = "値なし"
            
            info["properties"][pset.Name] = property_dict
        
        return info
    
    def get_available_properties(self, file_path=None):
        """利用可能なプロパティの一覧を取得する関数
        
        引数:
            file_path (str, optional): IFCファイルのパス。指定されていない場合は保存済みのJSONから取得
            
        戻り値:
            list: 利用可能なプロパティのリスト
        """
        try:
            # ファイルパスが指定されている場合は処理
            if file_path and os.path.exists(file_path):
                result = self.process_file(file_path)
                properties = result.get("properties", {})
            else:
                # 保存済みのJSONファイルから最新のものを取得
                json_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.json')]
                if not json_files:
                    return []
                
                # 最新のファイルを取得
                latest_file = max(json_files, key=lambda f: os.path.getmtime(os.path.join(DATA_DIR, f)))
                json_path = os.path.join(DATA_DIR, latest_file)
                
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                properties = data.get("properties", {})
            
            # プロパティの一覧を作成
            property_list = []
            for pset_name, props in properties.items():
                for prop_name in props.keys():
                    property_list.append(f"{pset_name}.{prop_name}")
            
            return property_list
            
        except Exception as e:
            print(f"プロパティ一覧の取得中にエラーが発生しました: {str(e)}")
            return []

# メイン処理
def main():
    """メイン処理"""
    # コマンドライン引数の処理
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "process" and len(sys.argv) > 2:
            # IFCファイルの処理
            file_path = sys.argv[2]
            processor = IFCProcessor()
            processor.process_file(file_path)
        
        elif command == "properties" and len(sys.argv) > 2:
            # 利用可能なプロパティの一覧を取得
            file_path = sys.argv[2]
            processor = IFCProcessor()
            properties = processor.get_available_properties(file_path)
            print(json.dumps(properties, ensure_ascii=False, indent=2))
        
        elif command == "serve":
            # 簡易HTTPサーバーを起動
            PORT = 8000
            Handler = http.server.SimpleHTTPRequestHandler
            
            with socketserver.TCPServer(("", PORT), Handler) as httpd:
                print(f"サーバーを起動しました: http://localhost:{PORT}")
                # デフォルトのブラウザでアプリを開く
                webbrowser.open(f"http://localhost:{PORT}")
                # サーバーを実行
                httpd.serve_forever()
        
        else:
            print_usage()
    else:
        print_usage()

def print_usage():
    """使用方法を表示"""
    print("使用方法:")
    print("  python app.py process <ifc_file_path>  - IFCファイルを処理")
    print("  python app.py properties <ifc_file_path> - 利用可能なプロパティの一覧を取得")
    print("  python app.py serve - ローカルサーバーを起動してアプリを実行")

if __name__ == "__main__":
    main()
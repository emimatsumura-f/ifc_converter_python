import ifcopenshell
import logging
import os
from . import db
from datetime import datetime

logger = logging.getLogger(__name__)

def get_cached_elements(conversion_id):
    """キャッシュされた要素を取得"""
    try:
        database = db.get_db()
        elements = database.execute(
            'SELECT * FROM ifc_elements_cache WHERE conversion_id = ?',
            (conversion_id,)
        ).fetchall()
        
        if elements:
            return [{
                'type': element['element_type'],
                'name': element['element_name'],
                'description': element['element_description'],
                'size': element['profile_size'],
                'weight': element['weight'],
                'length': element['length']
            } for element in elements]
        return None
    except Exception as e:
        logger.error(f"キャッシュの取得中にエラーが発生: {str(e)}")
        return None

def cache_elements(conversion_id, elements):
    """要素をキャッシュに保存"""
    try:
        database = db.get_db()
        for element in elements:
            database.execute(
                '''INSERT INTO ifc_elements_cache 
                   (conversion_id, element_type, element_name, element_description, 
                    profile_size, weight, length)
                   VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (conversion_id, element['type'], element['name'], 
                 element.get('description', '未定義'),
                 element.get('size', '未定義'), 
                 element.get('weight', '未定義'),
                 element.get('length', '未定義'))
            )
        database.commit()
    except Exception as e:
        logger.error(f"キャッシュの保存中にエラーが発生: {str(e)}")
        database.rollback()

def process_ifc_file(filepath, conversion_id=None):
    """
    IFCファイルを処理して部材情報を抽出する
    """
    if not os.path.exists(filepath):
        error_msg = f"IFCファイルが見つかりません: {filepath}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    # キャッシュが利用可能な場合はキャッシュから返す
    if conversion_id:
        cached_elements = get_cached_elements(conversion_id)
        if cached_elements:
            logger.info(f"キャッシュから要素を取得: conversion_id={conversion_id}")
            return cached_elements

    try:
        logger.info(f"IFCファイルの処理を開始: {filepath}")
        ifc_file = ifcopenshell.open(filepath)
        elements = []

        # BeamとColumnの要素を取得
        beams = ifc_file.by_type('IfcBeam')
        columns = ifc_file.by_type('IfcColumn')

        logger.info(f"検出された部材数: Beams={len(beams)}, Columns={len(columns)}")

        # Beamの情報を処理
        for beam in beams:
            try:
                properties = {
                    "type": "Beam",
                    "name": beam.Name if hasattr(beam, 'Name') else "未定義",
                    "description": beam.Description if hasattr(beam, 'Description') else "未定義",
                    "size": extract_profile_information(beam),
                    "weight": get_weight(beam),
                    "length": get_length(beam)
                }
                elements.append(properties)
            except Exception as e:
                logger.warning(f"Beam {beam.id() if hasattr(beam, 'id') else 'unknown'} の処理中にエラーが発生: {str(e)}")
                continue

        # Columnの情報を処理
        for column in columns:
            try:
                properties = {
                    "type": "Column",
                    "name": column.Name if hasattr(column, 'Name') else "未定義",
                    "description": column.Description if hasattr(column, 'Description') else "未定義",
                    "size": extract_profile_information(column),
                    "weight": get_weight(column),
                    "length": get_length(column)
                }
                elements.append(properties)
            except Exception as e:
                logger.warning(f"Column {column.id() if hasattr(column, 'id') else 'unknown'} の処理中にエラーが発生: {str(e)}")
                continue

        if not elements:
            logger.warning("解析可能な部材が見つかりませんでした")
            
        logger.info(f"IFCファイルの処理が完了しました。抽出された部材数: {len(elements)}")

        if conversion_id and elements:
            # 解析結果をキャッシュに保存
            cache_elements(conversion_id, elements)
            logger.info(f"要素をキャッシュに保存: conversion_id={conversion_id}")

        return elements

    except Exception as e:
        error_msg = f"IFCファイルの処理中に重大なエラーが発生: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise RuntimeError(error_msg) from e

def extract_profile_information(element):
    """部材のプロファイル情報を抽出"""
    try:
        # まず、Description属性をチェック
        if hasattr(element, 'Description') and element.Description:
            return element.Description

        # PropertySetから情報を取得
        for rel in element.IsDefinedBy:
            if rel.is_a("IfcRelDefinesByProperties"):
                property_set = rel.RelatingPropertyDefinition
                if property_set.is_a("IfcPropertySet"):
                    for prop in property_set.HasProperties:
                        # 断面性能に関連するpropertyを検索
                        if any(keyword in prop.Name.lower() for keyword in ["section", "profile", "size"]):
                            if hasattr(prop, "NominalValue"):
                                return prop.NominalValue.wrappedValue

        # 材料プロファイルから情報を取得
        for rel in element.HasAssociations:
            if rel.is_a("IfcRelAssociatesMaterial"):
                material = rel.RelatingMaterial
                if material.is_a("IfcMaterialProfileSet"):
                    for profile in material.MaterialProfiles:
                        if profile.Profile:
                            return profile.Profile.ProfileName

        return "未定義"
    except Exception as e:
        logger.warning(f"プロファイル情報の抽出中にエラーが発生: {str(e)}")
        return "未定義"

def get_weight(element):
    """部材の重量情報を抽出"""
    try:
        # 材料プロパティから情報を取得
        material = element.HasAssociations
        for association in material:
            if association.is_a("IfcRelAssociatesMaterial"):
                material_select = association.RelatingMaterial
                if hasattr(material_select, "MaterialProperties"):
                    for props in material_select.MaterialProperties:
                        if props.is_a("IfcMechanicalMaterialProperties"):
                            if hasattr(props, "SpecificGravity"):
                                return f"{props.SpecificGravity}kg"

        # プロパティセットから重量情報を検索
        for rel in element.IsDefinedBy:
            if rel.is_a("IfcRelDefinesByProperties"):
                property_set = rel.RelatingPropertyDefinition
                if property_set.is_a("IfcPropertySet"):
                    for prop in property_set.HasProperties:
                        if any(keyword in prop.Name.lower() for keyword in ["weight", "mass", "重量", "質量"]):
                            if hasattr(prop, "NominalValue"):
                                value = prop.NominalValue.wrappedValue
                                if isinstance(value, (int, float)):
                                    return f"{value}kg"
                                return str(value)

        return "未定義"
    except Exception as e:
        logger.warning(f"重量情報の抽出中にエラーが発生: {str(e)}")
        return "未定義"

def get_length(element):
    """部材の長さ情報を抽出"""
    try:
        # 数量セットから情報を取得
        for rel in element.IsDefinedBy:
            if rel.is_a("IfcRelDefinesByProperties"):
                props = rel.RelatingPropertyDefinition
                if props.is_a("IfcElementQuantity"):
                    for quantity in props.Quantities:
                        if quantity.is_a("IfcQuantityLength"):
                            return f"{int(quantity.LengthValue)}mm"  # HTMLでの表示用にmmを保持

        # プロパティセットから長さ情報を検索
        for rel in element.IsDefinedBy:
            if rel.is_a("IfcRelDefinesByProperties"):
                property_set = rel.RelatingPropertyDefinition
                if property_set.is_a("IfcPropertySet"):
                    for prop in property_set.HasProperties:
                        if any(keyword in prop.Name.lower() for keyword in ["length", "長さ"]):
                            if hasattr(prop, "NominalValue"):
                                value = prop.NominalValue.wrappedValue
                                if isinstance(value, (int, float)):
                                    return f"{int(value)}mm"  # HTMLでの表示用にmmを保持
                                return str(value)

        # 形状情報から長さを計算する試み
        if hasattr(element, "Representation"):
            representation = element.Representation
            if representation:
                for rep in representation.Representations:
                    if rep.RepresentationIdentifier == 'Body':
                        for item in rep.Items:
                            if item.is_a('IfcExtrudedAreaSolid'):
                                depth = item.Depth
                                return f"{int(depth)}mm"  # HTMLでの表示用にmmを保持

        return "未定義"
    except Exception as e:
        logger.warning(f"長さ情報の抽出中にエラーが発生: {str(e)}")
        return "未定義"
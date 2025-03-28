import ifcopenshell
import logging
import os

logger = logging.getLogger(__name__)

def process_ifc_file(filepath):
    """
    IFCファイルを処理して部材情報を抽出する
    """
    if not os.path.exists(filepath):
        error_msg = f"IFCファイルが見つかりません: {filepath}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

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
                            return f"{int(quantity.LengthValue * 1000)}mm"  # メートルからミリメートルに変換

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
                                    return f"{int(value * 1000)}mm"  # メートルからミリメートルに変換
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
                                return f"{int(depth * 1000)}mm"  # メートルからミリメートルに変換

        return "未定義"
    except Exception as e:
        logger.warning(f"長さ情報の抽出中にエラーが発生: {str(e)}")
        return "未定義"
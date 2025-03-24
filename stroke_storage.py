# -*- coding: utf-8 -*-
# Copyright: Louis Liu <liury2015@outlook.com>
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
"""
笔迹数据存储模块 - 负责笔迹与卡片ID的绑定和持久化存储
"""

import json
import os
from aqt import mw
from aqt.utils import showInfo

# 笔迹数据存储路径
def get_stroke_data_path():
    """获取笔迹数据的存储路径"""
    # 使用Anki配置目录下的特定文件夹存储数据
    base_folder = os.path.join(mw.pm.profileFolder(), "ankidraw_strokes")
    # 确保目录存在
    if not os.path.exists(base_folder):
        os.makedirs(base_folder)
        print(f"Debug - 笔迹存储: 创建数据目录 {base_folder}")
    return base_folder

# 向后兼容的保存函数，将数据同时保存到正面和全部笔迹
def save_stroke_data(card_id, stroke_data):
    """保存特定卡片的笔迹数据（向后兼容函数）
    
    参数:
    card_id -- 卡片ID
    stroke_data -- 笔迹数据JSON字符串
    """
    # 同时保存到正面和全部，确保兼容性
    save_front_stroke_data(card_id, stroke_data)
    return save_all_stroke_data(card_id, stroke_data)

# 保存正面笔迹
def save_front_stroke_data(card_id, stroke_data, window_width=None, window_height=None):
    """保存特定卡片正面的笔迹数据
    
    参数:
    card_id -- 卡片ID
    stroke_data -- 笔迹数据JSON字符串
    window_width -- 保存时窗口宽度（可选）
    window_height -- 保存时窗口高度（可选）
    """
    try:
        # 确保是字符串类型的card_id
        card_id = str(card_id)
        
        # 获取存储路径
        base_folder = get_stroke_data_path()
        stroke_file = os.path.join(base_folder, f"card_{card_id}_front.json")
        
        print(f"Debug - 保存正面笔迹: 准备保存到文件 {stroke_file}")
        
        # 如果提供了窗口大小信息，将其添加到笔迹数据中
        if window_width is not None and window_height is not None:
            try:
                # 解析JSON数据
                stroke_data_obj = json.loads(stroke_data)
                # 添加窗口尺寸
                stroke_data_obj['window_size'] = {
                    'width': window_width,
                    'height': window_height
                }
                # 重新序列化
                stroke_data = json.dumps(stroke_data_obj)
                print(f"Debug - 保存正面笔迹: 添加窗口大小信息 宽={window_width}, 高={window_height}")
            except Exception as e:
                print(f"添加窗口大小信息时出错: {e}")
                import traceback
                traceback.print_exc()
        
        # 保存数据
        with open(stroke_file, "w", encoding="utf-8") as f:
            f.write(stroke_data)
            
        print(f"Debug - 保存正面笔迹: 已成功写入文件 {stroke_file}, 数据长度={len(stroke_data)}")
        return True
    except Exception as e:
        print(f"保存正面笔迹数据时出错: {e}")
        import traceback
        traceback.print_exc()
        return False

# 保存全部笔迹
def save_all_stroke_data(card_id, stroke_data, window_width=None, window_height=None):
    """保存特定卡片的全部笔迹数据
    
    参数:
    card_id -- 卡片ID
    stroke_data -- 笔迹数据JSON字符串
    window_width -- 保存时窗口宽度（可选）
    window_height -- 保存时窗口高度（可选）
    """
    try:
        # 确保是字符串类型的card_id
        card_id = str(card_id)
        
        # 获取存储路径
        base_folder = get_stroke_data_path()
        stroke_file = os.path.join(base_folder, f"card_{card_id}_all.json")
        
        # 尝试合并正面笔迹和当前笔迹
        try:
            # 先获取正面笔迹数据
            front_data = load_front_stroke_data(card_id)
            
            if front_data and front_data != stroke_data:
                print(f"Debug - 保存全部笔迹: 尝试合并正面笔迹")
                # 解析两份数据
                front_strokes = json.loads(front_data)
                current_strokes = json.loads(stroke_data)
                
                # 确保两者都有预期的结构
                if (isinstance(front_strokes, dict) and isinstance(current_strokes, dict) and
                    'arrays_of_points' in front_strokes and 'arrays_of_points' in current_strokes and
                    'line_type_history' in front_strokes and 'line_type_history' in current_strokes):
                    
                    # 如果当前笔迹中没有保存正面笔迹的内容，则合并它们
                    # 检查是否已经包含正面笔迹，通过比较数组长度
                    if len(current_strokes['arrays_of_points']) < len(front_strokes['arrays_of_points']):
                        # 合并笔迹数据
                        current_strokes['arrays_of_points'] = front_strokes['arrays_of_points'] + current_strokes['arrays_of_points']
                        current_strokes['line_type_history'] = front_strokes['line_type_history'] + current_strokes['line_type_history']
                        
                        # 如果有书法笔画数据，也合并它们
                        if 'strokes' in front_strokes and 'strokes' in current_strokes:
                            current_strokes['strokes'] = front_strokes['strokes'] + current_strokes['strokes']
                        
                        # 将合并后的数据转换回字符串
                        stroke_data = json.dumps(current_strokes)
                        print(f"Debug - 保存全部笔迹: 成功合并正面笔迹，合并后数据长度={len(stroke_data)}")
        except Exception as e:
            print(f"保存全部笔迹时合并数据出错: {e}")
            import traceback
            traceback.print_exc()
        
        # 如果提供了窗口大小信息，将其添加到笔迹数据中
        if window_width is not None and window_height is not None:
            try:
                # 解析JSON数据
                stroke_data_obj = json.loads(stroke_data)
                # 添加窗口尺寸
                stroke_data_obj['window_size'] = {
                    'width': window_width,
                    'height': window_height
                }
                # 重新序列化
                stroke_data = json.dumps(stroke_data_obj)
                print(f"Debug - 保存全部笔迹: 添加窗口大小信息 宽={window_width}, 高={window_height}")
            except Exception as e:
                print(f"添加窗口大小信息时出错: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"Debug - 保存全部笔迹: 准备保存到文件 {stroke_file}")
        
        # 保存数据
        with open(stroke_file, "w", encoding="utf-8") as f:
            f.write(stroke_data)
            
        print(f"Debug - 保存全部笔迹: 已成功写入文件 {stroke_file}, 数据长度={len(stroke_data)}")
        return True
    except Exception as e:
        print(f"保存全部笔迹数据时出错: {e}")
        import traceback
        traceback.print_exc()
        return False

# 获取正面笔迹的窗口大小
def get_front_window_size(card_id):
    """从正面笔迹数据中获取窗口大小
    
    参数:
    card_id -- 卡片ID
    
    返回:
    元组 (width, height)，如果没有则返回 (None, None)
    """
    try:
        # 获取正面笔迹数据
        front_strokes = load_front_stroke_data(card_id)
        if front_strokes:
            try:
                data = json.loads(front_strokes)
                if 'window_size' in data:
                    width = data['window_size'].get('width')
                    height = data['window_size'].get('height')
                    if width is not None and height is not None:
                        print(f"Debug - 获取正面笔迹窗口大小: 宽={width}, 高={height}")
                        return (width, height)
            except Exception as e:
                print(f"解析正面笔迹获取窗口大小时出错: {e}")
        
        # 没有找到窗口大小信息
        print(f"Debug - 获取正面笔迹窗口大小: 未找到窗口大小信息")
        return (None, None)
    except Exception as e:
        print(f"获取正面笔迹窗口大小时出错: {e}")
        import traceback
        traceback.print_exc()
        return (None, None)

# 获取全部笔迹的窗口大小
def get_all_window_size(card_id):
    """从全部笔迹数据中获取窗口大小
    
    参数:
    card_id -- 卡片ID
    
    返回:
    元组 (width, height)，如果没有则返回 (None, None)
    """
    try:
        # 获取全部笔迹数据
        all_strokes = load_all_stroke_data(card_id)
        if all_strokes:
            try:
                data = json.loads(all_strokes)
                if 'window_size' in data:
                    width = data['window_size'].get('width')
                    height = data['window_size'].get('height')
                    if width is not None and height is not None:
                        print(f"Debug - 获取全部笔迹窗口大小: 宽={width}, 高={height}")
                        return (width, height)
            except Exception as e:
                print(f"解析全部笔迹获取窗口大小时出错: {e}")
        
        # 没有找到窗口大小信息
        print(f"Debug - 获取全部笔迹窗口大小: 未找到窗口大小信息")
        return (None, None)
    except Exception as e:
        print(f"获取全部笔迹窗口大小时出错: {e}")
        import traceback
        traceback.print_exc()
        return (None, None)

# 向后兼容的窗口大小获取函数
def get_window_size(card_id):
    """从笔迹数据中获取窗口大小（向后兼容函数）
    
    参数:
    card_id -- 卡片ID
    
    返回:
    元组 (width, height)，如果没有则返回 (None, None)
    """
    # 优先获取全部笔迹的窗口大小
    width, height = get_all_window_size(card_id)
    if width is not None and height is not None:
        return (width, height)
    
    # 如果没有全部笔迹的窗口大小，尝试获取正面笔迹的窗口大小
    return get_front_window_size(card_id)

# 向后兼容的加载函数，优先加载全部笔迹，如果没有则加载正面笔迹
def load_stroke_data(card_id):
    """加载特定卡片的笔迹数据（向后兼容函数）
    
    参数:
    card_id -- 卡片ID
    
    返回:
    笔迹数据JSON字符串，如果没有则返回None
    """
    # 优先尝试加载全部笔迹，如果没有则加载正面笔迹
    all_strokes = load_all_stroke_data(card_id)
    if all_strokes:
        return all_strokes
    
    return load_front_stroke_data(card_id)

# 加载正面笔迹
def load_front_stroke_data(card_id):
    """加载特定卡片正面的笔迹数据
    
    参数:
    card_id -- 卡片ID
    
    返回:
    笔迹数据JSON字符串，如果没有则返回None
    """
    try:
        # 确保是字符串类型的card_id
        card_id = str(card_id)
        
        # 获取存储路径
        base_folder = get_stroke_data_path()
        stroke_file = os.path.join(base_folder, f"card_{card_id}_front.json")
        
        print(f"Debug - 加载正面笔迹: 尝试从文件加载 {stroke_file}")
        
        # 检查文件是否存在
        if not os.path.exists(stroke_file):
            print(f"Debug - 加载正面笔迹: 文件不存在 {stroke_file}")
            # 尝试从老文件格式加载（向后兼容）
            legacy_file = os.path.join(base_folder, f"card_{card_id}.json")
            if os.path.exists(legacy_file):
                print(f"Debug - 加载正面笔迹: 尝试从旧格式文件加载 {legacy_file}")
                with open(legacy_file, "r", encoding="utf-8") as f:
                    stroke_data = f.read()
                print(f"Debug - 加载正面笔迹: 已从旧格式文件成功读取，数据长度={len(stroke_data)}")
                # 同时保存到新格式（迁移数据）
                save_front_stroke_data(card_id, stroke_data)
                return stroke_data
            return None
            
        # 加载数据
        with open(stroke_file, "r", encoding="utf-8") as f:
            stroke_data = f.read()
            
        print(f"Debug - 加载正面笔迹: 已成功读取文件 {stroke_file}, 数据长度={len(stroke_data)}")
        return stroke_data
    except Exception as e:
        print(f"加载正面笔迹数据时出错: {e}")
        import traceback
        traceback.print_exc()
        return None

# 加载全部笔迹
def load_all_stroke_data(card_id):
    """加载特定卡片的全部笔迹数据
    
    参数:
    card_id -- 卡片ID
    
    返回:
    笔迹数据JSON字符串，如果没有则返回None
    """
    try:
        # 确保是字符串类型的card_id
        card_id = str(card_id)
        
        # 获取存储路径
        base_folder = get_stroke_data_path()
        stroke_file = os.path.join(base_folder, f"card_{card_id}_all.json")
        
        print(f"Debug - 加载全部笔迹: 尝试从文件加载 {stroke_file}")
        
        # 检查文件是否存在
        if not os.path.exists(stroke_file):
            print(f"Debug - 加载全部笔迹: 文件不存在 {stroke_file}")
            # 尝试从老文件格式加载（向后兼容）
            legacy_file = os.path.join(base_folder, f"card_{card_id}.json")
            if os.path.exists(legacy_file):
                print(f"Debug - 加载全部笔迹: 尝试从旧格式文件加载 {legacy_file}")
                with open(legacy_file, "r", encoding="utf-8") as f:
                    stroke_data = f.read()
                print(f"Debug - 加载全部笔迹: 已从旧格式文件成功读取，数据长度={len(stroke_data)}")
                # 同时保存到新格式（迁移数据）
                save_all_stroke_data(card_id, stroke_data)
                return stroke_data
            return None
            
        # 加载数据
        with open(stroke_file, "r", encoding="utf-8") as f:
            stroke_data = f.read()
            
        print(f"Debug - 加载全部笔迹: 已成功读取文件 {stroke_file}, 数据长度={len(stroke_data)}")
        return stroke_data
    except Exception as e:
        print(f"加载全部笔迹数据时出错: {e}")
        import traceback
        traceback.print_exc()
        return None

def delete_stroke_data(card_id):
    """删除特定卡片的所有笔迹数据
    
    参数:
    card_id -- 卡片ID
    
    返回:
    是否成功删除
    """
    try:
        # 确保是字符串类型的card_id
        card_id = str(card_id)
        
        # 获取存储路径
        base_folder = get_stroke_data_path()
        front_file = os.path.join(base_folder, f"card_{card_id}_front.json")
        all_file = os.path.join(base_folder, f"card_{card_id}_all.json")
        legacy_file = os.path.join(base_folder, f"card_{card_id}.json")
        
        # 删除所有可能的文件
        for file_path in [front_file, all_file, legacy_file]:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Debug - 删除笔迹: 已删除文件 {file_path}")
        
        return True
    except Exception as e:
        print(f"删除笔迹数据时出错: {e}")
        import traceback
        traceback.print_exc()
        return False 
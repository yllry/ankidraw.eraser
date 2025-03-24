# -*- coding: utf-8 -*-
# Copyright: Louis Liu <liury2015@outlook.com>
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
"""
笔迹管理模块 - 提供笔迹的导入导出和管理功能
"""

import os
import json
import shutil
import time
import zipfile
import re
from aqt import mw
from aqt.qt import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QCheckBox, QFileDialog, QMessageBox, QProgressBar, Qt
from aqt.utils import showInfo, showWarning, askUser, tooltip
from anki.lang import _

# 导入语言模块
from . import lang

# 全局变量，控制是否保存笔迹
save_strokes_enabled = True

# 导入笔迹存储模块
from . import stroke_storage

def get_save_strokes_enabled():
    """获取是否启用笔迹保存"""
    global save_strokes_enabled
    # 从配置中加载设置
    if 'ankidraw_save_strokes_enabled' in mw.pm.profile:
        save_strokes_enabled = mw.pm.profile['ankidraw_save_strokes_enabled']
    return save_strokes_enabled

def set_save_strokes_enabled(enabled):
    """设置是否启用笔迹保存"""
    global save_strokes_enabled
    save_strokes_enabled = enabled
    # 保存设置到配置
    mw.pm.profile['ankidraw_save_strokes_enabled'] = enabled

def export_strokes(export_path=None):
    """
    导出所有笔迹数据到一个zip文件
    返回: 成功导出的文件路径，如果失败则返回None
    """
    try:
        # 获取笔迹数据文件夹
        strokes_folder = stroke_storage.get_stroke_data_path()
        
        # 如果文件夹不存在或者为空，提示用户
        if not os.path.exists(strokes_folder) or not os.listdir(strokes_folder):
            showInfo(lang.get_text("stroke_manager_import_no_files", "没有可导出的笔迹数据。"))
            return None
        
        # 如果没有指定导出路径，打开文件对话框让用户选择
        if not export_path:
            # 生成默认文件名，包含日期时间
            default_filename = f"AnkiDraw_Strokes_Backup_{time.strftime('%Y%m%d_%H%M%S')}.zip"
            export_path, _ = QFileDialog.getSaveFileName(
                None, 
                lang.get_text("stroke_manager_export_backup", "导出笔迹数据"), 
                os.path.join(os.path.expanduser("~"), default_filename),
                "ZIP文件 (*.zip)"
            )
            if not export_path:  # 用户取消
                return None
        
        # 确保文件扩展名是.zip
        if not export_path.lower().endswith('.zip'):
            export_path += '.zip'
        
        # 创建一个临时目录用于放置元数据
        temp_dir = os.path.join(strokes_folder, "temp_export")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        
        try:
            # 创建一个元数据文件，包含导出时间和版本信息
            metadata = {
                "export_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "version": "1.0",
                "profile": mw.pm.name
            }
            
            with open(os.path.join(temp_dir, "metadata.json"), "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # 创建zip文件
            with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 首先添加元数据文件
                zipf.write(os.path.join(temp_dir, "metadata.json"), "metadata.json")
                
                # 添加所有笔迹数据文件
                for root, _, files in os.walk(strokes_folder):
                    for file in files:
                        if file.endswith('.json') and not file == "metadata.json":
                            file_path = os.path.join(root, file)
                            # 将文件添加到zip中，但不包含原始路径
                            arcname = os.path.basename(file_path)
                            zipf.write(file_path, arcname)
        finally:
            # 清理临时目录
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        
        return export_path
    except Exception as e:
        showWarning(f"{lang.get_text('stroke_manager_clear_error', '导出笔迹数据时出错:')} {e}")
        return None

def import_strokes(import_path=None, overwrite=False):
    """
    从zip文件导入笔迹数据
    参数:
        import_path: zip文件路径，如果为None则打开文件对话框
        overwrite: 是否覆盖已存在的笔迹数据
    返回: 成功导入的文件数量，如果失败则返回0
    """
    try:
        # 如果没有指定导入路径，打开文件对话框让用户选择
        if not import_path:
            import_path, _ = QFileDialog.getOpenFileName(
                None, 
                lang.get_text("stroke_manager_import_backup", "导入笔迹数据"), 
                os.path.expanduser("~"),
                "ZIP文件 (*.zip)"
            )
            if not import_path:  # 用户取消
                return 0
        
        # 获取笔迹数据文件夹
        strokes_folder = stroke_storage.get_stroke_data_path()
        
        # 检查文件是否存在
        if not os.path.exists(import_path):
            showWarning(f"{lang.get_text('file_not_found', '找不到文件:')} {import_path}")
            return 0
        
        # 创建一个临时目录用于解压文件
        temp_dir = os.path.join(strokes_folder, "temp_import")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)
        
        try:
            # 解压文件到临时目录
            with zipfile.ZipFile(import_path, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # 检查元数据文件
            metadata_path = os.path.join(temp_dir, "metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                    # 可以在这里进行版本检查等操作
                    if "version" in metadata and "export_time" in metadata:
                        tooltip(f"{lang.get_text('importing_backup', '正在导入')} {metadata['export_time']} {lang.get_text('backup_of_traces', '备份的笔迹数据...')}")
            
            # 计算导入的文件数量
            imported_count = 0
            
            # 复制所有笔迹数据文件到目标目录
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    if file.endswith('.json') and file != "metadata.json":
                        file_path = os.path.join(root, file)
                        target_path = os.path.join(strokes_folder, file)
                        
                        # 检查目标文件是否已存在
                        if os.path.exists(target_path) and not overwrite:
                            # 如果不覆盖，跳过已存在的文件
                            continue
                        
                        # 复制文件
                        shutil.copy2(file_path, target_path)
                        imported_count += 1
            
            return imported_count
        finally:
            # 清理临时目录
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    except Exception as e:
        showWarning(f"{lang.get_text('stroke_manager_clear_error', '导入笔迹数据时出错:')} {e}")
        return 0

def count_stroke_files():
    """计算笔迹文件数量"""
    try:
        strokes_folder = stroke_storage.get_stroke_data_path()
        if not os.path.exists(strokes_folder):
            return 0
        
        count = 0
        for file in os.listdir(strokes_folder):
            if file.endswith('.json'):
                count += 1
        
        return count
    except:
        return 0

def get_strokes_folder_size():
    """获取笔迹文件夹大小(MB)"""
    try:
        strokes_folder = stroke_storage.get_stroke_data_path()
        if not os.path.exists(strokes_folder):
            return 0
        
        total_size = 0
        for root, _, files in os.walk(strokes_folder):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
        
        # 转换为MB
        return total_size / (1024 * 1024)
    except:
        return 0

def find_invalid_strokes():
    """
    查找失效的笔迹数据文件（对应的卡片已删除）
    返回: 失效笔迹文件的列表
    """
    try:
        # 获取笔迹数据文件夹
        strokes_folder = stroke_storage.get_stroke_data_path()
        if not os.path.exists(strokes_folder):
            return []
        
        # 获取所有笔迹文件
        stroke_files = []
        for file in os.listdir(strokes_folder):
            if file.endswith('.json'):
                stroke_files.append(file)
        
        # 提取所有卡片ID
        card_ids = set()
        for file in stroke_files:
            # 文件名格式为 card_ID_type.json
            match = re.match(r"card_(\d+)_(front|all)\.json", file)
            if match:
                card_ids.add(int(match.group(1)))
        
        # 检查卡片是否存在
        invalid_files = []
        for card_id in card_ids:
            try:
                card = mw.col.get_card(card_id)
                if card is None:
                    # 卡片不存在，添加相关的笔迹文件到失效列表
                    for file in stroke_files:
                        if file.startswith(f"card_{card_id}_"):
                            invalid_files.append(file)
            except Exception:
                # 卡片不存在或获取卡片出错，添加相关的笔迹文件到失效列表
                for file in stroke_files:
                    if file.startswith(f"card_{card_id}_"):
                        invalid_files.append(file)
        
        return invalid_files
    except Exception as e:
        showWarning(f"{lang.get_text('stroke_manager_clear_error', '查找失效笔迹时出错:')} {e}")
        return []

def clean_invalid_strokes(files_to_clean):
    """
    清理失效的笔迹数据文件
    参数: 要清理的文件列表
    返回: 成功清理的文件数量
    """
    try:
        strokes_folder = stroke_storage.get_stroke_data_path()
        cleaned_count = 0
        
        for file in files_to_clean:
            file_path = os.path.join(strokes_folder, file)
            if os.path.exists(file_path):
                os.remove(file_path)
                cleaned_count += 1
        
        return cleaned_count
    except Exception as e:
        # 针对"No such card"错误提供更友好的错误信息
        if "No such card" in str(e):
            showWarning(lang.get_text("stroke_manager_card_not_exist", "这些卡片已不存在，请使用「清理失效笔迹」功能来清除相关笔迹数据。"))
        else:
            showWarning(f"{lang.get_text('stroke_manager_clear_error', '清理失效笔迹时出错:')} {e}")
        return 0


class StrokeManagerDialog(QDialog):
    """笔迹管理对话框"""
    def __init__(self, parent=None):
        super(StrokeManagerDialog, self).__init__(parent)
        self.setWindowTitle(lang.get_text("stroke_manager_title", "AnkiDraw 笔迹管理"))
        self.setMinimumWidth(500)
        self.setup_ui()
        self.update_stats()
    
    def setup_ui(self):
        """设置对话框界面"""
        layout = QVBoxLayout()
        
        # 统计信息
        self.stats_label = QLabel(lang.get_text("stroke_manager_loading_stats", "正在加载笔迹统计..."))
        layout.addWidget(self.stats_label)
        
        # 笔迹保存控制选项
        self.save_enabled_cb = QCheckBox(lang.get_text("stroke_manager_enable_save", "启用笔迹保存"))
        self.save_enabled_cb.setChecked(get_save_strokes_enabled())
        self.save_enabled_cb.toggled.connect(self.toggle_save_enabled)
        layout.addWidget(self.save_enabled_cb)
        
        # 导出备份按钮
        export_layout = QHBoxLayout()
        export_btn = QPushButton(lang.get_text("stroke_manager_export_backup", "一键导出笔迹备份"))
        export_btn.clicked.connect(self.export_strokes)
        export_layout.addWidget(export_btn)
        
        # 导入按钮
        import_btn = QPushButton(lang.get_text("stroke_manager_import_backup", "导入笔迹备份"))
        import_btn.clicked.connect(self.import_strokes)
        export_layout.addWidget(import_btn)
        layout.addLayout(export_layout)
        
        # 笔迹清理按钮
        clean_layout = QHBoxLayout()
        
        # 添加失效笔迹清理按钮
        invalid_btn = QPushButton(lang.get_text("stroke_manager_clean_invalid", "清理失效笔迹"))
        invalid_btn.clicked.connect(self.clean_invalid_strokes)
        invalid_btn.setToolTip(lang.get_text("stroke_manager_clean_tooltip", "检查并清理已删除卡片的笔迹数据，释放存储空间"))
        clean_layout.addWidget(invalid_btn, 1)  # 设置伸缩因子为1，使其占据一半宽度
        
        # 清空所有笔迹按钮 - 设置为红色按钮
        clear_btn = QPushButton(lang.get_text("stroke_manager_clear_all", "清空所有笔迹"))
        clear_btn.clicked.connect(self.clear_all_strokes)
        clear_btn.setStyleSheet("color: red; font-size: 10pt; padding: 3px;")
        clear_btn.setToolTip(lang.get_text("stroke_manager_clear_warning", "警告：此操作将删除所有笔迹数据！"))
        # 删除最大宽度限制，让其与另一个按钮大小相同
        clean_layout.addWidget(clear_btn, 1)  # 设置伸缩因子为1，使其占据一半宽度
        
        layout.addLayout(clean_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 关闭按钮
        close_btn = QPushButton(lang.get_text("stroke_manager_close", "关闭"))
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
    
    def update_stats(self):
        """更新统计信息"""
        file_count = count_stroke_files()
        folder_size = get_strokes_folder_size()
        
        stats_text = f"{lang.get_text('stroke_manager_file_count', '笔迹文件数量: ')}{file_count} {lang.get_text('file_count_suffix', '个')}\n"
        stats_text += f"{lang.get_text('stroke_manager_data_size', '笔迹数据大小: ')}{folder_size:.2f} MB\n"
        stats_text += f"{lang.get_text('stroke_manager_save_status', '笔迹保存状态: ')}{lang.get_text('stroke_manager_enabled', '已启用') if get_save_strokes_enabled() else lang.get_text('stroke_manager_disabled', '已禁用')}\n"
        stats_text += f"{lang.get_text('stroke_manager_storage_path', '笔迹存储路径: ')}{stroke_storage.get_stroke_data_path()}"
        
        self.stats_label.setText(stats_text)
    
    def toggle_save_enabled(self, enabled):
        """切换笔迹保存状态"""
        set_save_strokes_enabled(enabled)
        self.update_stats()
        tooltip(lang.get_text('stroke_manager_save_enabled_tooltip' if enabled else 'stroke_manager_save_disabled_tooltip', 
                             f"笔迹保存功能已{'启用' if enabled else '禁用'}"))
    
    def export_strokes(self):
        """导出笔迹数据"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(10)
        
        export_path = export_strokes()
        
        self.progress_bar.setValue(100)
        self.progress_bar.setVisible(False)
        
        if export_path:
            QMessageBox.information(self, lang.get_text("stroke_manager_export_success", "导出成功"), 
                                  f"{lang.get_text('stroke_manager_export_success_message', '笔迹数据已成功导出到:')}\n{export_path}")
    
    def import_strokes(self):
        """导入笔迹数据"""
        # 询问是否覆盖已存在的文件
        overwrite = QMessageBox.question(self, lang.get_text("stroke_manager_import_options", "导入选项"), 
                                       lang.get_text("stroke_manager_overwrite_question", "是否覆盖已存在的笔迹文件？"),
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                       QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(10)
        
        imported_count = import_strokes(overwrite=overwrite)
        
        self.progress_bar.setValue(100)
        self.progress_bar.setVisible(False)
        
        if imported_count > 0:
            QMessageBox.information(self, lang.get_text("stroke_manager_import_success", "导入成功"), 
                                  f"{lang.get_text('stroke_manager_import_success_message', '成功导入 ')}{imported_count}{lang.get_text('stroke_manager_import_files', ' 个笔迹文件')}")
            self.update_stats()
        else:
            QMessageBox.information(self, lang.get_text("stroke_manager_import_success", "导入结果"), 
                                   lang.get_text("stroke_manager_import_no_files", "没有导入任何文件"))
    
    def clean_invalid_strokes(self):
        """清理失效笔迹"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(10)
        
        # 查找失效笔迹
        invalid_files = find_invalid_strokes()
        
        self.progress_bar.setValue(50)
        
        if not invalid_files:
            self.progress_bar.setVisible(False)
            QMessageBox.information(self, lang.get_text("stroke_manager_check_complete", "检查完成"), 
                                  lang.get_text("stroke_manager_no_invalid", "没有发现失效笔迹数据。"))
            return
        
        # 准备显示的信息
        invalid_count = len(invalid_files)
        match_ids = set()
        for file in invalid_files:
            match = re.match(r"card_(\d+)_(front|all)\.json", file)
            if match:
                match_ids.add(match.group(1))
        
        # 显示确认对话框
        message = f"{lang.get_text('stroke_manager_found_invalid', '发现 ')}{invalid_count}{lang.get_text('stroke_manager_invalid_files', ' 个失效笔迹文件，涉及 ')}{len(match_ids)}{lang.get_text('stroke_manager_deleted_cards', ' 张已删除的卡片。')}\n\n"
        
        # 显示一些文件名作为示例
        if invalid_count > 5:
            examples = invalid_files[:5]
            message += f"{lang.get_text('stroke_manager_some_invalid_files', '部分失效文件：')}\n" + "\n".join(examples) + "\n...\n\n"
        else:
            message += f"{lang.get_text('stroke_manager_invalid_files_list', '失效文件：')}\n" + "\n".join(invalid_files) + "\n\n"
        
        message += lang.get_text("stroke_manager_clean_question", "是否清理这些失效笔迹文件？")
        
        # 询问用户是否清理
        if QMessageBox.question(self, lang.get_text("stroke_manager_invalid_cleanup", "失效笔迹清理"), 
                               message,
                               QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                               QMessageBox.StandardButton.Yes) == QMessageBox.StandardButton.Yes:
            
            # 清理失效笔迹
            cleaned_count = clean_invalid_strokes(invalid_files)
            
            self.progress_bar.setValue(100)
            self.progress_bar.setVisible(False)
            
            # 更新统计信息
            self.update_stats()
            
            QMessageBox.information(self, lang.get_text("stroke_manager_cleanup_complete", "清理完成"), 
                                  f"{lang.get_text('stroke_manager_cleaned_files', '成功清理了 ')}{cleaned_count}{lang.get_text('stroke_manager_cleaned_files_end', ' 个失效笔迹文件。')}")
        else:
            self.progress_bar.setVisible(False)
    
    def clear_all_strokes(self):
        """清空所有笔迹"""
        if askUser(lang.get_text("stroke_manager_clear_warning_message", "<span style='color: red; font-weight: bold;'>警告：此操作无法撤销！</span><br><br>确定要删除所有保存的笔迹数据吗？")):
            try:
                # 获取笔迹数据文件夹
                strokes_folder = stroke_storage.get_stroke_data_path()
                
                # 如果文件夹存在，删除并重建
                if os.path.exists(strokes_folder):
                    # 先备份当前文件
                    backup_path = export_strokes(os.path.join(
                        os.path.expanduser("~"), 
                        f"AnkiDraw_Strokes_Auto_Backup_{time.strftime('%Y%m%d_%H%M%S')}.zip"
                    ))
                    
                    shutil.rmtree(strokes_folder)
                    os.makedirs(strokes_folder)
                
                showInfo(f"{lang.get_text('stroke_manager_clear_success', '所有笔迹数据已成功清除。')}\n"
                         f"{lang.get_text('stroke_manager_backup_saved', '备份已保存到: ') + backup_path if backup_path else lang.get_text('stroke_manager_no_backup', '未创建备份。')}")
                self.update_stats()
            except Exception as e:
                showWarning(f"{lang.get_text('stroke_manager_clear_error', '清除笔迹数据时出错: ')}{e}")

def show_stroke_manager():
    """显示笔迹管理对话框"""
    dialog = StrokeManagerDialog(mw)
    dialog.exec() 
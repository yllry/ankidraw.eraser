# -*- coding: utf-8 -*-
# Copyright: louis Liu <liury2015@outlook.com>
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
"""
快捷键管理模块 for AnkiDraw addon.
提供界面用于控制工具栏上各个工具按钮的快捷键设置。
"""

import os
import json
import time
from aqt import mw
from aqt.qt import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox, 
                   QTableWidget, QTableWidgetItem, QKeySequence, QKeySequenceEdit, QHeaderView, Qt)
from aqt.qt import pyqtSlot as slot

# 导入语言模块
from . import lang

# 添加日志功能
def log_debug(message):
    """
    将调试信息写入日志文件
    """
    try:
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'addon_logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'hotkey_debug.log')
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        print(f"Error writing to log: {e}")

# Anki默认快捷键列表，用于冲突检测
anki_default_shortcuts = [
    "F1", "Ctrl+T", "Y", "Shift+S", "D", "A", "B", "/", "F", "Ctrl+Z", "Ctrl+Q", 
    "Ctrl+E", "Ctrl+I", "Ctrl+P", "Ctrl+Shift+P", "Ctrl+Shift+N", "Space", "Enter", 
    "U", "C", "O", "E", "1", "2", "3", "4", "S", "*", "-", "Shift++", "=", "Shift+2", 
    "@", "Shift+1", "!", "Del", "о", "R", "Shift+V", "V", "Ctrl+Enter", "Ctrl+N", 
    "Ctrl+D", "Ctrl+L", "Alt+F4", "Ctrl+B", "Ctrl+I", "Ctrl+U", "Ctrl+Shift+=", 
    "Ctrl+=", "Ctrl+R", "F7", "F8", "Ctrl+Shift+C", "F3", "F5", "Ctrl+T,T", 
    "Ctrl+T,E", "Ctrl+T,M", "Ctrl+Shift+X", "Ctrl+Shift+M", "Ctrl+A", "Ctrl+Shift+A", 
    "Ctrl+Alt+F", "Ctrl+F", "Ctrl+Shift+R", "Ctrl+Shift+F", "Ctrl+Shift+L", 
    "Ctrl+Shift+P", "Home", "Ctrl+P", "Ctrl+N", "End", "Ctrl+Shift+I", "Ctrl+E", 
    "Ctrl+K", "Ctrl+D", "Ctrl+Shift+T", "Ctrl+Alt+T", "Del"
]

# 默认工具快捷键设置
default_hotkey_config = {
    # 绘图工具
    'visibility': '',      # 绘图工具按钮
    'eraser': '',          # 橡皮擦按钮
    'line': '',            # 直线工具按钮
    'rectangle': '',       # 矩形工具按钮
    'undo': '',            # 撤销按钮
    'clear': '',           # 清除画布按钮
    'fullscreen': '',      # 全屏切换按钮
    'restore_window_size': ''  # 恢复窗口大小按钮
}

# 当前快捷键配置
hotkey_config = dict(default_hotkey_config)

class HotkeyConfigDialog(QDialog):
    """
    快捷键配置对话框
    """
    def __init__(self, parent=None):
        super(HotkeyConfigDialog, self).__init__(parent)
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """
        设置对话框UI
        """
        self.setWindowTitle(lang.get_text("dialog_hotkey_config", "快捷键设置"))
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        main_layout = QVBoxLayout()
        
        # 说明标签
        info_label = QLabel(lang.get_text("dialog_hotkey_info", 
            "为工具栏上的工具设置快捷键。设置快捷键时，请点击对应工具的快捷键单元格并按下您想要的按键组合。"))
        info_label.setWordWrap(True)
        main_layout.addWidget(info_label)
        
        # 警告标签
        warning_label = QLabel(lang.get_text("dialog_hotkey_warning", 
            "注意：请避免使用与Anki默认快捷键冲突的组合，否则将无法设置成功。"))
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet("color: red;")
        main_layout.addWidget(warning_label)
        
        # 工具快捷键表格
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([
            lang.get_text("dialog_hotkey_tool", "工具"),
            lang.get_text("dialog_hotkey_shortcut", "快捷键"),
            lang.get_text("dialog_hotkey_action", "操作")
        ])
        try:
            # Qt6
            self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        except AttributeError:
            # Qt5
            self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        # 填充表格
        tool_names = {
            'visibility': lang.get_text("dialog_drawing_tool_button", "绘图工具"),
            'eraser': lang.get_text("dialog_eraser_button", "橡皮擦"),
            'line': lang.get_text("dialog_line_tool_button", "直线工具"),
            'rectangle': lang.get_text("dialog_rectangle_tool_button", "矩形工具"),
            'undo': lang.get_text("dialog_undo_button", "撤销"),
            'clear': lang.get_text("dialog_clear_canvas_button", "清除画布"),
            'fullscreen': lang.get_text("dialog_fullscreen_toggle_button", "全屏切换"),
            'restore_window_size': lang.get_text("dialog_restore_window_size_button", "恢复窗口大小")
        }
        
        self.table.setRowCount(len(tool_names))
        self.key_edits = {}
        
        row = 0
        for tool_id, tool_name in tool_names.items():
            # 工具名称
            name_item = QTableWidgetItem(tool_name)
            try:
                # Qt6
                name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            except AttributeError:
                # Qt5
                name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, name_item)
            
            # 快捷键编辑器
            key_edit = QKeySequenceEdit()
            self.key_edits[tool_id] = key_edit
            self.table.setCellWidget(row, 1, key_edit)
            
            # 清除按钮
            clear_button = QPushButton(lang.get_text("dialog_hotkey_clear", "清除"))
            clear_button.clicked.connect(lambda checked, r=row: self.clear_shortcut(r))
            self.table.setCellWidget(row, 2, clear_button)
            
            row += 1
        
        main_layout.addWidget(self.table)
        
        # 按钮区域
        buttons_layout = QHBoxLayout()
        
        # 重置按钮
        reset_btn = QPushButton(lang.get_text("dialog_reset_all", "重置所有"))
        reset_btn.clicked.connect(self.reset_all)
        buttons_layout.addWidget(reset_btn)
        
        # 弹性空间
        buttons_layout.addStretch()
        
        # 确定按钮
        ok_btn = QPushButton(lang.get_text("ok_button", "确定"))
        ok_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(ok_btn)
        
        # 取消按钮
        cancel_btn = QPushButton(lang.get_text("cancel_button", "取消"))
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        main_layout.addLayout(buttons_layout)
        
        self.setLayout(main_layout)
    
    def load_settings(self):
        """
        加载快捷键设置到UI
        """
        for tool_id, key_edit in self.key_edits.items():
            shortcut = hotkey_config.get(tool_id, '')
            if shortcut:
                key_edit.setKeySequence(QKeySequence(shortcut))
    
    def save_settings(self):
        """
        保存UI设置到配置
        """
        global hotkey_config
        log_debug("Saving hotkey settings from dialog")
        
        # 检查快捷键冲突
        has_conflict = False
        conflict_shortcuts = []
        
        for tool_id, key_edit in self.key_edits.items():
            shortcut = key_edit.keySequence().toString()
            
            # 检查快捷键是否与Anki默认快捷键冲突
            if shortcut and shortcut in anki_default_shortcuts:
                has_conflict = True
                conflict_shortcuts.append((tool_id, shortcut))
        
        # 如果有冲突，显示警告并返回False（不保存设置）
        if has_conflict:
            from aqt.utils import showWarning
            conflict_msg = ""
            for tool_id, shortcut in conflict_shortcuts:
                tool_name = self.table.item(list(self.key_edits.keys()).index(tool_id), 0).text()
                msg = lang.get_text("dialog_hotkey_conflict", "快捷键 '{0}' 与Anki默认快捷键冲突，已被忽略。")
                msg = msg.replace("{0}", shortcut)
                conflict_msg += f"{tool_name}: {msg}\n"
            
            # 添加提示信息
            conflict_msg += "\n" + lang.get_text("dialog_hotkey_conflict_retry", "请修改这些快捷键后再次点击确定。")
            showWarning(conflict_msg)
            
            # 清除冲突的快捷键
            for tool_id, _ in conflict_shortcuts:
                self.key_edits[tool_id].clear()
            
            return False
        
        # 保存设置
        for tool_id, key_edit in self.key_edits.items():
            shortcut = key_edit.keySequence().toString()
            old_value = hotkey_config.get(tool_id, '')
            hotkey_config[tool_id] = shortcut
            
            if old_value != shortcut:
                log_debug(f"Changed hotkey for {tool_id}: {old_value} -> {shortcut}")
        
        # 保存到Anki配置
        save_hotkey_config()
        
        # 立即应用设置
        apply_hotkey_config()
        log_debug("Applied hotkey settings immediately")
        return True
    
    def clear_shortcut(self, row):
        """
        清除指定行的快捷键
        """
        tool_id = list(self.key_edits.keys())[row]
        key_edit = self.key_edits[tool_id]
        key_edit.clear()
    
    def reset_all(self):
        """
        重置所有快捷键
        """
        for key_edit in self.key_edits.values():
            key_edit.clear()
    
    def accept(self):
        """
        确定按钮点击处理
        """
        # 只有在成功保存设置时才关闭对话框
        if self.save_settings():
            super(HotkeyConfigDialog, self).accept()

def load_hotkey_config():
    """
    从Anki配置加载快捷键配置
    """
    global hotkey_config
    
    try:
        saved_config = mw.pm.profile.get('hotkey_config', None)
        log_debug(f"Loading hotkey config: {saved_config}")
        
        if saved_config:
            for key, value in saved_config.items():
                if key in hotkey_config:
                    hotkey_config[key] = value
            
            # 立即应用加载的配置
            apply_hotkey_config()
            log_debug(f"Applied hotkey config: {hotkey_config}")
        else:
            log_debug("No saved hotkey config found, using defaults")
    except Exception as e:
        log_debug(f"Error loading hotkey config: {e}")
        print(f"Error loading hotkey config: {e}")

def save_hotkey_config():
    """
    保存快捷键配置到Anki
    """
    try:
        log_debug(f"Saving hotkey config: {hotkey_config}")
        mw.pm.profile['hotkey_config'] = dict(hotkey_config)
        # 确保配置被立即写入
        mw.pm.save()
        log_debug("Hotkey config saved successfully")
    except Exception as e:
        log_debug(f"Error saving hotkey config: {e}")
        print(f"Error saving hotkey config: {e}")

def apply_hotkey_config():
    """
    应用快捷键配置
    """
    from . import execute_js
    
    # 构建JavaScript代码来设置快捷键
    js_code = """
    // 清除所有现有的快捷键处理器
    if (window.ankidraw_hotkey_handlers) {
        for (let handler of window.ankidraw_hotkey_handlers) {
            document.removeEventListener('keydown', handler);
        }
    }
    
    // 初始化新的处理器数组
    window.ankidraw_hotkey_handlers = [];
    
    // 添加快捷键处理函数
    function addHotkeyHandler(hotkey, action) {
        if (!hotkey) return; // 跳过未设置的快捷键
        
        const handler = function(e) {
            // 检查是否在输入框中
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }
            
            // 解析快捷键
            const parts = hotkey.split('+');
            let match = true;
            
            // 检查Alt键
            if (parts.includes('Alt') && !e.altKey) match = false;
            // 检查Ctrl键
            if (parts.includes('Ctrl') && !e.ctrlKey) match = false;
            // 检查Shift键
            if (parts.includes('Shift') && !e.shiftKey) match = false;
            
            // 检查主键
            const mainKey = parts[parts.length - 1].toLowerCase();
            if (e.key.toLowerCase() !== mainKey) match = false;
            
            if (match) {
                e.preventDefault();
                action();
                return false;
            }
        };
        
        document.addEventListener('keydown', handler);
        window.ankidraw_hotkey_handlers.push(handler);
    }
    """
    
    # 为每个工具添加快捷键处理
    for tool_id, shortcut in hotkey_config.items():
        if not shortcut:
            continue
        
        if tool_id == 'visibility':
            js_code += f"""
            // 绘图工具快捷键
            addHotkeyHandler('{shortcut}', function() {{
                const btn = document.getElementById('ts_visibility_button');
                if (btn) btn.click();
            }});
            """
        elif tool_id == 'eraser':
            js_code += f"""
            // 橡皮擦快捷键
            addHotkeyHandler('{shortcut}', function() {{
                const btn = document.getElementById('ts_eraser_button');
                if (btn) btn.click();
            }});
            """
        elif tool_id == 'line':
            js_code += f"""
            // 直线工具快捷键
            addHotkeyHandler('{shortcut}', function() {{
                const btn = document.getElementById('ts_line_button');
                if (btn) btn.click();
            }});
            """
        elif tool_id == 'rectangle':
            js_code += f"""
            // 矩形工具快捷键
            addHotkeyHandler('{shortcut}', function() {{
                const btn = document.getElementById('ts_rectangle_button');
                if (btn) btn.click();
            }});
            """
        elif tool_id == 'undo':
            js_code += f"""
            // 撤销按钮快捷键
            addHotkeyHandler('{shortcut}', function() {{
                const btn = document.getElementById('ts_undo_button');
                if (btn) btn.click();
            }});
            """
        elif tool_id == 'clear':
            js_code += f"""
            // 清除画布按钮快捷键
            addHotkeyHandler('{shortcut}', function() {{
                const btn = document.getElementById('ts_clear_button');
                if (btn) btn.click();
            }});
            """
        elif tool_id == 'fullscreen':
            js_code += f"""
            // 全屏切换按钮快捷键
            addHotkeyHandler('{shortcut}', function() {{
                const btn = document.getElementById('ts_fullscreen_button');
                if (btn) btn.click();
            }});
            """
        elif tool_id == 'restore_window_size':
            js_code += f"""
            // 恢复窗口大小按钮快捷键
            addHotkeyHandler('{shortcut}', function() {{
                const btn = document.getElementById('ts_restore_window_size_button');
                if (btn) btn.click();
            }});
            """
    
    # 执行JavaScript代码
    execute_js(js_code)

def show_hotkey_config_dialog():
    """
    显示快捷键配置对话框
    """
    dialog = HotkeyConfigDialog(mw)
    try:
        # Qt6
        dialog.exec()
    except AttributeError:
        # Qt5
        dialog.exec_()

def setup_hotkey_config():
    """
    设置快捷键配置
    """
    # 加载配置
    load_hotkey_config()
    
    # 添加到reviewer_did_show_question和reviewer_did_show_answer钩子，
    # 确保在显示问题和答案时都应用快捷键配置
    from anki.hooks import addHook
    addHook('reviewer_did_show_question', apply_hotkey_config)
    addHook('reviewer_did_show_answer', apply_hotkey_config) 
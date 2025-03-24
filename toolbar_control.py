# -*- coding: utf-8 -*-
# Copyright: louis Liu <liury2015@outlook.com>
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
"""
工具栏控制面板模块 for AnkiDraw addon.
提供界面用于控制工具栏上各个工具按钮的显示和隐藏。
"""

import os
import time
from aqt import mw
from aqt.qt import QDialog, QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton, QLabel, QGroupBox
from aqt.qt import pyqtSlot as slot

# 导入语言模块
from . import lang

# 工具栏控制变量
toolbar_buttons_config = {
    'visibility': True,    # 绘图工具按钮
    'eraser': True,        # 橡皮擦按钮
    'line': True,          # 直线工具按钮
    'rectangle': True,     # 矩形工具按钮
    'perfect_freehand': False,  # 完美手绘按钮
    'calligraphy': False,   # 书法模式按钮
    'undo': True,          # 撤销按钮
    'clear': True,         # 清除画布按钮
    'fullscreen': True,     # 全屏切换按钮
    'restore_window_size': True  # 恢复窗口大小按钮
}

# 添加日志功能
def log_debug(message):
    """
    将调试信息写入日志文件
    """
    try:
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'addon_logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'toolbar_debug.log')
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        print(f"Error writing to log: {e}")

class ToolbarControlDialog(QDialog):
    """
    工具栏控制面板对话框
    """
    def __init__(self, parent=None):
        super(ToolbarControlDialog, self).__init__(parent)
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """
        设置对话框UI
        """
        self.setWindowTitle(lang.get_text("dialog_toolbar_control", "Toolbar Control Panel"))
        self.setMinimumWidth(300)
        
        main_layout = QVBoxLayout()
        
        # 工具控制组
        tools_group = QGroupBox(lang.get_text("dialog_toolbar_button_visibility", "Toolbar Button Visibility"))
        tools_layout = QVBoxLayout()
        
        # 创建各个工具的复选框
        self.checkboxes = {}
        
        # 绘图工具按钮
        self.checkboxes['visibility'] = QCheckBox(lang.get_text("dialog_drawing_tool_button", "Drawing Tool Button"))
        tools_layout.addWidget(self.checkboxes['visibility'])
        
        # 橡皮擦按钮
        self.checkboxes['eraser'] = QCheckBox(lang.get_text("dialog_eraser_button", "Eraser Button"))
        tools_layout.addWidget(self.checkboxes['eraser'])
        
        # 直线工具按钮
        self.checkboxes['line'] = QCheckBox(lang.get_text("dialog_line_tool_button", "Line Tool Button"))
        tools_layout.addWidget(self.checkboxes['line'])
        
        # 矩形工具按钮
        self.checkboxes['rectangle'] = QCheckBox(lang.get_text("dialog_rectangle_tool_button", "Rectangle Tool Button"))
        tools_layout.addWidget(self.checkboxes['rectangle'])
        
        # 完美手绘和书法模式按钮已禁用，不再显示相关选项
        
        # 撤销按钮
        self.checkboxes['undo'] = QCheckBox(lang.get_text("dialog_undo_button", "Undo Button"))
        tools_layout.addWidget(self.checkboxes['undo'])
        
        # 清除画布按钮
        self.checkboxes['clear'] = QCheckBox(lang.get_text("dialog_clear_canvas_button", "Clear Canvas Button"))
        tools_layout.addWidget(self.checkboxes['clear'])
        
        # 全屏切换按钮
        self.checkboxes['fullscreen'] = QCheckBox(lang.get_text("dialog_fullscreen_toggle_button", "Fullscreen Toggle Button"))
        tools_layout.addWidget(self.checkboxes['fullscreen'])
        
        # 恢复窗口大小按钮
        self.checkboxes['restore_window_size'] = QCheckBox(lang.get_text("dialog_restore_window_size_button", "Restore Window Size Button"))
        tools_layout.addWidget(self.checkboxes['restore_window_size'])
        
        tools_group.setLayout(tools_layout)
        main_layout.addWidget(tools_group)
        
        # 按钮区域
        buttons_layout = QHBoxLayout()
        
        # 全选按钮
        select_all_btn = QPushButton(lang.get_text("dialog_select_all", "Select All"))
        select_all_btn.clicked.connect(self.select_all)
        buttons_layout.addWidget(select_all_btn)
        
        # 取消全选按钮
        unselect_all_btn = QPushButton(lang.get_text("dialog_deselect_all", "Deselect All"))
        unselect_all_btn.clicked.connect(self.unselect_all)
        buttons_layout.addWidget(unselect_all_btn)
        
        # 确定按钮
        ok_btn = QPushButton(lang.get_text("ok_button", "OK"))
        ok_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(ok_btn)
        
        # 取消按钮
        cancel_btn = QPushButton(lang.get_text("cancel_button", "Cancel"))
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        main_layout.addLayout(buttons_layout)
        
        self.setLayout(main_layout)
    
    def load_settings(self):
        """
        加载工具栏设置到UI
        """
        for button_id, checkbox in self.checkboxes.items():
            checkbox.setChecked(toolbar_buttons_config[button_id])
    
    def save_settings(self):
        """
        保存UI设置到配置
        """
        global toolbar_buttons_config
        log_debug("Saving toolbar settings from dialog")
        
        for button_id, checkbox in self.checkboxes.items():
            old_value = toolbar_buttons_config.get(button_id, True)
            new_value = checkbox.isChecked()
            toolbar_buttons_config[button_id] = new_value
            
            if old_value != new_value:
                log_debug(f"Changed {button_id}: {old_value} -> {new_value}")
        
        # 保存到Anki配置
        save_toolbar_config()
        
        # 立即应用设置
        apply_toolbar_config()
        log_debug("Applied toolbar settings immediately")
    
    def select_all(self):
        """
        选中所有复选框
        """
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(True)
    
    def unselect_all(self):
        """
        取消选中所有复选框
        """
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(False)
    
    def accept(self):
        """
        确定按钮点击处理
        """
        self.save_settings()
        super(ToolbarControlDialog, self).accept()

def load_toolbar_config():
    """
    从Anki配置加载工具栏配置
    """
    global toolbar_buttons_config
    
    try:
        saved_config = mw.pm.profile.get('toolbar_buttons_config', None)
        log_debug(f"Loading toolbar config: {saved_config}")
        
        if saved_config:
            for key, value in saved_config.items():
                if key in toolbar_buttons_config:
                    toolbar_buttons_config[key] = value
            
            # 立即应用加载的配置
            apply_toolbar_config()
            log_debug(f"Applied toolbar config: {toolbar_buttons_config}")
        else:
            log_debug("No saved toolbar config found, using defaults")
    except Exception as e:
        log_debug(f"Error loading toolbar config: {e}")
        print(f"Error loading toolbar config: {e}")

def save_toolbar_config():
    """
    保存工具栏配置到Anki
    """
    try:
        log_debug(f"Saving toolbar config: {toolbar_buttons_config}")
        mw.pm.profile['toolbar_buttons_config'] = dict(toolbar_buttons_config)
        # 确保配置被立即写入
        mw.pm.save()
        log_debug("Toolbar config saved successfully")
    except Exception as e:
        log_debug(f"Error saving toolbar config: {e}")
        print(f"Error saving toolbar config: {e}")

def apply_toolbar_config(editor=None, html=None):
    """
    应用工具栏配置到界面
    注意: editor和html参数是为了兼容Anki的钩子系统
    """
    # 如果是作为钩子回调被调用，直接返回html，不执行JS
    if editor is not None and html is not None:
        log_debug("apply_toolbar_config called as a hook, returning html")
        return html
        
    from . import execute_js
    
    # 构建JavaScript代码来控制各个按钮的显示
    js_code = """
    function updateToolbarButtonsVisibility() {
        const toolbar = document.getElementById('pencil_button_bar');
        if (!toolbar) return;
        
    """
    
    # 添加各个按钮的可见性控制代码
    js_code += f"const btnVisibility = document.getElementById('ts_visibility_button');\n"
    js_code += f"if (btnVisibility) btnVisibility.style.display = {str(toolbar_buttons_config['visibility']).lower()} ? 'block' : 'none';\n\n"
    
    js_code += f"const btnEraser = document.getElementById('ts_eraser_button');\n"
    js_code += f"if (btnEraser) btnEraser.style.display = {str(toolbar_buttons_config['eraser']).lower()} ? 'block' : 'none';\n\n"
    
    js_code += f"const btnLine = document.getElementById('ts_line_button');\n"
    js_code += f"if (btnLine) btnLine.style.display = {str(toolbar_buttons_config['line']).lower()} ? 'block' : 'none';\n\n"
    
    js_code += f"const btnRectangle = document.getElementById('ts_rectangle_button');\n"
    js_code += f"if (btnRectangle) btnRectangle.style.display = {str(toolbar_buttons_config['rectangle']).lower()} ? 'block' : 'none';\n\n"
    
    js_code += f"const btnPerfectFreehand = document.getElementById('ts_perfect_freehand_button');\n"
    js_code += f"if (btnPerfectFreehand) btnPerfectFreehand.style.display = 'none';\n\n"
    
    js_code += f"const btnCalligraphy = document.getElementById('ts_kanji_button');\n"
    js_code += f"if (btnCalligraphy) btnCalligraphy.style.display = 'none';\n\n"
    
    js_code += f"const btnUndo = document.getElementById('ts_undo_button');\n"
    js_code += f"if (btnUndo) btnUndo.style.display = {str(toolbar_buttons_config['undo']).lower()} ? 'block' : 'none';\n\n"
    
    # 清除按钮没有ID，所以需要通过其他方式选择
    js_code += f"""
    // 清除画布按钮 (通过标题属性查找)
    const btnClear = Array.from(toolbar.querySelectorAll('button[title*=\"Clean canvas\"]'))[0];
    if (btnClear) btnClear.style.display = {str(toolbar_buttons_config['clear']).lower()} ? 'block' : 'none';
    
    """
    
    js_code += f"const btnFullscreen = document.getElementById('ts_switch_fullscreen_button');\n"
    js_code += f"if (btnFullscreen) btnFullscreen.style.display = {str(toolbar_buttons_config['fullscreen']).lower()} ? 'block' : 'none';\n\n"
    
    js_code += f"const btnRestoreWindowSize = document.getElementById('ts_restore_window_size_button');\n"
    js_code += f"if (btnRestoreWindowSize) btnRestoreWindowSize.style.display = {str(toolbar_buttons_config['restore_window_size']).lower()} ? 'block' : 'none';\n\n"
    
    js_code += "}\n\n updateToolbarButtonsVisibility();"
    
    # 执行JavaScript代码
    execute_js(js_code)

def show_toolbar_control_dialog():
    """
    显示工具栏控制面板对话框
    """
    dialog = ToolbarControlDialog(mw)
    result = dialog.exec()
    if result == QDialog.DialogCode.Accepted:
        apply_toolbar_config()

def setup_toolbar_control():
    """
    初始化工具栏控制功能
    """
    from anki.hooks import addHook
    
    log_debug("Setting up toolbar control hooks")
    
    # 加载配置
    load_toolbar_config()
    
    # 添加钩子确保配置在Anki启动时加载和应用
    addHook("profileLoaded", load_toolbar_config)
    
    # 添加钩子确保配置在Anki关闭时保存
    addHook("unloadProfile", save_toolbar_config)
    
    # 添加钩子确保配置在每次复习开始时应用
    # 重要：对于没有参数的函数使用lambda包装器
    addHook("showQuestion", lambda: apply_toolbar_config())
    addHook("showAnswer", lambda: apply_toolbar_config())
    
    # 移除导致错误的编辑器钩子
    # addHook("setupEditorButtons", apply_toolbar_config)
    
    # 使用lambda包装器来避免参数不匹配
    addHook("reviewer.setupWeb", lambda web: apply_toolbar_config())
    
    log_debug("Toolbar control hooks setup completed") 
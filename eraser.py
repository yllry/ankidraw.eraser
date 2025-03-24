# -*- coding: utf-8 -*-
# Copyright: Louis Liu <liury2015@outlook.com>
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
"""
Eraser module for AnkiDraw addon.
Adds an eraser functionality to erase entire strokes at once by clicking or dragging.
"""

from aqt import mw
from aqt.qt import QAction, pyqtSlot as slot
from anki.hooks import addHook
import os

# Eraser globals
eraser_active = False
eraser_size = 4  # 默认橡皮擦大小

def add_eraser_js():
    """
    Inject eraser JavaScript module into the reviewer.
    This is called when the profile is loaded and eraser feature is requested.
    """
    # 获取插件目录路径
    addon_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 读取eraser.js文件
    eraser_js_path = os.path.join(addon_dir, "templates", "eraser.js")
    try:
        with open(eraser_js_path, "r", encoding="utf-8") as f:
            eraser_js = f.read()
            
        # 执行JavaScript代码
        from . import execute_js
        execute_js(eraser_js)
        
        # 设置保存的橡皮擦大小
        set_eraser_size(eraser_size)
    except Exception as e:
        print(f"Error loading eraser.js: {e}")

def toggle_eraser():
    """
    Toggle the eraser tool on and off.
    """
    global eraser_active
    eraser_active = not eraser_active
    from . import execute_js
    execute_js(f"toggleEraser({str(eraser_active).lower()});")
    
    # 确保橡皮擦按钮状态与eraser_active同步
    if eraser_active:
        execute_js("""
        var eraserButton = document.getElementById('ts_eraser_button');
        if (eraserButton) {
            eraserButton.classList.add('active');
        }
        """)
    else:
        execute_js("""
        var eraserButton = document.getElementById('ts_eraser_button');
        if (eraserButton) {
            eraserButton.classList.remove('active');
        }
        """)

@slot()
def setup_eraser_shortcuts():
    """
    Set up keyboard shortcut for toggling eraser.
    """
    from . import execute_js
    execute_js("""
    document.addEventListener('keyup', function(e) {
        // Alt + Q to toggle eraser
        if ((e.key === "q" || e.key === "Q") && e.altKey) {
            e.preventDefault();
            toggleEraser();
        }
    });
    """)

def set_eraser_size(size):
    """
    设置橡皮擦大小
    """
    from . import execute_js
    execute_js(f"updateEraserSize({size});")

def save_eraser_state():
    """
    Save eraser state to profile.
    """
    mw.pm.profile['eraser_active'] = eraser_active
    mw.pm.profile['eraser_size'] = eraser_size

def load_eraser_state():
    """
    Load eraser state from profile.
    """
    global eraser_active, eraser_size
    try:
        eraser_active = mw.pm.profile.get('eraser_active', False)
        eraser_size = mw.pm.profile.get('eraser_size', 4)  # 默认值为4
    except KeyError:
        eraser_active = False
        eraser_size = 4

def save_eraser_size(size):
    """
    保存橡皮擦大小设置
    """
    global eraser_size
    size = int(size)
    if size < 1:
        size = 1
    elif size > 20:
        size = 20
    eraser_size = size
    mw.pm.profile['eraser_size'] = eraser_size

def toggle_line_tool():
    """
    切换直线工具
    """
    from . import execute_js
    execute_js("toggleLineTool();")

def toggle_rectangle_tool():
    """
    切换矩形工具
    """
    from . import execute_js
    execute_js("toggleRectangleTool();")

def setup_eraser():
    """
    Initialize eraser functionality by adding hooks.
    """
    addHook("profileLoaded", load_eraser_state)
    addHook("unloadProfile", save_eraser_state)
    addHook("profileLoaded", setup_eraser_shortcuts)
    addHook("profileLoaded", add_eraser_js) 
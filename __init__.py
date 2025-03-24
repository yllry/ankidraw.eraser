# Copyright: Michal Krassowski <krassowski.michal@gmail.com>
# Copyright: Rytis Petronis <petronisrytis@gmail.com>
# Copyright: Louis Liu <liury2015@outlook.com>

# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
"""
Initially based on the Anki-TouchScreen addon, updated ui and added pressure pen/stylus capabilities, perfect freehand(line smoothing) and calligrapher functionality.


It adds an AnkiDraw menu entity with options like:

    switching AnkiDraw
    modifying some of the colors
    thickness
    toolbar settings
    增加了橡皮擦功能（包括slim pen笔端擦除和侧方按键擦除）
    增加了笔迹存储功能
    增加了直线工具（包括虚线和波浪线）
    增加了矩形工具
    禁用了书法家功能和完美手写功能
    调整了工具栏样式
    对菜单栏做了整合修改
    增加了快捷键自定义功能
    新增回到书写时的窗口大小工具
    新增用户自定义快捷键控制面板


If you want to contribute visit GitHub page: https://github.com/Rytisgit/Anki-StylusDraw
Also, feel free to send me bug reports or feature requests.

Copyright: Michal Krassowski <krassowski.michal@gmail.com>
Copyright: Rytis Petronis <petronisrytis@gmail.com>
Copyright: Louis Liu <liury2015@outlook.com>
License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html,
Important parts of Javascript code inspired by http://creativejs.com/tutorials/painting-with-pixels/index.html
"""

__addon_name__ = "AnkiDraw.Eraser"
__version__ = "3.2"

from aqt import mw
from aqt.utils import showWarning

from anki.lang import _
from anki.hooks import addHook, wrap

from aqt.qt import QAction, QMenu, QColorDialog, QMessageBox, QInputDialog, QLabel,\
   QPushButton, QDialog, QVBoxLayout, QComboBox, QHBoxLayout, QSpinBox, QCheckBox
from aqt.qt import QKeySequence,QColor
from aqt.qt import pyqtSlot as slot

# 导入语言模块
from . import lang

# Import eraser module
from . import eraser
# Import toolbar control module
from . import toolbar_control
# Import stroke storage module
from . import stroke_storage
# Import stroke manager module
from . import stroke_manager
# Import hotkey manager module
from . import hotkey_manager

# This declarations are there only to be sure that in case of troubles
# with "profileLoaded" hook everything will work.

ts_state_on = False
ts_profile_loaded = False
ts_auto_hide = True
ts_auto_hide_pointer = True
ts_default_small_canvas = False
ts_zen_mode = False
ts_follow = False
ts_ConvertDotStrokes = True

ts_color = "#272828"
ts_line_width = 4
ts_opacity = 0.7
ts_location = 1
ts_x_offset = 2
ts_y_offset = 2
ts_small_width = 500
ts_small_height = 500
ts_background_color = "#FFFFFF00"
ts_orient_vertical = True
ts_default_review_html = mw.reviewer.revHtml

# 直线工具的颜色和线宽设置
ts_line_color = "#272828"
ts_line_line_width = 4

# 矩形工具的颜色和线宽设置
ts_rectangle_color = "#272828"
ts_rectangle_line_width = 4

ts_default_VISIBILITY = "true"
ts_default_PerfFreehand = "false"
ts_default_Calligraphy = "false"

# 添加全局变量跟踪当前是否显示卡片正面
is_question_side = True

@slot()
def ts_change_color():
    """
    Open color picker and set chosen color to text (in content)
    """
    global ts_color
    qcolor_old = QColor(ts_color)
    qcolor = QColorDialog.getColor(qcolor_old)
    if qcolor.isValid():
        ts_color = qcolor.name()
        execute_js("color = '" + ts_color + "';")
        execute_js("if (typeof update_pen_settings === 'function') { update_pen_settings(); }")


@slot()
def ts_change_width():
    global ts_line_width
    value, accepted = QInputDialog.getDouble(mw, lang.get_text("dialog_ankidraw", "AnkiDraw"), lang.get_text("dialog_enter_width", "Enter the width:"), ts_line_width)
    if accepted:
        ts_line_width = value
        execute_js("line_width = '" + str(ts_line_width) + "';")
        execute_js("if (typeof update_pen_settings === 'function') { update_pen_settings(); }")


@slot()
def ts_change_opacity():
    global ts_opacity
    value, accepted = QInputDialog.getDouble(mw, lang.get_text("dialog_ankidraw", "AnkiDraw"), lang.get_text("dialog_enter_opacity", "Enter the opacity (0 = transparent, 100 = opaque):"), 100 * ts_opacity, 0, 100, 2)
    if accepted:
        ts_opacity = value / 100
        execute_js("canvas.style.opacity = " + str(ts_opacity))


@slot()
def ts_change_line_color():
    """
    Open color picker and set chosen color for line tool
    """
    global ts_line_color
    qcolor_old = QColor(ts_line_color)
    qcolor = QColorDialog.getColor(qcolor_old)
    if qcolor.isValid():
        ts_line_color = qcolor.name()
        execute_js(f"set_line_color('{ts_line_color}');")


@slot()
def ts_change_line_width():
    """
    Set width for line tool
    """
    global ts_line_line_width
    value, accepted = QInputDialog.getDouble(mw, lang.get_text("dialog_line_tool", "AnkiDraw Line Tool"), lang.get_text("dialog_enter_line_width", "Enter the line width:"), ts_line_line_width)
    if accepted:
        ts_line_line_width = value
        execute_js(f"set_line_width({ts_line_line_width});")


@slot()
def ts_change_rectangle_color():
    """
    Open color picker and set chosen color for rectangle tool
    """
    global ts_rectangle_color
    qcolor_old = QColor(ts_rectangle_color)
    qcolor = QColorDialog.getColor(qcolor_old, title=lang.get_text("dialog_rectangle_tool", "AnkiDraw Rectangle Tool"))
    if qcolor.isValid():
        ts_rectangle_color = qcolor.name()
        execute_js(f"set_rectangle_color('{ts_rectangle_color}');")
        # 立即保存设置，确保永久保存
        mw.pm.profile['ts_rectangle_color'] = ts_rectangle_color
        mw.pm.save()


@slot()
def ts_change_rectangle_width():
    """
    Set width for rectangle tool
    """
    global ts_rectangle_line_width
    value, accepted = QInputDialog.getDouble(mw, lang.get_text("dialog_rectangle_tool", "AnkiDraw Rectangle Tool"), lang.get_text("dialog_enter_rectangle_width", "Enter the rectangle line width:"), ts_rectangle_line_width)
    if accepted:
        ts_rectangle_line_width = value
        execute_js(f"set_rectangle_width({ts_rectangle_line_width});")
        # 立即保存设置，确保永久保存
        mw.pm.profile['ts_rectangle_line_width'] = ts_rectangle_line_width
        mw.pm.save()


class CustomDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(lang.get_text("dialog_toolbar_location", "Toolbar And Canvas"))

        self.combo_box = QComboBox()
        self.combo_box.addItem("Top-Left")
        self.combo_box.addItem("Top-Right")
        self.combo_box.addItem("Bottom-Left")
        self.combo_box.addItem("Bottom-Right")

        combo_label = QLabel(lang.get_text("dialog_location", "Location:"))

        range_label = QLabel(lang.get_text("dialog_offset", "Offset:"))

        start_range_label = QLabel(lang.get_text("dialog_x_offset", "X Offset:"))
        self.start_spin_box = QSpinBox()
        self.start_spin_box.setRange(0, 1000)

        small_width_label = QLabel(lang.get_text("dialog_non_fullscreen_width", "Non-Fullscreen Canvas Width:"))
        self.small_width_spin_box = QSpinBox()
        self.small_width_spin_box.setRange(0, 9999)

        small_height_label = QLabel(lang.get_text("dialog_non_fullscreen_height", "Non-Fullscreen Canvas Height:"))
        self.small_height_spin_box = QSpinBox()
        self.small_height_spin_box.setRange(0, 9999)

        end_range_label = QLabel(lang.get_text("dialog_y_offset", "Y Offset:"))
        self.end_spin_box = QSpinBox()
        self.end_spin_box.setRange(0, 1000)

        range_layout = QVBoxLayout()

        small_height_layout = QHBoxLayout()
        small_height_layout.addWidget(small_height_label)
        small_height_layout.addWidget(self.small_height_spin_box)

        small_width_layout = QHBoxLayout()
        small_width_layout.addWidget(small_width_label)
        small_width_layout.addWidget(self.small_width_spin_box)

        color_layout = QHBoxLayout()
        self.color_button = QPushButton(lang.get_text("dialog_select_color", "Select Color"))
        self.color_button.clicked.connect(self.select_color)

        self.color_label = QLabel(f"{lang.get_text('dialog_background_color', 'Background color:')} #FFFFFF00")  # Initial color label

        color_layout.addWidget(self.color_label)
        color_layout.addWidget(self.color_button)
        

        

        start_layout = QHBoxLayout()
        start_layout.addWidget(start_range_label)
        start_layout.addWidget(self.start_spin_box)

        end_layout = QHBoxLayout()
        end_layout.addWidget(end_range_label)
        end_layout.addWidget(self.end_spin_box)
        range_layout.addLayout(start_layout)
        range_layout.addLayout(end_layout)
        range_layout.addLayout(small_width_layout)
        range_layout.addLayout(small_height_layout)
        

        checkbox_label2 = QLabel(lang.get_text("dialog_orient_vertically", "Orient vertically:"))
        self.checkbox2 = QCheckBox()

        checkbox_layout2 = QHBoxLayout()
        checkbox_layout2.addWidget(checkbox_label2)
        checkbox_layout2.addWidget(self.checkbox2)

        accept_button = QPushButton(lang.get_text("dialog_accept", "Accept"))
        cancel_button = QPushButton(lang.get_text("dialog_cancel", "Cancel"))
        reset_button = QPushButton(lang.get_text("dialog_default", "Default"))

        accept_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        reset_button.clicked.connect(self.reset_to_default)

        button_layout = QHBoxLayout()
        button_layout.addWidget(accept_button)
        button_layout.addWidget(reset_button)
        button_layout.addWidget(cancel_button)
        

        dialog_layout = QVBoxLayout()
        dialog_layout.addWidget(combo_label)
        dialog_layout.addWidget(self.combo_box)
        dialog_layout.addWidget(range_label)
        dialog_layout.addLayout(range_layout)
        dialog_layout.addLayout(checkbox_layout2)
        dialog_layout.addLayout(color_layout)
        dialog_layout.addLayout(button_layout)
        
        self.setLayout(dialog_layout)

    def set_values(self, combo_index, start_value, end_value, checkbox_state2, width, height, background_color):
        self.combo_box.setCurrentIndex(combo_index)
        self.start_spin_box.setValue(start_value)
        self.small_height_spin_box.setValue(height)
        self.small_width_spin_box.setValue(width)
        self.end_spin_box.setValue(end_value)
        self.checkbox2.setChecked(checkbox_state2)
        self.color_label.setText(f"{lang.get_text('dialog_background_color', 'Background color:')} {background_color}")

    def reset_to_default(self):
        self.combo_box.setCurrentIndex(1)
        self.start_spin_box.setValue(2)
        self.end_spin_box.setValue(2)
        self.small_height_spin_box.setValue(500)
        self.small_width_spin_box.setValue(500)
        self.checkbox2.setChecked(True)
        self.color_label.setText(f"{lang.get_text('dialog_background_color', 'Background color:')} #FFFFFF00")  # Reset color label

    def select_color(self):
        qcolor_old = QColor(ts_background_color)
        qcolor = QColorDialog.getColor(qcolor_old, options=QColorDialog.ShowAlphaChannel)
        if qcolor.isValid():
            color_name = qcolor.name(QColor.HexArgb)
            self.color_label.setText(f"{lang.get_text('dialog_background_color', 'Background color:')} {color_name}")

def get_css_for_toolbar_location(location, x_offset, y_offset, orient_column, canvas_width, canvas_height, background_color):
    orient = "column" if orient_column else "row"
    switch = {
        0: f"""
                        --button-bar-pt: {y_offset}px;
                        --button-bar-pr: unset;
                        --button-bar-pb: unset;
                        --button-bar-pl: {x_offset}px;
                        --button-bar-orientation: {orient};
                        --small-canvas-height: {canvas_height};
                        --small-canvas-width: {canvas_width};
                        --background-color: {background_color};
                    """,
        1: f"""
                        --button-bar-pt: {y_offset}px;
                        --button-bar-pr: {x_offset}px;
                        --button-bar-pb: unset;
                        --button-bar-pl: unset;
                        --button-bar-orientation: {orient};
                        --small-canvas-height: {canvas_height};
                        --small-canvas-width: {canvas_width};
                        --background-color: {background_color};
                    """,
        2: f"""
                        --button-bar-pt: unset;
                        --button-bar-pr: unset;
                        --button-bar-pb: {y_offset}px;
                        --button-bar-pl: {x_offset}px;
                        --button-bar-orientation: {orient};
                        --small-canvas-height: {canvas_height};
                        --small-canvas-width: {canvas_width};
                        --background-color: {background_color};
                    """,
        3: f"""
                        --button-bar-pt: unset;
                        --button-bar-pr: {x_offset}px;
                        --button-bar-pb: {y_offset}px;
                        --button-bar-pl: unset;
                        --button-bar-orientation: {orient};
                        --small-canvas-height: {canvas_height};
                        --small-canvas-width: {canvas_width};
                        --background-color: {background_color};
                    """,
    }
    return switch.get(location, """
                        --button-bar-pt: 2px;
                        --button-bar-pr: 2px;
                        --button-bar-pb: unset;
                        --button-bar-pl: unset;
                        --button-bar-orientation: column;
                        --small-canvas-height: 500;
                        --small-canvas-width: 500;
                        --background-color: #FFFFFF00;
                    """)

def get_css_for_auto_hide(auto_hide, zen):
    return "none" if auto_hide or zen else "flex"

def get_css_for_zen_mode(hide):
    return "none" if hide else "flex"

def get_css_for_auto_hide_pointer(auto_hide):
    return "none" if auto_hide else "default"

@slot()
def ts_change_toolbar_settings():
    global ts_orient_vertical, ts_y_offset, ts_x_offset, ts_location, ts_small_width, ts_small_height, ts_background_color
    
    dialog = CustomDialog()
    dialog.set_values(ts_location, ts_x_offset, ts_y_offset, ts_orient_vertical, ts_small_width, ts_small_height, ts_background_color) 
    result = dialog.exec()

    if result == QDialog.DialogCode.Accepted:
        ts_location = dialog.combo_box.currentIndex()
        ts_x_offset = dialog.start_spin_box.value()
        ts_y_offset = dialog.end_spin_box.value()
        ts_small_height = dialog.small_height_spin_box.value()
        ts_background_color = dialog.color_label.text()[-9:]
        ts_small_width = dialog.small_width_spin_box.value()
        ts_orient_vertical = dialog.checkbox2.isChecked()
        ts_switch()
        ts_switch()


def ts_save():
    """
    Saves configurable variables into profile, so they can
    be used to restore previous state after Anki restart.
    """
    mw.pm.profile['ts_state_on'] = ts_state_on
    mw.pm.profile['ts_color'] = ts_color
    mw.pm.profile['ts_line_width'] = ts_line_width
    mw.pm.profile['ts_opacity'] = ts_opacity
    mw.pm.profile['ts_default_ConvertDotStrokes'] = ts_ConvertDotStrokes
    mw.pm.profile['ts_auto_hide'] = ts_auto_hide
    mw.pm.profile['ts_auto_hide_pointer'] = ts_auto_hide_pointer
    mw.pm.profile['ts_default_small_canvas'] = ts_default_small_canvas
    mw.pm.profile['ts_zen_mode'] = ts_zen_mode
    mw.pm.profile['ts_follow'] = ts_follow
    mw.pm.profile['ts_location'] = ts_location
    mw.pm.profile['ts_x_offset'] = ts_x_offset
    mw.pm.profile['ts_y_offset'] = ts_y_offset
    mw.pm.profile['ts_small_height'] = ts_small_height
    mw.pm.profile['ts_background_color'] = ts_background_color
    mw.pm.profile['ts_small_width'] = ts_small_width
    mw.pm.profile['ts_orient_vertical'] = ts_orient_vertical
    # 保存直线工具的颜色和线宽
    mw.pm.profile['ts_line_color'] = ts_line_color
    mw.pm.profile['ts_line_line_width'] = ts_line_line_width
    # 保存矩形工具的颜色和线宽
    mw.pm.profile['ts_rectangle_color'] = ts_rectangle_color
    mw.pm.profile['ts_rectangle_line_width'] = ts_rectangle_line_width
    # Save eraser state
    eraser.save_eraser_state()


def ts_load():
    """
    Load configuration from profile, set states of checkable menu objects
    and turn on night mode if it were enabled on previous session.
    """
    global ts_state_on, ts_color, ts_profile_loaded, ts_line_width, ts_opacity, ts_ConvertDotStrokes, ts_auto_hide, ts_auto_hide_pointer, ts_default_small_canvas, ts_zen_mode, ts_follow, ts_orient_vertical, ts_y_offset, ts_x_offset, ts_location, ts_small_width, ts_small_height, ts_background_color, ts_line_color, ts_line_line_width, ts_rectangle_color, ts_rectangle_line_width
    try:
        # 加载笔迹保存设置
        if 'ankidraw_save_strokes_enabled' in mw.pm.profile:
            stroke_manager.set_save_strokes_enabled(mw.pm.profile['ankidraw_save_strokes_enabled'])
        else:
            # 默认启用笔迹保存
            stroke_manager.set_save_strokes_enabled(True)
            
        ts_state_on = mw.pm.profile['ts_state_on']
        ts_color = mw.pm.profile['ts_color']
        ts_line_width = mw.pm.profile['ts_line_width']
        ts_opacity = mw.pm.profile['ts_opacity']
        ts_auto_hide = mw.pm.profile['ts_auto_hide']
        ts_auto_hide_pointer = mw.pm.profile['ts_auto_hide_pointer']
        ts_default_small_canvas = mw.pm.profile['ts_default_small_canvas']
        ts_zen_mode = mw.pm.profile['ts_zen_mode']
        ts_follow = mw.pm.profile['ts_follow']
        ts_ConvertDotStrokes = bool(mw.pm.profile['ts_default_ConvertDotStrokes'])#fix for previously being a string value, defaults string value to true bool, will be saved as true or false bool after
        ts_orient_vertical = mw.pm.profile['ts_orient_vertical']
        ts_y_offset = mw.pm.profile['ts_y_offset']
        ts_small_width = mw.pm.profile['ts_small_width']
        ts_small_height = mw.pm.profile['ts_small_height']
        ts_background_color = mw.pm.profile['ts_background_color']
        ts_x_offset = mw.pm.profile['ts_x_offset']
        ts_location = mw.pm.profile['ts_location']
        # 加载直线工具的颜色和线宽
        ts_line_color = mw.pm.profile['ts_line_color']
        ts_line_line_width = mw.pm.profile['ts_line_line_width']
        # 加载矩形工具的颜色和线宽
        ts_rectangle_color = mw.pm.profile['ts_rectangle_color']
        ts_rectangle_line_width = mw.pm.profile['ts_rectangle_line_width']
        ts_profile_loaded = True
        
        # 初始化语言设置 - 确保在配置文件加载后执行
        lang.init()
        
        # 注意：不在这里创建菜单，而是由delayed_menu_setup()负责
        # 这样可以避免菜单重复创建的问题
        
        # Load eraser state
        eraser.load_eraser_state()
        
        if ts_state_on:
            ts_on()

        assure_plugged_in()
    except KeyError:
        ts_state_on = False
        ts_color = "#272828"
        ts_line_width = 4
        ts_opacity = 0.8
        ts_auto_hide = True
        ts_auto_hide_pointer = True
        ts_default_small_canvas = False
        ts_zen_mode = False
        ts_follow = False
        ts_ConvertDotStrokes = True
        ts_orient_vertical = True
        ts_y_offset = 2
        ts_small_width = 500
        ts_small_height = 500
        ts_background_color = "#FFFFFF00"
        ts_x_offset = 2
        ts_location = 1
        # 默认直线工具颜色和线宽
        ts_line_color = "#272828"
        ts_line_line_width = 4
        # 默认矩形工具颜色和线宽
        ts_rectangle_color = "#272828"
        ts_rectangle_line_width = 4

        ts_profile_loaded = True
        
        # 初始化语言设置 - 确保在配置文件加载后执行
        lang.init()
        
        # 注意：不在这里创建菜单，而是由delayed_menu_setup()负责
        # 这样可以避免菜单重复创建的问题
        
        # Load eraser state
        eraser.load_eraser_state()
        
        if ts_state_on:
            ts_on()

        assure_plugged_in()


def execute_js(code):
    web_object = mw.reviewer.web
    web_object.eval(code)


# 修改bridge_command函数，添加处理正面/全部笔迹的命令
def bridge_command(cmd):
    """处理从JavaScript发来的命令"""
    if cmd.startswith("ankidraw:save_eraser_size:"):
        # 格式: ankidraw:save_eraser_size:数字
        try:
            size = int(cmd.split(":")[-1])
            eraser.save_eraser_size(size)
        except Exception as e:
            print(f"保存橡皮擦大小时出错: {e}")
    
    elif cmd.startswith("ankidraw:save_strokes:"):
        # 检查是否启用笔迹保存
        if not stroke_manager.get_save_strokes_enabled():
            print("Debug - 保存笔迹: 笔迹保存功能已禁用，跳过保存")
            return
            
        # 格式: ankidraw:save_strokes:[cardId]:[strokeData]:[windowWidth]:[windowHeight]
        try:
            # 分割命令数据，注意这里需要适当处理，因为strokeData本身可能包含':'
            parts = cmd.split(":", 3)  # 最多分割3次，确保strokeData部分完整
            if len(parts) >= 4:
                card_id = parts[2]
                stroke_data_with_dimensions = parts[3]
                
                # 检查是否包含窗口大小信息
                window_width = None
                window_height = None
                
                # 尝试从数据末尾提取窗口大小信息
                try:
                    # 查找最后两个分隔符
                    last_parts = stroke_data_with_dimensions.rsplit(":", 2)
                    if len(last_parts) == 3:
                        stroke_data = last_parts[0]
                        try:
                            window_width = int(last_parts[1])
                            window_height = int(last_parts[2])
                            print(f"Debug - 保存笔迹: 获取到窗口大小信息 宽={window_width}, 高={window_height}")
                        except ValueError:
                            # 如果转换失败，说明不是有效的窗口大小信息
                            stroke_data = stroke_data_with_dimensions
                            window_width = None
                            window_height = None
                    else:
                        stroke_data = stroke_data_with_dimensions
                except Exception as e:
                    print(f"提取窗口大小信息时出错: {e}")
                    stroke_data = stroke_data_with_dimensions
                
                print(f"Debug - 保存笔迹: 卡片ID={card_id}, 数据长度={len(stroke_data)}, 窗口大小={window_width}x{window_height if window_width and window_height else 'None'}")
                
                # 根据当前显示的是正面还是背面，保存到不同的区域
                if is_question_side:
                    success = stroke_storage.save_front_stroke_data(card_id, stroke_data, window_width, window_height)
                    print(f"Debug - 保存正面笔迹: {'成功' if success else '失败'}")
                else:
                    success = stroke_storage.save_all_stroke_data(card_id, stroke_data, window_width, window_height)
                    print(f"Debug - 保存全部笔迹: {'成功' if success else '失败'}")
        except Exception as e:
            print(f"保存笔迹数据时出错: {e}")
            import traceback
            traceback.print_exc()
    
    elif cmd.startswith("ankidraw:save_strokes_no_window:"):
        # 格式: ankidraw:save_strokes_no_window:[cardId]:[strokeData]
        try:
            # 分割命令数据，注意这里需要适当处理，因为strokeData本身可能包含':'
            parts = cmd.split(":", 3)  # 最多分割3次，确保strokeData部分完整
            if len(parts) >= 4:
                card_id = parts[2]
                stroke_data = parts[3]
                
                print(f"Debug - 保存笔迹(不更新窗口大小): 卡片ID={card_id}, 数据长度={len(stroke_data)}")
                
                # 根据当前显示的是正面还是背面，保存到不同的区域
                if is_question_side:
                    success = stroke_storage.save_front_stroke_data(card_id, stroke_data)
                    print(f"Debug - 保存正面笔迹(不更新窗口大小): {'成功' if success else '失败'}")
                else:
                    success = stroke_storage.save_all_stroke_data(card_id, stroke_data)
                    print(f"Debug - 保存全部笔迹(不更新窗口大小): {'成功' if success else '失败'}")
        except Exception as e:
            print(f"保存笔迹数据时出错: {e}")
            import traceback
            traceback.print_exc()
            
    elif cmd.startswith("ankidraw:restore_front_window_size:"):
        # 格式: ankidraw:restore_front_window_size:[cardId]:[dpr]:[osType]
        try:
            # 分割命令，提取卡片ID和系统信息
            parts = cmd.split(":", 3)
            card_id = parts[2]
            
            # 提取系统信息（如果有）
            dpr = 1.0
            is_windows = False
            if len(parts) > 3 and ':' in parts[3]:
                sys_info = parts[3].split(':')
                if len(sys_info) >= 2:
                    try:
                        dpr = float(sys_info[0])
                        is_windows = sys_info[1] == 'win'
                    except:
                        pass
            
            print(f"Debug - 恢复正面笔迹窗口大小: 请求卡片ID={card_id}, DPR={dpr}, 是否Windows={is_windows}")
            
            # 获取保存的窗口大小信息
            width, height = stroke_storage.get_front_window_size(card_id)
            
            if width and height:
                print(f"Debug - 恢复正面笔迹窗口大小: 找到窗口大小 宽={width}, 高={height}")
                
                # Windows系统下，特殊处理高度
                if is_windows:
                    # Windows下根据DPI调整高度，增加一些额外高度以补偿缩放和标题栏等UI元素
                    # 对于高DPI显示器，调整比例更大
                    height_adjustment = 1.0
                    if dpr > 1.0:  # 高DPI显示器
                        height_adjustment = 1.15  # 增加15%的高度
                    else:
                        height_adjustment = 1.1   # 增加10%的高度
                    
                    adjusted_height = int(height * height_adjustment)
                    print(f"Debug - 恢复正面笔迹窗口大小: Windows系统，将高度从{height}调整到{adjusted_height}")
                    height = adjusted_height
                
                # 调整Anki主窗口大小
                mw.resize(width, height)
                print(f"Debug - 恢复正面笔迹窗口大小: 已调整窗口到 {width}x{height}")
                
                # 通知用户
                from aqt.utils import tooltip
                tooltip(lang.get_text("restore_window_size_success") % (width, height))
            else:
                print(f"Debug - 恢复正面笔迹窗口大小: 未找到窗口大小信息")
                # 通知用户未找到窗口大小信息
                from aqt.utils import tooltip
                tooltip(lang.get_text("restore_window_size_not_found"))
        except Exception as e:
            print(f"恢复正面笔迹窗口大小时出错: {e}")
            import traceback
            traceback.print_exc()
    
    elif cmd.startswith("ankidraw:restore_all_window_size:"):
        # 格式: ankidraw:restore_all_window_size:[cardId]:[dpr]:[osType]
        try:
            # 分割命令，提取卡片ID和系统信息
            parts = cmd.split(":", 3)
            card_id = parts[2]
            
            # 提取系统信息（如果有）
            dpr = 1.0
            is_windows = False
            if len(parts) > 3 and ':' in parts[3]:
                sys_info = parts[3].split(':')
                if len(sys_info) >= 2:
                    try:
                        dpr = float(sys_info[0])
                        is_windows = sys_info[1] == 'win'
                    except:
                        pass
            
            print(f"Debug - 恢复全部笔迹窗口大小: 请求卡片ID={card_id}, DPR={dpr}, 是否Windows={is_windows}")
            
            # 获取保存的窗口大小信息
            width, height = stroke_storage.get_all_window_size(card_id)
            
            if width and height:
                print(f"Debug - 恢复全部笔迹窗口大小: 找到窗口大小 宽={width}, 高={height}")
                
                # Windows系统下，特殊处理高度
                if is_windows:
                    # Windows下根据DPI调整高度，增加一些额外高度以补偿缩放和标题栏等UI元素
                    # 对于高DPI显示器，调整比例更大
                    height_adjustment = 1.0
                    if dpr > 1.0:  # 高DPI显示器
                        height_adjustment = 1.15  # 增加15%的高度
                    else:
                        height_adjustment = 1.1   # 增加10%的高度
                    
                    adjusted_height = int(height * height_adjustment)
                    print(f"Debug - 恢复全部笔迹窗口大小: Windows系统，将高度从{height}调整到{adjusted_height}")
                    height = adjusted_height
                
                # 调整Anki主窗口大小
                mw.resize(width, height)
                print(f"Debug - 恢复全部笔迹窗口大小: 已调整窗口到 {width}x{height}")
                
                # 通知用户
                from aqt.utils import tooltip
                tooltip(lang.get_text("restore_window_size_success") % (width, height))
            else:
                print(f"Debug - 恢复全部笔迹窗口大小: 未找到窗口大小信息")
                # 通知用户未找到窗口大小信息
                from aqt.utils import tooltip
                tooltip(lang.get_text("restore_window_size_not_found"))
        except Exception as e:
            print(f"恢复全部笔迹窗口大小时出错: {e}")
            import traceback
            traceback.print_exc()
    
    elif cmd.startswith("ankidraw:restore_window_size:"):
        # 向后兼容旧版命令 格式: ankidraw:restore_window_size:[cardId]:[dpr]:[osType]
        try:
            # 分割命令，提取卡片ID和系统信息
            parts = cmd.split(":", 3)
            card_id = parts[2]
            
            # 提取系统信息（如果有）
            dpr = 1.0
            is_windows = False
            if len(parts) > 3 and ':' in parts[3]:
                sys_info = parts[3].split(':')
                if len(sys_info) >= 2:
                    try:
                        dpr = float(sys_info[0])
                        is_windows = sys_info[1] == 'win'
                    except:
                        pass
            else:
                # 如果前端没有提供环境信息，尝试从操作系统获取
                import platform
                is_windows = platform.system() == "Windows"
                
            print(f"Debug - 兼容模式恢复窗口大小: 请求卡片ID={card_id}, DPR={dpr}, 是否Windows={is_windows}")
            
            # 根据当前显示的是正面还是背面，恢复不同的窗口大小
            if is_question_side:
                width, height = stroke_storage.get_front_window_size(card_id)
                side_name = "正面"
            else:
                width, height = stroke_storage.get_all_window_size(card_id)
                side_name = "答案"
            
            if width and height:
                print(f"Debug - 兼容模式恢复{side_name}笔迹窗口大小: 找到窗口大小 宽={width}, 高={height}")
                
                # Windows系统下，特殊处理高度
                if is_windows:
                    # Windows下根据DPI调整高度，增加一些额外高度以补偿缩放和标题栏等UI元素
                    # 对于高DPI显示器，调整比例更大
                    height_adjustment = 1.0
                    if dpr > 1.0:  # 高DPI显示器
                        height_adjustment = 1.15  # 增加15%的高度
                    else:
                        height_adjustment = 1.1   # 增加10%的高度
                    
                    adjusted_height = int(height * height_adjustment)
                    print(f"Debug - 兼容模式恢复{side_name}笔迹窗口大小: Windows系统，将高度从{height}调整到{adjusted_height}")
                    height = adjusted_height
                
                # 调整Anki主窗口大小
                mw.resize(width, height)
                print(f"Debug - 兼容模式恢复{side_name}笔迹窗口大小: 已调整窗口到 {width}x{height}")
                
                # 通知用户
                from aqt.utils import tooltip
                tooltip(lang.get_text("restore_window_size_success") % (width, height))
            else:
                print(f"Debug - 兼容模式恢复{side_name}笔迹窗口大小: 未找到窗口大小信息")
                # 通知用户未找到窗口大小信息
                from aqt.utils import tooltip
                tooltip(lang.get_text("restore_window_size_not_found"))
        except Exception as e:
            print(f"兼容模式恢复窗口大小时出错: {e}")
            import traceback
            traceback.print_exc()
    
    elif cmd.startswith("ankidraw:load_front_strokes:"):
        # 格式: ankidraw:load_front_strokes:[cardId]
        try:
            card_id = cmd.split(":", 2)[2]
            print(f"Debug - 加载正面笔迹: 请求卡片ID={card_id}")
            stroke_data = stroke_storage.load_front_stroke_data(card_id)
            
            if stroke_data:
                print(f"Debug - 加载正面笔迹: 成功加载数据，长度={len(stroke_data)}")
                # 转义JSON字符串，确保安全传递
                stroke_data = stroke_data.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
                # 将笔迹数据发送回JavaScript
                execute_js(f'load_saved_strokes("{stroke_data}", true);') # true表示是正面笔迹
            else:
                print(f"Debug - 加载正面笔迹: 未找到笔迹数据")
        except Exception as e:
            print(f"加载正面笔迹数据时出错: {e}")
    
    elif cmd.startswith("ankidraw:load_all_strokes:"):
        # 格式: ankidraw:load_all_strokes:[cardId]
        try:
            card_id = cmd.split(":", 2)[2]
            print(f"Debug - 加载全部笔迹: 请求卡片ID={card_id}")
            stroke_data = stroke_storage.load_all_stroke_data(card_id)
            
            if stroke_data:
                print(f"Debug - 加载全部笔迹: 成功加载数据，长度={len(stroke_data)}")
                # 转义JSON字符串，确保安全传递
                stroke_data = stroke_data.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
                # 将笔迹数据发送回JavaScript
                execute_js(f'load_saved_strokes("{stroke_data}", false);') # false表示不只是正面笔迹
            else:
                print(f"Debug - 加载全部笔迹: 未找到笔迹数据")
        except Exception as e:
            print(f"加载全部笔迹数据时出错: {e}")
    
    elif cmd.startswith("ankidraw:load_strokes:"):
        # 向后兼容旧版命令
        try:
            card_id = cmd.split(":", 2)[2]
            print(f"Debug - 兼容模式加载笔迹: 请求卡片ID={card_id}")
            
            # 根据当前显示的是正面还是背面，加载不同的笔迹
            if is_question_side:
                stroke_data = stroke_storage.load_front_stroke_data(card_id)
                side_name = "正面"
            else:
                stroke_data = stroke_storage.load_all_stroke_data(card_id)
                side_name = "全部"
            
            if stroke_data:
                print(f"Debug - 兼容模式加载{side_name}笔迹: 成功加载数据，长度={len(stroke_data)}")
                # 转义JSON字符串，确保安全传递
                stroke_data = stroke_data.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
                # 将笔迹数据发送回JavaScript
                execute_js(f'load_saved_strokes("{stroke_data}", {str(is_question_side).lower()});')
            else:
                print(f"Debug - 兼容模式加载{side_name}笔迹: 未找到笔迹数据")
        except Exception as e:
            print(f"兼容模式加载笔迹数据时出错: {e}")
    
    elif cmd.startswith("ankidraw:get_card_id"):
        # 从Python获取当前卡片ID并发送给JavaScript
        try:
            card_id = get_current_card_id()
            if card_id:
                print(f"Debug - 获取卡片ID: Python获取到ID={card_id}")
                execute_js(f"window.currentCardId = '{card_id}'; console.log('AnkiDraw Debug: 从Python获取到卡片ID:', '{card_id}');")
                # 尝试加载笔迹数据，根据当前是问题还是答案加载不同的笔迹
                if is_question_side:
                    stroke_data = stroke_storage.load_front_stroke_data(card_id)
                    side_name = "正面"
                else:
                    stroke_data = stroke_storage.load_all_stroke_data(card_id)
                    side_name = "全部"
                    
                if stroke_data:
                    print(f"Debug - 获取卡片ID后加载{side_name}笔迹: 成功加载数据，长度={len(stroke_data)}")
                    # 转义JSON字符串，确保安全传递
                    stroke_data = stroke_data.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
                    execute_js(f'load_saved_strokes("{stroke_data}", {str(is_question_side).lower()});')
            else:
                print("Debug - 获取卡片ID: Python无法获取卡片ID")
        except Exception as e:
            print(f"获取卡片ID时出错: {e}")
    
    # 这里可以添加其他命令处理


def assure_plugged_in():
    global ts_default_review_html
    if not mw.reviewer.revHtml == custom:
        ts_default_review_html = mw.reviewer.revHtml
        mw.reviewer.revHtml = custom

def resize_js():
    execute_js("if (typeof resize === 'function') { setTimeout(resize, 101); }");
    
def clear_blackboard():
    assure_plugged_in()

    if ts_state_on:
        execute_js("if (typeof clear_canvas === 'function') { clear_canvas(); }")
        # is qFade the reason for having to wait?
        execute_js("if (typeof resize === 'function') { setTimeout(resize, 101); }");

def get_current_card_id():
    """获取当前正在复习的卡片ID"""
    try:
        if mw.reviewer and mw.reviewer.card:
            return mw.reviewer.card.id
        return None
    except Exception as e:
        print(f"获取卡片ID时出错: {e}")
        return None

# 修改load_card_strokes函数，只加载正面笔迹
def load_card_strokes():
    """清空画布并加载当前卡片正面的笔迹"""
    global is_question_side
    is_question_side = True
    
    # 首先清空画布
    clear_blackboard()
    
    # 检查AnkiDraw是否开启
    if not ts_state_on:
        return
        
    # 获取当前卡片ID
    card_id = get_current_card_id()
    if not card_id:
        return
        
    # 使用JavaScript获取并加载正面笔迹数据
    execute_js(f"if (typeof pycmd === 'function') {{ pycmd('ankidraw:load_front_strokes:{card_id}'); }}")
    # 调整画布大小
    resize_js()

# 添加一个函数处理显示答案时的笔迹加载
def load_answer_strokes():
    """加载当前卡片的所有笔迹（包括背面）"""
    global is_question_side
    is_question_side = False
    
    # 检查AnkiDraw是否开启
    if not ts_state_on:
        return
        
    # 获取当前卡片ID
    card_id = get_current_card_id()
    if not card_id:
        return
    
    # 首先尝试加载正面笔迹，确保它们不会被丢失
    front_strokes = stroke_storage.load_front_stroke_data(card_id)
    
    # 然后加载全部笔迹数据
    all_strokes = stroke_storage.load_all_stroke_data(card_id)
    
    # 如果全部笔迹数据存在但不包含正面笔迹，则需要合并它们
    if all_strokes and front_strokes and len(all_strokes) < len(front_strokes):
        try:
            import json
            # 解析两份数据
            front_data = json.loads(front_strokes)
            all_data = json.loads(all_strokes)
            
            # 确保两者都有预期的结构
            if (isinstance(front_data, dict) and isinstance(all_data, dict) and
                'arrays_of_points' in front_data and 'arrays_of_points' in all_data and
                'line_type_history' in front_data and 'line_type_history' in all_data):
                
                # 合并笔迹数据
                all_data['arrays_of_points'] = front_data['arrays_of_points'] + all_data['arrays_of_points']
                all_data['line_type_history'] = front_data['line_type_history'] + all_data['line_type_history']
                
                # 如果有书法笔画数据，也合并它们
                if 'strokes' in front_data and 'strokes' in all_data:
                    all_data['strokes'] = front_data['strokes'] + all_data['strokes']
                
                # 将合并后的数据再保存
                all_strokes = json.dumps(all_data)
                stroke_storage.save_all_stroke_data(card_id, all_strokes)
                print(f"Debug - 显示答案时: 已合并正面笔迹到全部笔迹，合并后长度={len(all_strokes)}")
        except Exception as e:
            print(f"Debug - 显示答案时合并笔迹出错: {e}")
            import traceback
            traceback.print_exc()
    
    # 使用JavaScript获取并加载全部笔迹数据
    execute_js(f"if (typeof pycmd === 'function') {{ pycmd('ankidraw:load_all_strokes:{card_id}'); }}")
    # 调整画布大小
    resize_js()

def ts_onload():
    """
    Add hooks and initialize menu.
    Call to this function is placed on the end of this file.
    """
    addHook("unloadProfile", ts_save)
    addHook("profileLoaded", ts_load)
    addHook("showQuestion", load_card_strokes)  # 显示问题时加载正面笔迹
    addHook("showAnswer", load_answer_strokes)  # 显示答案时加载全部笔迹
    
    # 在Anki主窗口完全加载后再初始化菜单
    from aqt.gui_hooks import main_window_did_init
    main_window_did_init.append(delayed_menu_setup)
    
    # 连接桥接函数到Anki的pycmd处理系统
    from anki.hooks import wrap
    from aqt.reviewer import Reviewer
    
    # 重写Reviewer._linkHandler来处理来自JavaScript的命令
    def my_link_handler(self, url, _old):
        if url.startswith("ankidraw:"):
            return bridge_command(url)
        return _old(self, url)
    
    Reviewer._linkHandler = wrap(Reviewer._linkHandler, my_link_handler, "around")
    
    # Initialize eraser module
    eraser.setup_eraser()

def delayed_menu_setup():
    """在Anki主窗口完全加载后初始化菜单"""
    # 首先确保语言已加载
    if not hasattr(lang, '_lang_data') or not lang._lang_data:
        lang.init()
    
    # 清理可能存在的旧菜单
    if hasattr(mw, 'addon_view_menu') and mw.addon_view_menu is not None:
        try:
            mw.form.menubar.removeAction(mw.addon_view_menu.menuAction())
            mw.addon_view_menu = None
        except Exception as e:
            print(f"移除旧菜单时出错: {e}")
    
    # 创建新菜单
    ts_setup_menu()
    
    # 更新菜单项状态
    if hasattr(mw, 'addon_view_menu'):
        # 首先确保菜单反映当前的AnkiDraw状态
        ts_menu_switch.setChecked(ts_state_on)
        
        # 然后更新其他菜单项状态
        ts_menu_auto_hide.setChecked(ts_auto_hide)
        ts_menu_auto_hide_pointer.setChecked(ts_auto_hide_pointer)
        ts_menu_small_default.setChecked(ts_default_small_canvas)
        ts_menu_zen_mode.setChecked(ts_zen_mode)
        ts_menu_follow.setChecked(ts_follow)



def blackboard():
    """
    Load and return the HTML, CSS and JS required for the AnkiDraw functionality.
    """
    import os
    
    # 获取插件目录路径
    addon_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 读取HTML文件
    html_path = os.path.join(addon_dir, "templates", "blackboard.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # 读取CSS文件
    css_path = os.path.join(addon_dir, "templates", "blackboard.css")
    with open(css_path, "r", encoding="utf-8") as f:
        css_content = f.read()
    
    # 读取JS文件
    js_path = os.path.join(addon_dir, "templates", "blackboard.js")
    with open(js_path, "r", encoding="utf-8") as f:
        js_content = f.read()
    
    # 读取橡皮擦JS文件
    eraser_js_path = os.path.join(addon_dir, "templates", "eraser.js")
    with open(eraser_js_path, "r", encoding="utf-8") as f:
        eraser_js_content = f.read()
    
    # 获取额外的JavaScript代码，用于在每次卡片显示时获取卡片ID
    card_id_js = """
    // 获取当前卡片ID并加载笔迹数据的功能
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(function() {
            console.log('AnkiDraw Debug: DOM加载完成，开始获取卡片ID');
            
            if (typeof pycmd !== 'function') {
                console.error('AnkiDraw Error: pycmd函数不可用，无法获取卡片ID');
                return;
            }
            
            // 获取卡片ID
            var cardId = '';
            
            try {
                // 尝试从全局变量中获取卡片ID (桌面版Anki)
                if (typeof globalThis !== 'undefined' && typeof globalThis.ankiPlatform !== 'undefined') {
                    console.log('AnkiDraw Debug: 正在使用Anki桌面版方法获取卡片ID');
                }
                
                // 尝试最常见的方法
                if (typeof globalThis !== 'undefined' && typeof globalThis.cardid !== 'undefined') {
                    cardId = globalThis.cardid;
                    console.log('AnkiDraw Debug: 从globalThis.cardid获取到卡片ID:', cardId);
                } 
                // 尝试AnkiDroid方法
                else if (typeof AnkiDroidJS !== 'undefined' && typeof AnkiDroidJS.ankiGetCardId === 'function') {
                    cardId = AnkiDroidJS.ankiGetCardId();
                    console.log('AnkiDraw Debug: 从AnkiDroidJS获取到卡片ID:', cardId);
                }
                // 后备方法: 从页面元素获取
                else {
                    console.log('AnkiDraw Debug: 尝试从页面元素中查找卡片ID');
                    // 有些版本的Anki在特定元素中存储了cardid
                    var metaElements = document.querySelectorAll('meta[name="cardid"]');
                    if (metaElements.length > 0) {
                        cardId = metaElements[0].getAttribute('content');
                        console.log('AnkiDraw Debug: 从meta标签获取到卡片ID:', cardId);
                    }
                }
            } catch (e) {
                console.error('AnkiDraw Error: 获取卡片ID失败', e);
            }
            
            if (cardId) {
                window.currentCardId = cardId;
                console.log('AnkiDraw Debug: 成功设置当前卡片ID:', cardId);
                // 请求加载此卡片的笔迹数据
                pycmd('ankidraw:load_strokes:' + cardId);
            } else {
                // 如果无法获取卡片ID，尝试从Python获取
                console.log('AnkiDraw Debug: 通过Python获取卡片ID');
                pycmd('ankidraw:get_card_id');
            }
        }, 500); // 延迟执行，确保DOM已完全加载
    });
    """
    
    # 替换CSS文件中的占位符
    css_content = css_content.replace('/*TOOLBAR_LOCATION_PLACEHOLDER*/', 
                                       get_css_for_toolbar_location(ts_location, ts_x_offset, ts_y_offset, ts_orient_vertical, ts_small_width, ts_small_height, ts_background_color))
    css_content = css_content.replace('/*ZEN_MODE_PLACEHOLDER*/', get_css_for_zen_mode(ts_zen_mode))
    css_content = css_content.replace('/*AUTO_HIDE_POINTER_PLACEHOLDER*/', get_css_for_auto_hide_pointer(ts_auto_hide_pointer))
    css_content = css_content.replace('/*AUTO_HIDE_PLACEHOLDER*/', get_css_for_auto_hide(ts_auto_hide, ts_zen_mode))
    css_content = css_content.replace('/*OPACITY_PLACEHOLDER*/', str(ts_opacity))
    
    # 替换JS文件中的占位符
    js_content = js_content.replace('/*VISIBILITY_PLACEHOLDER*/', ts_default_VISIBILITY)
    js_content = js_content.replace('/*PERFECT_FREEHAND_PLACEHOLDER*/', "false")  # 强制禁用完美手写
    js_content = js_content.replace('/*CALLIGRAPHY_PLACEHOLDER*/', "false")  # 强制禁用书法家
    js_content = js_content.replace('/*CONVERT_DOT_STROKES_PLACEHOLDER*/', str(ts_ConvertDotStrokes).lower())
    js_content = js_content.replace('/*SMALL_CANVAS_PLACEHOLDER*/', str(ts_default_small_canvas).lower())
    js_content = js_content.replace('/*FOLLOW_PLACEHOLDER*/', str(ts_follow).lower())
    
    # 将获取卡片ID和加载笔迹的代码添加到JS代码末尾
    js_content = js_content + card_id_js
    
    # 替换eraser.js中的"Eraser Size"文本
    eraser_js_content = eraser_js_content.replace('sliderTitle.textContent = \'Eraser Size\';', 
                                                 f'sliderTitle.textContent = \'{lang.get_text("eraser_size", "Eraser Size")}\';')
    
    # 替换eraser.js中的"Box Selection"文本
    eraser_js_content = eraser_js_content.replace('label.textContent = \'Box Selection\';', 
                                                 f'label.textContent = \'{lang.get_text("eraser_box_selection", "Box Selection")}\';')
    
    # 替换blackboard.js中的直线样式文本
    js_content = js_content.replace('sliderTitle.textContent = \'Line Style\';', 
                                   f'sliderTitle.textContent = \'{lang.get_text("line_style", "Line Style")}\';')
    js_content = js_content.replace('text.textContent = \'Solid\';', 
                                   f'text.textContent = \'{lang.get_text("line_style_solid", "Solid")}\';')
    js_content = js_content.replace('text.textContent = \'Dashed\';', 
                                   f'text.textContent = \'{lang.get_text("line_style_dashed", "Dashed")}\';')
    js_content = js_content.replace('text.textContent = \'Wavy\';', 
                                   f'text.textContent = \'{lang.get_text("line_style_wavy", "Wavy")}\';')
    
    # 替换HTML文件中的橡皮擦图标SVG代码
    with open(os.path.join(addon_dir, "templates", "eraser_icon.svg"), "r", encoding="utf-8") as f:
        eraser_svg = f.read()
    html_content = html_content.replace('<!-- ERASER_ICON_SVG_PLACEHOLDER -->', eraser_svg)
    
    # 添加恢复窗口大小按钮的JavaScript函数
    restore_window_js = """
    // 恢复窗口大小函数
    function restore_window_size() {
        try {
            console.log('AnkiDraw Debug: 尝试恢复窗口大小');
            
            // 确保有卡片ID
            if (!currentCardId) {
                console.error('AnkiDraw Error: 恢复窗口大小失败，没有卡片ID');
                return;
            }
            
            // 通过pycmd发送命令到Python端
            if (typeof pycmd === 'function') {
                console.log('AnkiDraw Debug: 发送恢复窗口大小命令，卡片ID:', currentCardId);
                pycmd('ankidraw:restore_window_size:' + currentCardId);
            } else {
                console.error('AnkiDraw Error: pycmd函数不可用，无法恢复窗口大小');
            }
        } catch (e) {
            console.error('AnkiDraw Error: 恢复窗口大小时出错', e);
        }
    }
    """
    
    # 将恢复窗口大小函数添加到JS内容中
    js_content = js_content + restore_window_js
    
    # 替换HTML文件中的工具栏按钮提示文本，实现多语言支持
    html_content = html_content.replace('title="Toggle visiblity (, comma)"', 
                                       f'title="{lang.get_text("tooltip_toggle_visibility", "Toggle visiblity (, comma)")}"')
    html_content = html_content.replace('title="Toggle Eraser (Alt + Q)"', 
                                       f'title="{lang.get_text("tooltip_toggle_eraser", "Toggle Eraser (Alt + Q)")}"')
    html_content = html_content.replace('title="Line Tool (Alt + L)"', 
                                       f'title="{lang.get_text("tooltip_line_tool", "Line Tool (Alt + L)")}"')
    html_content = html_content.replace('title="Rectangle Tool (Alt + R)"', 
                                       f'title="{lang.get_text("tooltip_rectangle_tool", "Rectangle Tool (Alt + R)")}"')
    html_content = html_content.replace('title="Perfect Freehand (Alt + x)"', 
                                       f'title="{lang.get_text("tooltip_perfect_freehand", "Perfect Freehand (Alt + x)")}"')
    html_content = html_content.replace('title="Toggle calligrapher (Alt + c)"', 
                                       f'title="{lang.get_text("tooltip_toggle_calligrapher", "Toggle calligrapher (Alt + c)")}"')
    html_content = html_content.replace('title="Undo the last stroke (Alt + z)"', 
                                       f'title="{lang.get_text("tooltip_undo_last_stroke", "Undo the last stroke (Alt + z)")}"')
    html_content = html_content.replace('title="Clean canvas (. dot)"', 
                                       f'title="{lang.get_text("tooltip_clean_canvas", "Clean canvas (. dot)")}"')
    html_content = html_content.replace('title="Toggle fullscreen canvas(Alt + b)"', 
                                       f'title="{lang.get_text("tooltip_toggle_fullscreen", "Toggle fullscreen canvas(Alt + b)")}"')
    # 添加窗口大小按钮的多语言支持
    html_content = html_content.replace('title="Restore to writing window size"', 
                                       f'title="{lang.get_text("tooltip_restore_window_size", "Restore to writing window size")}"')
    
    # 构建完整的HTML，确保eraser.js在主JS之前加载
    return f"""
<style>
{css_content}
</style>

{html_content}

<script>
// 先加载eraser.js内容
{eraser_js_content}

// 设置保存的橡皮擦大小
updateEraserSize({eraser.eraser_size});

// 再加载主JS
{js_content}
</script>
"""


def custom(*args, **kwargs):
    global ts_state_on
    default = ts_default_review_html(*args, **kwargs)
    if not ts_state_on:
        return default
    output = (
        default +
        blackboard() + 
        "<script>color = '" + ts_color + "'</script>" +
        "<script>line_width = '" + str(ts_line_width) + "'</script>" +
        "<script>lineColor = '" + ts_line_color + "'</script>" +
        "<script>lineWidth = " + str(ts_line_line_width) + "</script>" +
        "<script>rectangleColor = '" + ts_rectangle_color + "'</script>" +
        "<script>rectangleWidth = " + str(ts_rectangle_line_width) + "</script>" +
        "<script>if (typeof initializeRectangleSettings === 'function') { initializeRectangleSettings('" + ts_rectangle_color + "', " + str(ts_rectangle_line_width) + "); }</script>"
    )
    return output


mw.reviewer.revHtml = custom


def checkProfile():
    if not ts_profile_loaded:
        showWarning(TS_ERROR_NO_PROFILE)
        return False


def ts_on():
    """
    Turn on AnkiDraw.
    Function modifies the reviewer.revHtml
    to inject blackboard's HTML and JS.
    """
    checkProfile()

    global ts_state_on
    ts_state_on = True
    
    # 只有在菜单已经创建后才设置菜单项的状态
    if 'ts_menu_switch' in globals() and ts_menu_switch is not None:
        ts_menu_switch.setChecked(True)
    
    # 初始化橡皮擦状态
    eraser.eraser_active = False
    
    return True


def ts_off():
    """
    Turn off
    """
    checkProfile()

    global ts_state_on
    ts_state_on = False
    
    # 只有在菜单已经创建后才设置菜单项的状态
    if 'ts_menu_switch' in globals() and ts_menu_switch is not None:
        ts_menu_switch.setChecked(False)
    
    return True

@slot()
def ts_dots():
    """
    Switch dot conversion.
    """
    global ts_ConvertDotStrokes
    ts_ConvertDotStrokes = not ts_ConvertDotStrokes
    execute_js("convertDotStrokes = " + str(ts_ConvertDotStrokes).lower() + ";")
    execute_js("if (typeof resize === 'function') { resize(); }")


@slot()
def ts_change_auto_hide_settings():
    """
    Switch auto hide toolbar setting.
    """
    global ts_auto_hide
    ts_auto_hide = not ts_auto_hide
    ts_switch()
    ts_switch()

@slot()
def ts_change_follow_settings():
    """
    Switch whiteboard follow screen.
    """
    global ts_follow
    ts_follow = not ts_follow
    execute_js("fullscreen_follow = " + str(ts_follow).lower() + ";")
    execute_js("if (typeof resize === 'function') { resize(); }")

@slot()
def ts_change_small_default_settings():
    """
    Switch default small canvas mode setting.
    """
    global ts_default_small_canvas
    ts_default_small_canvas = not ts_default_small_canvas
    ts_switch()
    ts_switch()

@slot()
def ts_change_zen_mode_settings():
    """
    Switch default zen mode setting.
    """
    global ts_zen_mode
    ts_zen_mode = not ts_zen_mode
    ts_switch()
    ts_switch()
    
@slot()
def ts_change_auto_hide_pointer_settings():
    """
    Switch auto hide pointer setting.
    """
    global ts_auto_hide_pointer
    ts_auto_hide_pointer = not ts_auto_hide_pointer
    ts_switch()
    ts_switch()
      

@slot()
def ts_switch():
    """
    Switch AnkiDraw.
    """

    if ts_state_on:
        ts_off()
    else:
        ts_on()


    # Reload current screen.

    if mw.state == "review":
        #mw.moveToState('overview')
        mw.moveToState('review')
    if mw.state == "deckBrowser":
        mw.deckBrowser.refresh()
    if mw.state == "overview":
        mw.overview.refresh()

def ts_setup_menu():
    """
    Initialize menu. 
    """
    global ts_menu_switch, ts_menu_auto_hide, ts_menu_auto_hide_pointer, ts_menu_small_default, ts_menu_zen_mode, ts_menu_follow, ts_menu_eraser, ts_menu_line, ts_menu_line_color, ts_menu_line_width, ts_menu_rectangle, ts_menu_rectangle_color, ts_menu_rectangle_width, ts_menu_toolbar_control, ts_menu_language, ts_menu_clear_all_strokes, ts_menu_stroke_manager, ts_menu_toolbar_settings, ts_menu_restore_window_size, ts_menu_hotkey_config
    
    # 确保工具栏配置已加载
    toolbar_control.load_toolbar_config()
    
    # 确保快捷键配置已加载
    hotkey_manager.setup_hotkey_config()
    
    # 注意：语言初始化已移至ts_load()函数中，确保在配置加载后执行
    
    try:
        mw.addon_view_menu
    except AttributeError:
        mw.addon_view_menu = QMenu("""&AnkiDraw""", mw)
        mw.form.menubar.insertMenu(mw.form.menuTools.menuAction(),
                                    mw.addon_view_menu)

    # Create menu items
    ts_menu_switch = QAction(lang.get_text("menu_enable_ankidraw", "&Enable Ankidraw"), mw, checkable=True)
    ts_menu_auto_hide = QAction(lang.get_text("menu_auto_hide_toolbar", "Auto &hide toolbar when drawing"), mw, checkable=True)
    ts_menu_auto_hide_pointer = QAction(lang.get_text("menu_auto_hide_pointer", "Auto &hide pointer when drawing"), mw, checkable=True)
    ts_menu_follow = QAction(lang.get_text("menu_follow_when_scrolling", "&Follow when scrolling (faster on big cards)"), mw, checkable=True)
    ts_menu_small_default = QAction(lang.get_text("menu_small_canvas_default", "&Small Canvas by default"), mw, checkable=True)
    ts_menu_zen_mode = QAction(lang.get_text("menu_enable_zen_mode", "Enable Zen Mode(hide toolbar until this is disabled)"), mw, checkable=True)
    ts_menu_color = QAction(lang.get_text("menu_set_pen_color", "Set &pen color"), mw)
    ts_menu_width = QAction(lang.get_text("menu_set_pen_width", "Set pen &width"), mw)
    ts_menu_opacity = QAction(lang.get_text("menu_set_pen_opacity", "Set pen &opacity"), mw)
    ts_menu_toolbar_settings = QAction(lang.get_text("menu_toolbar_canvas_location", "&Toolbar and canvas location settings"), mw)
    
    # 新增恢复窗口大小菜单项
    ts_menu_restore_window_size = QAction(lang.get_text("menu_restore_window_size", "Restore Writing Window Size"), mw)
    ts_menu_restore_window_size.triggered.connect(restore_writing_window_size)
    
    # 添加新的笔迹管理菜单项
    ts_menu_stroke_manager = QAction(lang.get_text("menu_stroke_management", "Pen Trace Management"), mw)
    ts_menu_stroke_manager.triggered.connect(stroke_manager.show_stroke_manager)
    
    # 添加快捷键设置菜单项
    ts_menu_hotkey_config = QAction(lang.get_text("menu_hotkey_config", "自定义快捷键设置"), mw)
    ts_menu_hotkey_config.triggered.connect(hotkey_manager.show_hotkey_config_dialog)
    
    # 其他菜单项
    ts_menu_toolbar_control = QAction(lang.get_text("menu_toolbar_button_visibility", "Toolbar Button Visibility Control"), mw)
    
    # 直线工具相关菜单项
    ts_menu_line = QAction(lang.get_text("menu_toggle_line_tool", "Toggle &Line Tool"), mw, checkable=True)
    ts_menu_line.setShortcut(QKeySequence("Alt+L"))
    
    # 设置直线颜色和宽度
    ts_menu_line_color = QAction(lang.get_text("menu_set_line_color", "Set line &color"), mw)
    ts_menu_line_width = QAction(lang.get_text("menu_set_line_width", "Set line w&idth"), mw)
    
    # 矩形工具相关菜单项
    ts_menu_rectangle = QAction(lang.get_text("menu_toggle_rectangle_tool", "Toggle &Rectangle Tool"), mw, checkable=True)
    ts_menu_rectangle.setShortcut(QKeySequence("Alt+R"))
    
    # 设置矩形颜色和宽度
    ts_menu_rectangle_color = QAction(lang.get_text("menu_set_rectangle_color", "Set rectangle &color"), mw)
    ts_menu_rectangle_width = QAction(lang.get_text("menu_set_rectangle_width", "Set rectangle w&idth"), mw)
    
    # 添加语言设置菜单项 - 固定显示双语文本
    ts_menu_language = QAction("Language/语言设置", mw)
    
    # 原清除所有笔迹菜单项不再直接添加到菜单，而是由笔迹管理面板提供
    ts_menu_clear_all_strokes = QAction(lang.get_text("menu_clear_all_strokes", "Clear All Saved Strokes"), mw)
    ts_menu_clear_all_strokes.triggered.connect(ts_clear_all_saved_strokes)
    
    # 设置菜单项的初始状态
    ts_menu_switch.setChecked(ts_state_on)
    ts_menu_auto_hide.setChecked(ts_auto_hide)
    ts_menu_auto_hide_pointer.setChecked(ts_auto_hide_pointer)
    ts_menu_follow.setChecked(ts_follow)
    ts_menu_small_default.setChecked(ts_default_small_canvas)
    ts_menu_zen_mode.setChecked(ts_zen_mode)
    
    # 连接信号
    ts_menu_switch.triggered.connect(ts_switch)
    ts_menu_auto_hide.triggered.connect(ts_change_auto_hide_settings)
    ts_menu_auto_hide_pointer.triggered.connect(ts_change_auto_hide_pointer_settings)
    ts_menu_follow.triggered.connect(ts_change_follow_settings)
    ts_menu_small_default.triggered.connect(ts_change_small_default_settings)
    ts_menu_zen_mode.triggered.connect(ts_change_zen_mode_settings)
    ts_menu_color.triggered.connect(ts_change_color)
    ts_menu_width.triggered.connect(ts_change_width)
    ts_menu_opacity.triggered.connect(ts_change_opacity)
    ts_menu_line.triggered.connect(eraser.toggle_line_tool)
    ts_menu_line_color.triggered.connect(ts_change_line_color)
    ts_menu_line_width.triggered.connect(ts_change_line_width)
    ts_menu_rectangle.triggered.connect(eraser.toggle_rectangle_tool)
    ts_menu_rectangle_color.triggered.connect(ts_change_rectangle_color)
    ts_menu_rectangle_width.triggered.connect(ts_change_rectangle_width)
    ts_menu_toolbar_settings.triggered.connect(ts_change_toolbar_settings)
    ts_menu_toolbar_control.triggered.connect(toolbar_control.show_toolbar_control_dialog)
    ts_menu_language.triggered.connect(lang.show_language_select_dialog)
    
    # 为菜单添加项目
    mw.addon_view_menu.addAction(ts_menu_switch)
    mw.addon_view_menu.addSeparator()
    
    # 默认视图选项
    view_submenu = QMenu(lang.get_text("view_settings", "&View Settings"), mw)
    view_submenu.addAction(ts_menu_auto_hide)
    view_submenu.addAction(ts_menu_auto_hide_pointer)
    view_submenu.addAction(ts_menu_follow)
    view_submenu.addAction(ts_menu_small_default)
    view_submenu.addAction(ts_menu_zen_mode)
    
    # 工具菜单
    tool_submenu = QMenu(lang.get_text("tool_settings", "&Tool Settings"), mw)
    
    # 普通画笔设置
    pen_submenu = QMenu(lang.get_text("pen_settings", "&Pen Settings"), tool_submenu)
    pen_submenu.addAction(ts_menu_color)
    pen_submenu.addAction(ts_menu_width)
    pen_submenu.addAction(ts_menu_opacity)
    tool_submenu.addMenu(pen_submenu)
    
    # 直线工具设置
    line_submenu = QMenu(lang.get_text("menu_toggle_line_tool", "&Line Tool"), tool_submenu)
    line_submenu.addAction(ts_menu_line)
    line_submenu.addAction(ts_menu_line_color)
    line_submenu.addAction(ts_menu_line_width)
    tool_submenu.addMenu(line_submenu)
    
    # 矩形工具设置
    rectangle_submenu = QMenu(lang.get_text("menu_toggle_rectangle_tool", "&Rectangle Tool"), tool_submenu)
    rectangle_submenu.addAction(ts_menu_rectangle)
    rectangle_submenu.addAction(ts_menu_rectangle_color)
    rectangle_submenu.addAction(ts_menu_rectangle_width)
    tool_submenu.addMenu(rectangle_submenu)
    
    # 添加子菜单到主菜单
    mw.addon_view_menu.addMenu(view_submenu)
    mw.addon_view_menu.addMenu(tool_submenu)
    mw.addon_view_menu.addSeparator()
    
    # 工具栏设置
    mw.addon_view_menu.addAction(ts_menu_toolbar_settings)
    mw.addon_view_menu.addAction(ts_menu_toolbar_control)
    mw.addon_view_menu.addAction(ts_menu_hotkey_config)  # 添加快捷键设置菜单项
    mw.addon_view_menu.addSeparator()
    
    # 添加笔迹管理菜单
    mw.addon_view_menu.addAction(ts_menu_stroke_manager)
    mw.addon_view_menu.addSeparator()
    
    # 语言设置
    mw.addon_view_menu.addAction(ts_menu_language)


TS_ERROR_NO_PROFILE = "No profile loaded"

#
# ONLOAD SECTION
#

# 初始化工具栏控制功能
toolbar_control.setup_toolbar_control()

ts_onload()

# 添加清除所有保存笔迹数据的函数
@slot()
def ts_clear_all_saved_strokes():
    """清除所有保存的笔迹数据"""
    from aqt.utils import askUser, showInfo
    import shutil
    import os
    
    # 询问用户是否确定要清除所有笔迹数据
    if askUser(lang.get_text("dialog_clear_all_strokes", "确定要删除所有保存的笔迹数据吗？此操作不可撤销。")):
        try:
            # 获取笔迹数据文件夹
            strokes_folder = stroke_storage.get_stroke_data_path()
            
            # 如果文件夹存在，删除并重建
            if os.path.exists(strokes_folder):
                shutil.rmtree(strokes_folder)
                os.makedirs(strokes_folder)
                
            showInfo(lang.get_text("dialog_clear_success", "所有笔迹数据已成功清除。"))
        except Exception as e:
            showInfo(lang.get_text("dialog_clear_error", f"清除笔迹数据时出错: {e}"))

# 新增恢复窗口大小的功能
@slot()
def restore_writing_window_size():
    """
    恢复到卡片书写时的窗口大小
    """
    try:
        card_id = get_current_card_id()
        if not card_id:
            print("Debug - 恢复窗口大小: 无法获取当前卡片ID")
            from aqt.utils import tooltip
            tooltip("无法获取当前卡片ID，请确保您在复习中")
            return
            
        # 获取系统信息
        import platform
        is_windows = platform.system() == "Windows"
        
        # 执行JavaScript获取当前DPI
        dpr_js = "window.devicePixelRatio || 1"
        dpr = 1.0
        
        try:
            dpr_str = execute_js(f"return {dpr_js};")
            if dpr_str:
                dpr = float(dpr_str)
        except:
            pass
            
        # 构建系统信息参数
        system_info = f":{dpr}:{'win' if is_windows else 'other'}"
            
        # 发送命令到JS
        execute_js(f"if (typeof pycmd === 'function') {{ pycmd('ankidraw:restore_window_size:{card_id}{system_info}'); }}")
    except Exception as e:
        print(f"恢复窗口大小出错: {e}")
        import traceback
        traceback.print_exc()

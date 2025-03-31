import sys
import os
import toml
import json  # 导入 json 模块
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QLabel,
    QMessageBox, QFileDialog, QTabWidget, QComboBox
)

from processor import Process

class ModuleManagerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Surge Module Manager")
        self.setGeometry(100, 100, 900, 700) # 适当增加窗口高度

        self.central_widget = QWidget() # 创建中央小部件
        self.setCentralWidget(self.central_widget) # 设置中央小部件
        self.layout = QVBoxLayout(self.central_widget) # 创建布局并设置为中央小部件的布局 V为垂直布局

        self.config_file = "config.toml" # 存放路径的 TOML 配置文件
        self.default_modules_info_dir = os.path.join(os.path.dirname(__file__), "modules.json") # 默认的模块信息 JSON 文件
        self.default_modules_storage_dir = os.path.join(os.path.dirname(__file__), "Modules") # 默认的模块存放路径
        self.modules_storage_dir, self.modules_info_dir = self.load_module_path() # 加载模块存放路径和模块信息 JSON 文件路径
        self.process = Process(self.modules_info_dir, self.modules_storage_dir) # 创建 Process 实例

        self.module_data = self.load_module_data_from_json() # 从 JSON 文件加载模块数据

        self.init_ui()

    def init_ui(self):
        self.tab_widget = QTabWidget() # 创建标签页
        self.layout.addWidget(self.tab_widget) # 将标签页添加到布局中

        # 模块管理标签页
        self.modules_tab = QWidget()
        self.tab_widget.addTab(self.modules_tab, "模块管理")
        self.init_modules_tab()

        # 新增模块标签页
        self.add_module_tab = QWidget()
        self.tab_widget.addTab(self.add_module_tab, "新增模块")
        self.init_add_module_tab()

    def init_modules_tab(self):
        modules_layout = QVBoxLayout(self.modules_tab) # 创建模块管理标签页的布局(垂直布局)

        # 模块路径
        path_layout = QHBoxLayout() # 创建水平布局
        path_label = QLabel("模块存放路径:") # 标签
        self.path_display_label = QLabel(self.modules_storage_dir) # 创建标签显示模块存放路径
        change_path_button = QPushButton("选择文件夹") # 按钮
        change_path_button.clicked.connect(self.change_module_path) # 连接按钮点击事件
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_display_label)
        path_layout.addWidget(change_path_button) # 将标签和按钮添加到水平布局中
        modules_layout.addLayout(path_layout) # 将模块路径信息的水平布局添加到模块管理标签页的布局中
        # 模块信息 JSON 文件显示和选择
        json_path_layout = QHBoxLayout()
        json_path_label = QLabel("模块信息 JSON 文件:")
        self.json_path_display_label = QLabel(self.modules_info_dir)
        change_json_path_button = QPushButton("选择文件")
        change_json_path_button.clicked.connect(self.change_module_info_path)
        json_path_layout.addWidget(json_path_label)
        json_path_layout.addWidget(self.json_path_display_label)
        json_path_layout.addWidget(change_json_path_button)
        modules_layout.addLayout(json_path_layout) # 将模块信息 JSON 文件的水平布局添加到模块管理标签页的布局中

        # 分类筛选
        filter_layout = QHBoxLayout()
        filter_label = QLabel("筛选分类:")
        self.category_filter_combo = QComboBox() # 创建下拉框
        self.category_filter_combo.addItem("全部")
        # unique_categories = sorted(list(set(module['category'] for module in self.module_data)))
        unique_categories = sorted(self.process.getCategories()) # 从 Process 实例获取分类
        self.category_filter_combo.addItems(unique_categories)
        self.category_filter_combo.currentIndexChanged.connect(self.filter_modules_by_category) # 连接下拉框选择变化事件
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.category_filter_combo)
        filter_layout.addStretch(1) # 使筛选框靠左
        modules_layout.addLayout(filter_layout)

        self.module_table = QTableWidget() # 创建表格
        self.module_table.setColumnCount(5) # 设置列数
        self.module_table.setHorizontalHeaderLabels(["名称", "链接", "系统", "分类", "操作"])
        self.module_table.itemChanged.connect(self.module_table_item_changed) # 连接 itemChanged 信号
        self.populate_module_table()
        modules_layout.addWidget(self.module_table)

        # 保存修改按钮
        save_button_layout = QHBoxLayout()
        save_button = QPushButton("保存修改")
        save_button.clicked.connect(self.save_module_data_to_json)
        save_button_layout.addWidget(save_button)
        modules_layout.addLayout(save_button_layout)

        batch_actions_layout = QHBoxLayout()
        self.batch_delete_button = QPushButton("批量删除")
        self.batch_delete_button.clicked.connect(self.batch_delete_modules)
        self.batch_update_button = QPushButton("批量更新")
        self.batch_update_button.clicked.connect(self.batch_update_modules)
        batch_actions_layout.addWidget(self.batch_delete_button)
        batch_actions_layout.addWidget(self.batch_update_button)
        modules_layout.addLayout(batch_actions_layout)

    def load_module_path(self):
        """从 TOML 配置文件加载模块存放路径"""
        module_path = self.default_modules_storage_dir
        module_info_path = self.default_modules_info_dir
        try:
            with open(self.config_file, 'r') as f:
                config = toml.load(f)
                module_path = config.get('module_path', self.default_modules_storage_dir)
                module_info_path = config.get('module_info_path', self.default_modules_info_dir)
                if not os.path.isdir(module_path):
                    module_path = self.default_modules_storage_dir
                if not os.path.isfile(module_info_path):
                    module_info_path = self.default_modules_info_dir
        except FileNotFoundError:
            pass
        except toml.TomlDecodeError as e:
            print(f"解析 TOML 文件失败: {e}")
        except Exception as e:
            print(f"加载模块路径时发生错误: {e}")
        return module_path, module_info_path

    def save_module_path(self, data: dict):
        """将模块存放路径保存到 TOML 配置文件"""
        try:
            with open(self.config_file, 'r') as f:
                config = toml.load(f)
        except FileNotFoundError:
            config = {}
        except toml.TomlDecodeError as e:
            print(f"解析 TOML 文件失败: {e}")
            config = {}
        except Exception as e:
            print(f"加载配置文件时发生错误: {e}")
            config = {}

        config.update(data) # 更新配置
        try:
            with open(self.config_file, 'w') as f:
                toml.dump(config, f)
        except Exception as e:
            print(f"保存模块路径到 TOML 文件失败: {e}")

    def load_module_data_from_json(self):
        """从 JSON 文件加载模块数据"""
        try:
            with open(self.modules_info_dir, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        except FileNotFoundError:
            print(f"模块信息 JSON 文件未找到: {self.modules_info_dir}")
            return []
        except json.JSONDecodeError as e:
            print(f"解析模块信息 JSON 文件失败: {e}")
            return []
        except Exception as e:
            print(f"加载模块信息时发生错误: {e}")
            return []

    def save_module_data_to_json(self):
        """将模块数据保存到 JSON 文件"""
        try:
            with open(self.modules_info_dir, 'w', encoding='utf-8') as f:
                json.dump(self.module_data, f, indent=4, ensure_ascii=False)
            QMessageBox.information(self, "保存成功", "模块信息已保存。")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存模块信息失败: {e}")

    def module_table_item_changed(self, item):
        """表格内容改变时触发"""
        row = item.row()
        col = item.column()
        new_value = item.text()
        if 0 <= row < len(self.module_data):
            module = self.module_data[row]
            headers = ["名称", "链接", "系统", "分类"]
            header = headers[col]

            if header == "名称":
                old_name = module.get('name', '')
                if old_name != new_value:
                    old_file_path = os.path.join(self.modules_storage_dir, old_name + '.sgmodule')
                    # new_file_path = os.path.join(self.modules_storage_dir, new_value + '.sgmodule')
                    if os.path.exists(old_file_path):
                        # os.rename(old_file_path, new_file_path)
                        res = self.process.modifyFilename(old_name, new_value)
                        if res:
                            print(f"重命名文件: {old_name} -> {new_value}")
                        else:
                            QMessageBox.warning(self, "重命名文件失败")
                    module['name'] = new_value
            elif header == "链接":
                module['link'] = new_value
            elif header == "系统":
                module['system'] = new_value
            elif header == "分类":
                module['category'] = new_value

    def change_module_path(self):
        new_path = QFileDialog.getExistingDirectory(self, "选择模块存放路径", self.modules_storage_dir)
        if new_path:
            self.modules_storage_dir = new_path
            self.path_display_label.setText(self.modules_storage_dir)
            self.save_module_path({"module_path": self.modules_storage_dir}) # 保存新路径到 TOML 文件
            print(f"模块存放路径已更改为: {self.modules_storage_dir}")
            self.process.modules_storage_dir = self.modules_storage_dir # 更新 Process 实例的路径
            # 不在此处重新加载模块数据，因为模块数据是从 JSON 文件加载的

    def change_module_info_path(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择模块信息 JSON 文件", ".", "JSON Files (*.json)")
        if file_path:
            self.modules_info_dir = file_path
            self.json_path_display_label.setText(self.modules_info_dir)
            self.save_module_path({'module_info_path': self.modules_info_dir})
            print(f"模块信息 JSON 文件已更改为: {self.modules_info_dir}")
            self.process.modules_info_dir = self.modules_info_dir # 更新 Process 实例的路径
            self.module_data = self.load_module_data_from_json() # 重新加载模块数据
            self.update_category_filter() # 更新分类筛选
            self.populate_module_table() # 重新填充表格

    def update_category_filter(self):
        """更新分类筛选下拉框的内容"""
        self.category_filter_combo.clear()
        self.category_filter_combo.addItem("全部")
        unique_categories = sorted(list(set(module['category'] for module in self.module_data)))
        self.category_filter_combo.addItems(unique_categories)

    def filter_modules_by_category(self, index):
        selected_category = self.category_filter_combo.currentText()
        if selected_category == "全部":
            self.module_data = self.load_module_data_from_json() # 重新加载所有数据
        else:
            all_data = self.load_module_data_from_json() # 从 JSON 加载完整数据
            self.module_data = [module for module in all_data if module['category'] == selected_category]
        self.populate_module_table()

    def populate_module_table(self):
        """
        填充模块表格
        """
        self.module_table.setRowCount(len(self.module_data))
        for row, module in enumerate(self.module_data):
            name_item = QTableWidgetItem(module['name'])
            link_item = QTableWidgetItem(module['link'])
            system_item = QTableWidgetItem(module.get('system', '未知'))
            category_item = QTableWidgetItem(module['category'])

            self.module_table.setItem(row, 0, name_item)
            self.module_table.setItem(row, 1, link_item)
            self.module_table.setItem(row, 2, system_item)
            self.module_table.setItem(row, 3, category_item)

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)

            delete_button = QPushButton("删除")
            delete_button.clicked.connect(lambda checked, r=row: self.delete_module(r))
            update_button = QPushButton("更新")
            update_button.clicked.connect(lambda checked, r=row: self.update_module(r))
            view_button = QPushButton("查看内容")
            view_button.clicked.connect(lambda checked, r=row: self.view_module_content(r))

            actions_layout.addWidget(delete_button)
            actions_layout.addWidget(update_button)
            actions_layout.addWidget(view_button)

            self.module_table.setCellWidget(row, 4, actions_widget)

        self.module_table.resizeColumnsToContents()

    def delete_module(self, row):
        module_name = self.module_data[row]['name']
        reply = QMessageBox.question(self, '删除模块',
            f"确定要删除模块 '{module_name}' 吗?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            print(f"删除模块: {module_name}")
            self.process.delete_module(self.module_data[row]) # 删除模块
            self.module_data.pop(row)
            self.populate_module_table()

    def update_module(self, row):
        module = self.module_data[row]
        module_name = module['name']
        print(f"更新模块: {module_name}")
        update_res = self.process.download_module(module) # 更新模块
        if update_res:
            QMessageBox.information(self, "更新模块", f"已更新模块 '{module_name}'")
        else:
            QMessageBox.warning(self, "更新模块", f"模块 '{module_name}' 更新失败。")

    def view_module_content(self, row):
        module = self.module_data[row]
        module_name = module['name']
        module_path = os.path.join(self.modules_storage_dir, module_name + '.sgmodule')

        if module_path and os.path.exists(module_path):
            try:
                with open(module_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                dialog = QMessageBox()
                dialog.setWindowTitle(f"模块内容: {module_name}")
                dialog.setText(content)
                dialog.exec()
            except FileNotFoundError:
                QMessageBox.warning(self, "查看内容", f"模块 '{module_name}' 的文件未找到。")
            except Exception as e:
                QMessageBox.critical(self, "查看内容", f"查看模块 '{module_name}' 内容时发生错误: {e}")
        else:
            QMessageBox.warning(self, "查看内容", f"模块 '{module_name}' 的本地路径未知或文件不存在。")

    def batch_delete_modules(self):
        selected_rows = sorted(set(item.row() for item in self.module_table.selectedItems()), reverse=True)
        if not selected_rows:
            QMessageBox.warning(self, "批量删除", "请选择要删除的模块。")
            return

        modules_to_delete = [self.module_data[row] for row in selected_rows]
        module_names_to_delete = [module['name'] for module in modules_to_delete]
        reply = QMessageBox.question(self, '批量删除模块',
            f"确定要批量删除以下模块吗?\n\n{', '.join(module_names_to_delete)}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            print(f"批量删除模块: {module_names_to_delete}")
            for module in list(modules_to_delete): # 遍历副本以安全删除
                if module in self.module_data:
                    self.process.delete_module(module) # 删除模块
                    self.module_data.remove(module)
            self.populate_module_table()

    def batch_update_modules(self):
        selected_rows = [item.row() for item in self.module_table.selectedItems()]
        if not selected_rows:
            QMessageBox.warning(self, "批量更新", "请选择要更新的模块。")
            return

        module_names_to_update = [self.module_data[row]['name'] for row in selected_rows]
        print(f"批量更新模块: {module_names_to_update}")
        failed_res = []
        for row_index in selected_rows:
            module = self.module_data[row_index]
            update_res = self.process.download_module(module)
            if not update_res:
                failed_res.append(module["name"])
        if failed_res:
            QMessageBox.warning(self, "批量更新", f"以下模块更新失败: {', '.join(failed_res)}")
        else:
            QMessageBox.information(self, "批量更新", "所有选中的模块已成功更新。")

    def init_add_module_tab(self):
        add_layout = QVBoxLayout(self.add_module_tab)

        name_layout = QHBoxLayout()
        name_label = QLabel("名称:")
        self.name_input = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        add_layout.addLayout(name_layout)

        link_layout = QHBoxLayout()
        link_label = QLabel("链接:")
        self.link_input = QLineEdit()
        link_layout.addWidget(link_label)
        link_layout.addWidget(self.link_input)
        add_layout.addLayout(link_layout)

        system_layout = QHBoxLayout()
        system_label = QLabel("系统:")
        self.system_combo = QComboBox()
        self.system_combo.addItems(["iOS", "macOS", "iOS&macOS"])
        system_layout.addWidget(system_label)
        system_layout.addWidget(self.system_combo)
        add_layout.addLayout(system_layout)

        category_layout = QHBoxLayout()
        category_label = QLabel("分类:")
        self.category_combo = QComboBox()
        existing_categories = sorted(list(set(module['category'] for module in self.module_data))) # 从现有数据加载分类
        self.category_combo.addItems(existing_categories)
        self.category_combo.setEditable(True) # 允许用户输入不在列表中的分类
        category_layout.addWidget(category_label)
        category_layout.addWidget(self.category_combo)
        add_layout.addLayout(category_layout)

        self.add_button = QPushButton("添加模块")
        self.add_button.clicked.connect(self.add_new_module)
        self.add_button.setEnabled(False)
        add_layout.addWidget(self.add_button)

        self.name_input.textChanged.connect(self.update_add_button_state)
        self.link_input.textChanged.connect(self.update_add_button_state)

    def update_add_button_state(self):
        name_filled = bool(self.name_input.text())
        link_filled = bool(self.link_input.text())
        self.add_button.setEnabled(name_filled and link_filled) # 只有名称和链接都填写时才允许添加

    def add_new_module(self):
        name = self.name_input.text()
        link = self.link_input.text()
        system = self.system_combo.currentText()
        category = self.category_combo.currentText()

        if not name or not link:
            QMessageBox.warning(self, "新增模块", "模块名称和链接是必填项。")
            return

        new_module = {'name': name, 'link': link, 'system': system, 'category': category}
        if new_module in self.module_data:
            QMessageBox.warning(self, "新增模块", "模块已存在。")
            return
        if new_module["link"] in [self.module["link"] for self.module in self.module_data]:
            QMessageBox.warning(self, "新增模块", "链接已存在。")
            return
        print(f"新增模块: {new_module}")
        add_res = self.process.add_module(new_module) # 新增模块
        if not add_res:
            QMessageBox.warning(self, "新增模块", "新增模块失败。")
            return
        self.module_data.append(new_module)
        self.update_category_filter() # 更新分类筛选
        self.populate_module_table() # 刷新模块列表

        self.name_input.clear()
        self.link_input.clear()
        self.system_combo.setCurrentIndex(0) # 默认选择第一个
        self.category_combo.setCurrentIndex(-1)

if __name__ == '__main__':
    app = QApplication(sys.argv) # 创建应用程序实例
    window = ModuleManagerApp()
    window.show()
    sys.exit(app.exec())
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import os
from datetime import datetime
import shutil  # 用于删除文件夹

class MainWindow:
    def __init__(self, config_manager, browser_manager):
        self.root = tk.Tk()
        self.root.title("Yahoo Auction Manager")
        self.config_manager = config_manager
        self.browser_manager = browser_manager
        
        self.setup_ui()
        self.load_profiles()  # 初始化时加载配置
        
    def setup_ui(self):
        # 设置窗口最小大小
        self.root.minsize(500, 400)
        
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 顶部搜索框
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill="x", pady=(0, 5))
        ttk.Label(search_frame, text="搜索:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_profiles)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        # 配置列表框架
        self.profile_frame = ttk.LabelFrame(main_frame, text="配置列表")
        self.profile_frame.pack(fill="both", expand=True, pady=5)
        
        # 使用Treeview替代Listbox
        columns = ("名称", "创建时间", "路径")
        self.profile_tree = ttk.Treeview(self.profile_frame, columns=columns, show="headings")
        
        # 设置列
        for col in columns:
            self.profile_tree.heading(col, text=col, command=lambda c=col: self.sort_profiles(c))
            self.profile_tree.column(col, width=100)
        
        # 添加滚动条
        y_scrollbar = ttk.Scrollbar(self.profile_frame, orient="vertical", command=self.profile_tree.yview)
        x_scrollbar = ttk.Scrollbar(self.profile_frame, orient="horizontal", command=self.profile_tree.xview)
        self.profile_tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        # 布局
        self.profile_tree.pack(side="left", fill="both", expand=True)
        y_scrollbar.pack(side="right", fill="y")
        x_scrollbar.pack(side="bottom", fill="x")
        
        # 添加右键菜单
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="启动浏览器", command=self.launch_browser)
        self.context_menu.add_command(label="执行脚本", command=self.run_script)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="编辑配置", command=self.edit_profile)
        self.context_menu.add_command(label="删除配置", command=self.delete_profile)
        
        self.profile_tree.bind("<Button-3>", self.show_context_menu)
        self.profile_tree.bind("<Double-1>", lambda e: self.launch_browser())
        
        # 按钮区域使用更好的布局
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=5)
        
        # 左侧按钮
        left_buttons = ttk.Frame(button_frame)
        left_buttons.pack(side="left")
        
        ttk.Button(left_buttons, text="新建配置", command=self.create_new_profile).pack(side="left", padx=2)
        ttk.Button(left_buttons, text="删除配置", command=self.delete_profile).pack(side="left", padx=2)
        ttk.Button(left_buttons, text="启动浏览器", command=self.launch_browser).pack(side="left", padx=2)
        
        # 右侧按钮
        right_buttons = ttk.Frame(button_frame)
        right_buttons.pack(side="right")
        
        ttk.Button(right_buttons, text="执行脚本", command=self.run_script).pack(side="left", padx=2)
        ttk.Button(right_buttons, text="执行所有", command=self.run_all_scripts).pack(side="left", padx=2)
        
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief="sunken", anchor="w")
        status_bar.pack(fill="x", pady=(5, 0))
    
    def load_profiles(self):
        """加载配置列表"""
        for item in self.profile_tree.get_children():
            self.profile_tree.delete(item)
        
        profiles = self.config_manager.config.get("profiles", {})
        if not profiles:
            self.profile_tree.insert("", "end", values=("-- 没有配置 --", "", ""))
            return
        
        for name, info in profiles.items():
            created_at = info.get("created_at", "未知")
            path = info.get("profile_path", "")
            self.profile_tree.insert("", "end", values=(name, created_at, path))
    
    def filter_profiles(self, *args):
        """根据搜索框筛选配置"""
        search_text = self.search_var.get().lower()
        self.load_profiles()  # 重新加载所有配置
        
        if search_text:
            for item in self.profile_tree.get_children():
                values = self.profile_tree.item(item)["values"]
                if not any(search_text in str(v).lower() for v in values):
                    self.profile_tree.delete(item)
    
    def sort_profiles(self, column):
        """排序配置列表"""
        items = [(self.profile_tree.set(item, column), item) for item in self.profile_tree.get_children("")]
        items.sort()
        
        for index, (_, item) in enumerate(items):
            self.profile_tree.move(item, "", index)
    
    def show_context_menu(self, event):
        """显示右键菜单"""
        item = self.profile_tree.identify_row(event.y)
        if item:
            self.profile_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def edit_profile(self):
        """编辑配置"""
        old_profile_name = self.get_selected_profile()
        if not old_profile_name or old_profile_name == "-- 没有配置 --":
            return
        
        # 获取当前配置信息
        profile_info = self.config_manager.config["profiles"].get(old_profile_name, {})
        if not profile_info:
            messagebox.showerror("错误", f"无法获取配置 {old_profile_name} 的信息")
            return
        
        # 创建编辑对话框
        dialog = tk.Toplevel(self.root)
        dialog.title(f"编辑配置 - {old_profile_name}")
        
        # 设置对话框大小和位置
        dialog_width = 400
        dialog_height = 200
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog_width) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dialog_height) // 2
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        dialog.grab_set()
        
        # 配置名称输入
        name_frame = ttk.Frame(dialog)
        name_frame.pack(padx=5, pady=5, fill="x")
        ttk.Label(name_frame, text="配置名称:").pack(side="left")
        name_var = tk.StringVar(value=old_profile_name)
        name_entry = ttk.Entry(name_frame, textvariable=name_var)
        name_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        # 路径输入
        path_frame = ttk.Frame(dialog)
        path_frame.pack(padx=5, pady=5, fill="x")
        ttk.Label(path_frame, text="Chrome配置路径:").pack(side="left")
        path_var = tk.StringVar(value=profile_info.get("profile_path", ""))
        path_entry = ttk.Entry(path_frame, textvariable=path_var)
        path_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        def browse_path():
            """浏览文件夹"""
            from tkinter import filedialog
            path = filedialog.askdirectory(title="选择Chrome配置文件夹")
            if path:
                path_var.set(path)
        
        ttk.Button(path_frame, text="浏览", command=browse_path).pack(side="left", padx=5)
        
        def validate_and_save():
            """验证输入并保存配置"""
            new_name = name_var.get().strip()
            new_path = path_var.get().strip()
            
            # 验证输入
            if not new_name:
                messagebox.showerror("错误", "请输入配置名称")
                return
            if not new_path:
                messagebox.showerror("错误", "请选择Chrome配置路径")
                return
            
            # 如果名称改变，检查是否与其他配置冲突
            if new_name != old_profile_name and new_name in self.config_manager.get_all_profiles():
                messagebox.showerror("错误", "配置名称已存在")
                return
            
            # 检查路径是否存在
            if not os.path.exists(new_path):
                if messagebox.askyesno("确认", f"路径 {new_path} 不存在，是否创建?"):
                    try:
                        os.makedirs(new_path)
                    except Exception as e:
                        messagebox.showerror("错误", f"创建文件夹失败: {str(e)}")
                        return
                else:
                    return
            
            try:
                # 如果名称改变
                if new_name != old_profile_name:
                    # 询问是否要重命名文件夹
                    old_path = profile_info.get("profile_path", "")
                    if os.path.exists(old_path) and messagebox.askyesno(
                        "确认", 
                        f"是否将配置文件夹重命名？\n从: {old_path}\n到: {new_path}"
                    ):
                        try:
                            os.rename(old_path, new_path)
                        except Exception as e:
                            messagebox.showwarning(
                                "警告", 
                                f"文件夹重命名失败: {str(e)}\n将使用新指定的路径继续。"
                            )
                    
                    # 删除旧配置，添加新配置
                    del self.config_manager.config["profiles"][old_profile_name]
                    self.config_manager.config["profiles"][new_name] = {
                        "profile_path": new_path,
                        "created_at": profile_info.get("created_at", str(datetime.now()))
                    }
                else:
                    # 仅更新路径
                    self.config_manager.config["profiles"][old_profile_name]["profile_path"] = new_path
                
                # 保存配置
                self.config_manager.save_config()
                
                # 更新列表
                self.load_profiles()
                
                # 关闭对话框
                dialog.destroy()
                
                messagebox.showinfo("成功", f"配置已更新为:\n名称: {new_name}\n路径: {new_path}")
                
            except Exception as e:
                messagebox.showerror("错误", f"保存配置失败: {str(e)}")
        
        # 按钮区域
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(
            button_frame,
            text="保存",
            command=validate_and_save
        ).pack(side="left", padx=5)
        
        ttk.Button(
            button_frame,
            text="取消",
            command=dialog.destroy
        ).pack(side="left", padx=5)
    
    def get_selected_profile(self):
        """获取选中的配置名称"""
        selection = self.profile_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个配置")
            return None
        return self.profile_tree.item(selection[0])["values"][0]
    
    def update_status(self, message):
        """更新状态栏消息"""
        self.status_var.set(message)
    
    def create_new_profile(self):
        """创建新配置对话框"""
        # 创建对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("新建配置")
        
        # 设置对话框大小
        dialog_width = 400
        dialog_height = 200
        
        # 获取主窗口位置
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()
        
        # 计算对话框位置（相对于主窗口居中）
        x = root_x + (root_width - dialog_width) // 2
        y = root_y + (root_height - dialog_height) // 2
        
        # 设置对话框位置和大小
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
        # 使对话框成为模态窗口(阻止与主窗口的交互)
        dialog.grab_set()
        
        # 配置名称输入
        name_frame = ttk.Frame(dialog)
        name_frame.pack(padx=5, pady=5, fill="x")
        ttk.Label(name_frame, text="配置名称:").pack(side="left")
        name_var = tk.StringVar()
        name_entry = ttk.Entry(name_frame, textvariable=name_var)
        name_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        # 路径输入
        path_frame = ttk.Frame(dialog)
        path_frame.pack(padx=5, pady=5, fill="x")
        ttk.Label(path_frame, text="Chrome配置路径:").pack(side="left")
        path_var = tk.StringVar()
        path_entry = ttk.Entry(path_frame, textvariable=path_var)
        path_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        def browse_path():
            """浏览文件夹"""
            from tkinter import filedialog
            path = filedialog.askdirectory(title="选择Chrome配置文件夹")
            if path:
                path_var.set(path)
        
        ttk.Button(path_frame, text="浏览", command=browse_path).pack(side="left", padx=5)
        
        def validate_and_save():
            """验证输入并保存配置"""
            name = name_var.get().strip()
            base_path = path_var.get().strip()
            
            # 验证输入
            if not name:
                messagebox.showerror("错误", "请输入配置名称")
                return
            if not base_path:
                messagebox.showerror("错误", "请选择Chrome配置路径")
                return
            
            # 检查配置名是否已存在
            if name in self.config_manager.get_all_profiles():
                messagebox.showerror("错误", "配置名称已存在")
                return
            
            # 构建实际的配置文件夹路径
            profile_path = os.path.join(base_path, name)
            
            # 检查路径是否存在
            if not os.path.exists(profile_path):
                if messagebox.askyesno("确认", f"将在 {base_path} 下创建 {name} 文件夹，是否继续?"):
                    try:
                        os.makedirs(profile_path)
                    except Exception as e:
                        messagebox.showerror("错误", f"创建文件夹失败: {str(e)}")
                        return
                else:
                    return
            
            try:
                # 保存配置
                self.config_manager.config["profiles"][name] = {
                    "profile_path": profile_path,
                    "created_at": str(datetime.now())
                }
                self.config_manager.save_config()
                
                # 更新列表
                self.update_profile_list()
                
                # 关闭对话框
                dialog.destroy()
                
                messagebox.showinfo("成功", f"配置 {name} 创建成功\n配置路径: {profile_path}")
                
            except Exception as e:
                messagebox.showerror("错误", f"保存配置失败: {str(e)}")
        
        # 按钮区域
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(
            button_frame,
            text="确定",
            command=validate_and_save
        ).pack(side="left", padx=5)
        
        ttk.Button(
            button_frame,
            text="取消",
            command=dialog.destroy
        ).pack(side="left", padx=5)
        
        # 设置默认焦点
        name_entry.focus()
    
    def launch_browser(self):
        profile_name = self.get_selected_profile()
        if profile_name:
            print(f"Selected profile: {profile_name}")  # 调试信息
            profile_path = self.config_manager.get_profile_path(profile_name)
            print(f"Profile path: {profile_path}")  # 调试信息
            if profile_path:
                self.browser_manager.launch_browser(profile_name, profile_path)
            else:
                messagebox.showerror("错误", f"无法获取配置 {profile_name} 的路径")
        
    def run_script(self):
        profile_name = self.get_selected_profile()
        if profile_name:
            # TODO: 实现执行脚本逻辑
            pass
        
    def run_all_scripts(self):
        # TODO: 实现执行所有脚本逻辑
        pass
        
    def run(self):
        # 设置窗口大小和位置
        window_width = 400
        window_height = 300
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        self.root.mainloop() 

    def delete_profile(self):
        """删除选中的配置"""
        profile_name = self.get_selected_profile()
        if not profile_name:
            return
        
        if profile_name == "-- 没有配置 --":
            return
        
        # 确认删除
        if not messagebox.askyesno("确认删除", f"确定要删除配置 {profile_name} 吗？"):
            return
        
        try:
            # 从配置中删除
            if profile_name in self.config_manager.config["profiles"]:
                # 获取配置路径
                profile_path = self.config_manager.get_profile_path(profile_name)
                
                # 删除配置
                del self.config_manager.config["profiles"][profile_name]
                self.config_manager.save_config()
                
                # 提示是否删除配置文件夹
                if os.path.exists(profile_path):
                    if messagebox.askyesno("确认", 
                        f"是否同时删除配置文件夹？\n{profile_path}"):
                        try:
                            import shutil
                            shutil.rmtree(profile_path)
                        except Exception as e:
                            messagebox.showwarning("警告", 
                                f"配置已删除，但删除文件夹失败：{str(e)}")
                
                # 更新列表
                self.update_profile_list()
                messagebox.showinfo("成功", f"配置 {profile_name} 已删除")
            else:
                messagebox.showerror("错误", f"配置 {profile_name} 不存在")
                
        except Exception as e:
            messagebox.showerror("错误", f"删除配置失败: {str(e)}") 
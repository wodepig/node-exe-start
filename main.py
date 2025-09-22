import os
import sys
import platform
import getpass
import webbrowser
import subprocess
import time
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import utils  # 导入工具函数

class NodeServiceManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Node服务管理器")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # 状态变量
        self.node_process = None
        self.current_dir = Path(sys.argv[0]).parent.resolve()
        
        # 从配置文件加载配置
        self.config = self.load_config_from_file()
        
        # 设置配置变量（使用配置文件中的值，如果没有则使用默认值）
        self.DEFAULT_DIST_URL = self.config.get("dist_url", "https://rzerwczhiyzazzmpglim.supabase.co/storage/v1/object/public/exe/dist.zip")
        self.NODE_EXECUTABLE = self.config.get("node_executable", "node.exe")
        self.SERVER_PORT = self.config.get("server_port", 3000)
        self.INDEX_JS_PATH = self.config.get("index_js_path", "dist/server/index.mjs")
        self.TEMP_FILES = self.config.get("temp_files", ["dist.zip", "node.zip", "node_temp"])
        
        # 根据系统信息自动选择node下载地址
        self.DEFAULT_NODE_URL = self._get_node_url_by_system()
        
        # 保存系统信息到配置文件
        self._save_system_info_to_config()
        
        # 创建UI
        self.create_widgets()
        
        # 初始化显示系统信息
        self.update_system_info()
        
        # 加载保存的配置到UI
        self.load_config_to_ui()

    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建左右分栏的容器
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 左侧：系统信息区域
        info_frame = ttk.LabelFrame(top_frame, text="系统信息", padding="10")
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.os_version_var = tk.StringVar()
        self.architecture_var = tk.StringVar()
        self.username_var = tk.StringVar()
        
        ttk.Label(info_frame, text="操作系统:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Label(info_frame, textvariable=self.os_version_var).grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(info_frame, text="架构:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Label(info_frame, textvariable=self.architecture_var).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(info_frame, text="用户名:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Label(info_frame, textvariable=self.username_var).grid(row=2, column=1, sticky=tk.W, pady=2)
        
        # 右侧：程序配置区域
        app_config_frame = ttk.LabelFrame(top_frame, text="程序配置", padding="10")
        app_config_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # 程序版本号（固定，不可修改）
        ttk.Label(app_config_frame, text="程序版本:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.version_var = tk.StringVar(value="v1.0.0")
        version_entry = ttk.Entry(app_config_frame, textvariable=self.version_var, width=15, state="readonly")
        version_entry.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        # 服务端口号（可修改）
        ttk.Label(app_config_frame, text="服务端口:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.server_port_var = tk.StringVar(value=str(self.SERVER_PORT))
        self.server_port_entry = ttk.Entry(app_config_frame, textvariable=self.server_port_var, width=15)
        self.server_port_entry.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # 端口号修改事件绑定（焦点离开后校验）
        self.server_port_entry.bind("<FocusOut>", self._on_port_focus_out)
        
        # 配置区域
        config_frame = ttk.LabelFrame(main_frame, text="更新配置", padding="10")
        config_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(config_frame, text="dist下载地址:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.dist_url_var = tk.StringVar()
        self.dist_url_entry = ttk.Entry(config_frame, textvariable=self.dist_url_var, width=50)
        self.dist_url_entry.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # node下载地址现在根据系统信息自动选择，不再显示在UI中
        self.node_url_var = tk.StringVar()
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.check_update_btn = ttk.Button(button_frame, text="检查更新", command=self.check_update)
        self.check_update_btn.pack(side=tk.LEFT, padx=5)
        
        self.start_btn = ttk.Button(button_frame, text="启动服务", command=self.start_service)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(button_frame, text="停止服务", command=self.stop_service, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.clean_btn = ttk.Button(button_frame, text="清理临时文件", command=self.clean_temp_files)
        self.clean_btn.pack(side=tk.LEFT, padx=5)
        
        self.open_browser_btn = ttk.Button(button_frame, text="打开浏览器", command=self.open_browser, state=tk.DISABLED)
        self.open_browser_btn.pack(side=tk.LEFT, padx=5)
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="操作日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # 日志文本框
        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

    def _on_port_focus_out(self, event):
        """端口号焦点离开事件处理"""
        try:
            port = int(self.server_port_var.get())
            if 1024 <= port <= 65535:
                self.SERVER_PORT = port
                self.log(f"端口号已修改为: {port}")
                # 更新配置文件
                self._save_port_to_config()
            else:
                messagebox.showerror("错误", "端口号必须在1024-65535之间")
                self.server_port_var.set(str(self.SERVER_PORT))
        except ValueError:
            messagebox.showerror("错误", "请输入有效的端口号")
            self.server_port_var.set(str(self.SERVER_PORT))
    
    def _get_node_url_by_system(self):
        """根据系统信息选择对应的node下载地址"""
        
        # 构建系统标识符
        system_key = self.get_windows_version()
        
        # 从配置文件中获取node版本映射
        node_versions = self.config.get("node_version", {})
        
        # 选择对应的下载地址，如果没有匹配的则使用默认值
        default_url = "https://cdn.npmmirror.com/binaries/node/v20.19.5/node-v20.19.5-win-x64.zip"
        node_url = node_versions.get(system_key, default_url)
        
        # 在UI创建前不能使用log方法，直接打印到控制台
        print(f"系统标识: {system_key}, 选择Node下载地址: {node_url}")
        return node_url
    def get_windows_version(self):
        system_key = "win10-64bit"
        arch = platform.architecture()[0]
        # 检查是否为Windows系统
        if platform.system().lower() != 'windows':
            # 非Windows系统暂不支持
            print(f"警告: 检测到 {os_name} 系统，当前版本仅支持Windows系统")
            messagebox.showwarning("系统支持", f"检测到 {os_name} 系统，当前版本仅支持Windows系统")
            return system_key
        
        # 获取系统版本信息
        version = sys.getwindowsversion()
        major = version.major
        minor = version.minor
        build = version.build
        
        # 根据版本号判断具体系统
        if major == 6:
            if minor == 1:
                system_key = f"win7-{arch}"
            elif minor == 2:
                system_key = f"win8-{arch}"
            elif minor == 3:
                system_key = f"win8.1-{arch}"
        elif major == 10:
            if build < 22000:
                system_key = f"win10-{arch}"
            else:
                system_key = f"win11-{arch}"
        else:
            print(f"警告: {os_name} 系统不被支持")
            messagebox.showwarning("系统支持", f"检测到 {os_name} 系统不被支持")
            return system_key
        return system_key
    def _save_system_info_to_config(self):
        """保存系统信息到配置文件"""
        try:
            config_path = os.path.join(self.current_dir, "config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                config = {}
            
            # 更新系统信息
            if "system_info" not in config:
                config["system_info"] = {}
            
            config["system_info"]["os"] = platform.system() + " " + platform.release()
            config["system_info"]["arch"] = platform.architecture()[0]
            config["system_info"]["username"] = getpass.getuser()
            config["system_info"]["detected_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
                
        except Exception as e:
            self.log(f"保存系统信息失败: {str(e)}")
    
    def _save_port_to_config(self):
        """保存端口号到配置文件"""
        try:
            config_path = os.path.join(self.current_dir, "config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                config = {}
            
            config["server_port"] = self.SERVER_PORT
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
                
        except Exception as e:
            self.log(f"保存端口配置失败: {str(e)}")

    def update_system_info(self):
        """更新系统信息显示"""
        # 操作系统信息
        os_info = platform.system() + " " + platform.release()
        self.os_version_var.set(os_info)
        
        # 架构信息
        architecture = platform.architecture()[0]
        self.architecture_var.set(architecture)
        
        # 用户名
        username = getpass.getuser()
        self.username_var.set(username)
    
    def load_config(self):
        """加载保存的配置"""
        self.dist_url_var.set(self.DEFAULT_DIST_URL)
        self.node_url_var.set(self.DEFAULT_NODE_URL)
        
    def log(self, message):
        """在日志区域显示消息"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)  # 滚动到最后
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()  # 刷新UI
    
    def check_update(self):
        """检查并下载更新"""
        # 禁用按钮防止重复操作
        self.check_update_btn.config(state=tk.DISABLED)
        self.log("开始检查更新...")
        
        # 定义文件路径
        dist_zip_path = os.path.join(self.current_dir, "dist.zip")
        node_zip_path = os.path.join(self.current_dir, "node.zip")
        node_dir = os.path.join(self.current_dir, "node")
        node_temp_dir = os.path.join(self.current_dir, "node_temp")
        dist_dir = os.path.join(self.current_dir, "dist")
        
        try:
            # 下载dist.zip
            self.log("开始下载dist.zip...")
            if not utils.download_file_with_progress(self.dist_url_var.get(), dist_zip_path):
                self.log("dist.zip下载失败")
                self.check_update_btn.config(state=tk.NORMAL)
                return
            
            # 下载node.zip
            self.log("开始下载node.zip...")
            if not utils.download_file_with_progress(self.node_url_var.get(), node_zip_path):
                self.log("node.zip下载失败")
                self.check_update_btn.config(state=tk.NORMAL)
                return
            
            # 解压dist.zip到dist目录
            self.log("开始解压dist.zip...")
            if not utils.unzip_file(dist_zip_path, dist_dir):
                self.log("dist.zip解压失败")
                self.check_update_btn.config(state=tk.NORMAL)
                return
            
            # 解压并处理node.zip
            if not os.path.exists(node_dir):
                # 先解压到临时目录
                self.log("开始解压node.zip...")
                if not utils.unzip_file(node_zip_path, node_temp_dir):
                    self.log("node.zip解压失败")
                    self.check_update_btn.config(state=tk.NORMAL)
                    return
                
                # 自动检测node版本目录
                node_version_dir = utils.detect_node_version_dir(node_temp_dir)
                if not node_version_dir:
                    self.log("无法识别node版本目录")
                    self.check_update_btn.config(state=tk.NORMAL)
                    return
                
                # 将版本目录中的内容移动到最终的node目录
                self.log("正在整理Node文件...")
                if not utils.move_node_contents(node_temp_dir, node_dir, node_version_dir):
                    self.log("无法处理node文件")
                    self.check_update_btn.config(state=tk.NORMAL)
                    return
            else:
                self.log("Node目录已存在，跳过处理")
            
            self.log("更新检查完成")
            messagebox.showinfo("成功", "更新检查完成，可以启动服务了")
            
        except Exception as e:
            self.log(f"更新过程出错: {str(e)}")
            messagebox.showerror("错误", f"更新过程出错: {str(e)}")
        finally:
            self.check_update_btn.config(state=tk.NORMAL)
    
    def start_service(self):
        """启动Node服务"""
        if self.node_process is not None and self.node_process.poll() is None:
            messagebox.showinfo("提示", "服务已经在运行中")
            return
            
        # 固定检查/node/node.exe是否存在
        node_exe_path = os.path.join(self.current_dir, "node", "node.exe")
        if not os.path.exists(node_exe_path):
            self.log("程序不存在，需要先检查更新")
            if messagebox.askyesno("提示", "程序不存在，是否立即检查更新？"):
                # 调用检查更新功能
                self.check_update()
                # 检查更新完成后，如果node.exe存在了，则继续启动服务
                if os.path.exists(node_exe_path):
                    self.log("更新完成，继续启动服务")
                    # 延迟一下，等待UI更新
                    self.root.after(1000, self._start_service_after_check)
                else:
                    self.log("更新后程序仍然不存在，请手动检查更新")
                    self.reset_buttons()
            else:
                self.reset_buttons()
            return
        else:
            # 如果node.exe存在，直接启动服务
            self._start_service()
    
    def _start_service_after_check(self):
        """检查更新后启动服务"""
        node_exe_path = os.path.join(self.current_dir, "node", "node.exe")
        if os.path.exists(node_exe_path):
            self._start_service()
        else:
            self.log("更新后node.exe仍然不存在，无法启动服务")
            self.reset_buttons()
    
    def _start_service(self):
        """实际启动服务的逻辑"""
        # 禁用启动按钮，启用停止按钮
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.check_update_btn.config(state=tk.DISABLED)
        
        try:
            # 检查端口是否被占用，如果被占用则杀掉对应进程
            if utils.is_port_in_use(self.SERVER_PORT):
                self.log(f"端口{self.SERVER_PORT}被占用，正在清理...")
                killed_processes = utils.kill_process_by_port(self.SERVER_PORT)
                if killed_processes:
                    for process_info in killed_processes:
                        self.log(f"已终止进程: {process_info}")
                    self.log(f"端口{self.SERVER_PORT}清理完成")
                else:
                    self.log(f"无法清理端口{self.SERVER_PORT}的占用进程")
                    messagebox.showerror("错误", f"端口{self.SERVER_PORT}被占用且无法清理")
                    self.reset_buttons()
                    return
            
            # 使用固定的node.exe路径
            node_path = os.path.join(self.current_dir, "node", "node.exe")
            
            if not os.path.exists(node_path):
                self.log(f"找不到{node_path}")
                messagebox.showerror("错误", f"找不到Node可执行文件，请先检查更新")
                self.reset_buttons()
                return
            
            self.log(f"找到Node可执行文件: {node_path}")
            
            # 检查index.js是否存在
            index_js_full_path = os.path.join(self.current_dir, self.INDEX_JS_PATH)
            if not os.path.exists(index_js_full_path):
                self.log(f"找不到{self.INDEX_JS_PATH}")
                messagebox.showerror("错误", f"找不到{self.INDEX_JS_PATH}，请先检查更新")
                self.reset_buttons()
                return
            
            # 启动Node服务
            self.log("正在启动Node服务...")
            # 设置端口环境变量，让Node应用能够读取
            env = os.environ.copy()
            env["PORT"] = str(self.SERVER_PORT)
            
            self.node_process = subprocess.Popen(
                [node_path, self.INDEX_JS_PATH],
                cwd=self.current_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # 将stderr重定向到stdout
                text=True,
                bufsize=1,  # 行缓冲
                universal_newlines=True,
                env=env  # 传递环境变量
            )
            
            # 启动线程来读取输出（避免阻塞Tkinter主循环）
            import threading
            self.output_thread = threading.Thread(target=self.read_process_output_thread, daemon=True)
            self.output_thread.start()
            
            # 等待服务启动
            self.log(f"等待服务在端口{self.SERVER_PORT}启动...")
            if utils.wait_for_server(self.SERVER_PORT):
                self.log(f"服务已在端口{self.SERVER_PORT}启动")
                self.open_browser_btn.config(state=tk.NORMAL)
                # 使用after方法延迟显示消息框，避免阻塞主线程
                self.root.after(100, lambda: messagebox.showinfo("成功", f"服务已在端口{self.SERVER_PORT}启动"))
                # 服务启动成功后，继续在后台运行，不要阻塞主线程
                self.log("服务正在后台运行中...")
            else:
                self.log(f"超时: 服务在30秒内未启动")
                messagebox.showerror("错误", f"超时: 服务在30秒内未启动")
                self.stop_service()
                
        except Exception as e:
            self.log(f"启动服务时出错: {str(e)}")
            messagebox.showerror("错误", f"启动服务时出错: {str(e)}")
            self.reset_buttons()

    def read_process_output_thread(self):
        """在单独线程中读取进程输出"""
        while self.node_process is not None and self.node_process.poll() is None:
            try:
                output = self.node_process.stdout.readline()
                if output:
                    # 使用线程安全的方式更新UI
                    self.root.after(0, lambda: self.log(output.strip()))
            except Exception as e:
                if "I/O operation on closed file" not in str(e):
                    self.root.after(0, lambda: self.log(f"读取输出时出错: {str(e)}"))
                break
    
    def stop_service(self):
        """停止Node服务"""
        if self.node_process is None or self.node_process.poll() is not None:
            messagebox.showinfo("提示", "服务没有在运行")
            self.reset_buttons()
            return
            
        try:
            self.log("正在停止服务...")
            self.node_process.terminate()
            
            # 等待进程结束
            timeout = 10
            start_time = time.time()
            while self.node_process.poll() is None and time.time() - start_time < timeout:
                time.sleep(0.5)
                
            if self.node_process.poll() is None:
                # 强制终止
                self.node_process.kill()
                
            self.log("服务已停止")
            messagebox.showinfo("成功", "服务已停止")
            
        except Exception as e:
            self.log(f"停止服务时出错: {str(e)}")
            messagebox.showerror("错误", f"停止服务时出错: {str(e)}")
        finally:
            self.node_process = None
            self.reset_buttons()
    
    def open_browser(self):
        """打开浏览器访问服务"""
        if not utils.is_port_in_use(self.SERVER_PORT):
            messagebox.showwarning("警告", "服务未运行，无法打开浏览器")
            return
            
        url = f"http://localhost:{self.SERVER_PORT}"
        self.log(f"打开浏览器访问: {url}")
        webbrowser.open(url)
    
    def clean_temp_files(self):
        """清理临时文件"""
        if self.node_process is not None and self.node_process.poll() is None:
            messagebox.showwarning("警告", "请先停止服务再清理临时文件")
            return
            
        if messagebox.askyesno("确认", "确定要清理临时文件吗？这将删除下载的压缩包和临时文件"):
            self.log("开始清理临时文件...")
            utils.clean_temp_files(self.TEMP_FILES, self.current_dir)
            self.log("临时文件清理完成")
            messagebox.showinfo("成功", "临时文件清理完成")
    
    def load_config_from_file(self):
        """从配置文件加载配置"""
        config_path = os.path.join(self.current_dir, "config.json")
        default_config = {
            "project_name": "Node服务管理器",
            "dist_url": "https://rzerwczhiyzazzmpglim.supabase.co/storage/v1/object/public/exe/dist.zip",
            "node_url": "https://cdn.npmmirror.com/binaries/node/v20.19.5/node-v20.19.5-win-x64.zip",
            "server_port": 3000,
            "node_executable": "node.exe",
            "index_js_path": "dist/server/index.mjs",
            "temp_files": ["dist.zip", "node.zip", "node_temp"]
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 更新窗口标题
                    if "project_name" in config:
                        self.root.title(config["project_name"])
                    return config
            else:
                # 如果配置文件不存在，创建默认配置
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, ensure_ascii=False, indent=2)
                return default_config
        except Exception as e:
            self.log(f"读取配置文件时出错: {str(e)}")
            return default_config
    
    def load_config_to_ui(self):
        """加载配置到UI"""
        self.dist_url_var.set(self.config.get("dist_url", self.DEFAULT_DIST_URL))
        self.node_url_var.set(self.config.get("node_url", self.DEFAULT_NODE_URL))
    
    def reset_buttons(self):
        """重置按钮状态"""
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.check_update_btn.config(state=tk.NORMAL)
        self.open_browser_btn.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = NodeServiceManager(root)
    root.mainloop()
    
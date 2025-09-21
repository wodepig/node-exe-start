import os
import sys
import platform
import getpass
import webbrowser
import subprocess
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
        
        # 配置信息
        self.DEFAULT_DIST_URL = "https://rzerwczhiyzazzmpglim.supabase.co/storage/v1/object/public/exe/dist.zip"
        self.DEFAULT_NODE_URL = "https://cdn.npmmirror.com/binaries/node/v20.19.5/node-v20.19.5-win-x64.zip"
        self.NODE_EXECUTABLE = "node.exe"
        self.SERVER_PORT = 3000
        self.INDEX_JS_PATH = "dist/server/index.mjs"
        self.TEMP_FILES = ["dist.zip", "node.zip", "node_temp"]
        
        # 状态变量
        self.node_process = None
        self.current_dir = Path(sys.argv[0]).parent.resolve()
        
        # 创建UI
        self.create_widgets()
        
        # 初始化显示系统信息
        self.update_system_info()
        
        # 加载保存的配置
        self.load_config()

    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 系统信息区域
        info_frame = ttk.LabelFrame(main_frame, text="系统信息", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.os_version_var = tk.StringVar()
        self.architecture_var = tk.StringVar()
        self.username_var = tk.StringVar()
        
        ttk.Label(info_frame, text="操作系统:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Label(info_frame, textvariable=self.os_version_var).grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(info_frame, text="架构:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Label(info_frame, textvariable=self.architecture_var).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(info_frame, text="用户名:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Label(info_frame, textvariable=self.username_var).grid(row=2, column=1, sticky=tk.W, pady=2)
        
        # 配置区域
        config_frame = ttk.LabelFrame(main_frame, text="更新配置", padding="10")
        config_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(config_frame, text="dist下载地址:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.dist_url_var = tk.StringVar()
        self.dist_url_entry = ttk.Entry(config_frame, textvariable=self.dist_url_var, width=50)
        self.dist_url_entry.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(config_frame, text="node下载地址:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.node_url_var = tk.StringVar()
        self.node_url_entry = ttk.Entry(config_frame, textvariable=self.node_url_var, width=50)
        self.node_url_entry.grid(row=1, column=1, sticky=tk.W, pady=5)
        
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
            
            # 查找node可执行文件
            node_dir = os.path.join(self.current_dir, "node")
            node_path = utils.find_node_executable(node_dir)
            
            if not node_path or not os.path.exists(node_path):
                self.log(f"找不到{self.NODE_EXECUTABLE}")
                messagebox.showerror("错误", f"找不到{self.NODE_EXECUTABLE}，请先检查更新")
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
            self.node_process = subprocess.Popen(
                [node_path, self.INDEX_JS_PATH],
                cwd=self.current_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # 将stderr重定向到stdout
                text=True,
                bufsize=1,  # 行缓冲
                universal_newlines=True
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
    
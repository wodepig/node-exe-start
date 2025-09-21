import os
import sys
import zipfile
import requests
import subprocess
import time
import shutil
import socket
import psutil
from pathlib import Path
from tqdm import tqdm

def is_port_in_use(port):
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def kill_process_by_port(port):
    """杀掉占用指定端口的进程"""
    try:
        killed_processes = []
        
        # 获取所有网络连接
        for conn in psutil.net_connections():
            if conn.laddr and conn.laddr.port == port:
                try:
                    process = psutil.Process(conn.pid)
                    process_name = process.name()
                    process.terminate()
                    
                    # 等待进程结束
                    try:
                        process.wait(timeout=3)
                    except psutil.TimeoutExpired:
                        process.kill()
                        
                    killed_processes.append(f"{process_name} (PID: {conn.pid})")
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        
        return killed_processes
        
    except Exception as e:
        return []

def wait_for_server(port, timeout=30):
    """等待服务启动，超时返回False"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if is_port_in_use(port):
            return True
        time.sleep(1)
    
    return False

def download_file_with_progress(url, save_path):
    """带进度条的文件下载"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024  # 1KB
        
        with open(save_path, 'wb') as file, tqdm(
            desc=os.path.basename(save_path),
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as progress_bar:
            for chunk in response.iter_content(chunk_size=block_size):
                size = file.write(chunk)
                progress_bar.update(size)
        
        return True
    except Exception as e:
        print(f"下载失败: {str(e)}")
        return False

def unzip_file(zip_path, extract_dir):
    """解压zip文件到指定目录"""
    try:
        # 创建解压目录（如果不存在）
        os.makedirs(extract_dir, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # 获取压缩包中的文件列表
            file_list = zip_ref.namelist()
            # 创建进度条
            with tqdm(total=len(file_list), desc=f"解压 {os.path.basename(zip_path)}") as pbar:
                for file in file_list:
                    zip_ref.extract(file, extract_dir)
                    pbar.update(1)
        
        return True
    except Exception as e:
        print(f"解压失败: {str(e)}")
        return False

def detect_node_version_dir(temp_dir):
    """自动检测node压缩包解压后的版本目录"""
    try:
        # 获取临时目录中的所有项目
        items = os.listdir(temp_dir)
        
        # 寻找看起来像node版本的目录
        for item in items:
            item_path = os.path.join(temp_dir, item)
            if os.path.isdir(item_path) and item.startswith("node-v"):
                return item
        
        # 如果没找到明显的版本目录，检查是否有直接包含node.exe的目录
        for item in items:
            item_path = os.path.join(temp_dir, item)
            if os.path.isdir(item_path):
                for root, _, files in os.walk(item_path):
                    if "node.exe" in files:
                        return item
                
        return None
        
    except Exception as e:
        print(f"检测node目录时出错: {str(e)}")
        return None

def move_node_contents(temp_dir, target_dir, version_dir):
    """将node版本文件夹中的内容移动到目标node文件夹"""
    try:
        # 构建完整的版本目录路径
        version_path = os.path.join(temp_dir, version_dir)
        
        if not os.path.exists(version_path):
            return False
            
        # 创建目标目录
        os.makedirs(target_dir, exist_ok=True)
        
        # 获取所有项目并创建进度条
        items = os.listdir(version_path)
        with tqdm(total=len(items), desc="整理Node文件") as pbar:
            # 移动版本目录中的所有内容到目标目录
            for item in items:
                source = os.path.join(version_path, item)
                destination = os.path.join(target_dir, item)
                
                # 如果目标已存在则先删除
                if os.path.exists(destination):
                    if os.path.isdir(destination):
                        shutil.rmtree(destination)
                    else:
                        os.remove(destination)
                
                # 移动文件或目录
                shutil.move(source, destination)
                pbar.update(1)
        
        # 删除临时解压目录
        shutil.rmtree(temp_dir)
        return True
        
    except Exception as e:
        print(f"移动node文件失败: {str(e)}")
        return False

def find_node_executable(search_dir):
    """在指定目录中查找node可执行文件"""
    for root, _, files in os.walk(search_dir):
        if "node.exe" in files:
            return os.path.join(root, "node.exe")
    return None

def clean_temp_files(temp_files, base_dir):
    """清理临时文件"""
    for file in temp_files:
        file_path = os.path.join(base_dir, file)
        try:
            if os.path.exists(file_path):
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
                print(f"已清理: {file_path}")
        except Exception as e:
            print(f"清理{file_path}失败: {str(e)}")
    return True
    
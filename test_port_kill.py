#!/usr/bin/env python3
"""测试端口检测和清理功能"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import utils

def test_port_detection_and_kill():
    """测试端口检测和清理功能"""
    print("=== 测试端口检测和清理功能 ===")
    
    # 测试端口3000是否被占用
    port = 3000
    is_used = utils.is_port_in_use(port)
    print(f"端口{port}是否被占用: {is_used}")
    
    if is_used:
        print(f"端口{port}被占用，正在清理...")
        killed_processes = utils.kill_process_by_port(port)
        
        if killed_processes:
            print(f"清理完成，已终止的进程:")
            for process_info in killed_processes:
                print(f"  - {process_info}")
        else:
            print(f"无法清理端口{port}的占用进程")
    else:
        print(f"端口{port}未被占用，无需清理")
    
    # 再次检查端口状态
    is_used_after = utils.is_port_in_use(port)
    print(f"清理后端口{port}是否被占用: {is_used_after}")
    
    if not is_used_after:
        print("✅ 端口清理成功")
    else:
        print("❌ 端口清理失败")

if __name__ == "__main__":
    test_port_detection_and_kill()
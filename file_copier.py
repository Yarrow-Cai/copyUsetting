#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON文件复制工具 - 根据JSON配置文件自动复制文件到目标文件夹
支持替换复制（覆盖已存在的文件）
"""

import json
import shutil
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime


def log(message, level="INFO"):
    """打印带时间戳的日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    level_colors = {
        "INFO": "",
        "SUCCESS": "[成功] ",
        "WARNING": "[警告] ",
        "ERROR": "[错误] "
    }
    print(f"[{timestamp}] {level_colors.get(level, '')}{message}")


def copy_file(src, dst, dry_run=False):
    """
    复制单个文件
    :param src: 源文件路径
    :param dst: 目标文件路径
    :param dry_run: 是否为试运行模式（只显示操作，不实际执行）
    :return: (success: bool, message: str)
    """
    src_path = Path(src)
    dst_path = Path(dst)
    
    # 检查源文件是否存在
    if not src_path.exists():
        return False, f"源文件不存在: {src}"
    
    # 检查是否是文件
    if not src_path.is_file():
        return False, f"源路径不是文件: {src}"
    
    # 确保目标目录存在
    dst_dir = dst_path.parent
    if not dry_run:
        try:
            dst_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return False, f"创建目标目录失败: {dst_dir}, 错误: {e}"
    
    # 检查目标文件是否已存在
    exists = dst_path.exists()
    action = "替换" if exists else "复制"
    
    if dry_run:
        return True, f"[试运行] 将{action}: {src} -> {dst}"
    
    try:
        # 执行复制（覆盖模式）
        shutil.copy2(src, dst)
        return True, f"{action}成功: {src} -> {dst}"
    except Exception as e:
        return False, f"复制失败: {src} -> {dst}, 错误: {e}"


def load_json_config(json_path):
    """
    加载JSON配置文件
    支持多种格式：
    1. 对象列表: [{"src": "...", "dst": "..."}, ...]
    2. 对象: {"file1": "dst1", "file2": "dst2", ...}
    3. 简单列表: ["file1", "file2", ...] (需要配合 --output-dir 使用)
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON格式错误: {e}")
    except FileNotFoundError:
        raise ValueError(f"配置文件不存在: {json_path}")
    except Exception as e:
        raise ValueError(f"读取配置文件失败: {e}")


def parse_file_list(data, default_output_dir=None):
    """
    解析JSON数据为文件列表
    返回: [(src, dst), ...]
    """
    files = []
    
    if isinstance(data, list):
        # 如果是对象列表格式
        if len(data) > 0 and isinstance(data[0], dict):
            for item in data:
                src = item.get('src') or item.get('source') or item.get('from')
                dst = item.get('dst') or item.get('dest') or item.get('to') or item.get('target')
                if src and dst:
                    files.append((src, dst))
        # 如果是简单字符串列表
        elif len(data) > 0 and isinstance(data[0], str):
            if not default_output_dir:
                raise ValueError("简单列表格式需要提供 --output-dir 参数指定目标目录")
            for src in data:
                src_path = Path(src)
                dst = os.path.join(default_output_dir, src_path.name)
                files.append((src, dst))
    
    elif isinstance(data, dict):
        # 如果是对象格式 (src: dst)
        for src, dst in data.items():
            if isinstance(dst, str):
                files.append((src, dst))
            elif isinstance(dst, dict):
                # 嵌套对象格式
                target = dst.get('dst') or dst.get('dest') or dst.get('to') or dst.get('target')
                if target:
                    files.append((src, target))
    
    return files


def main():
    parser = argparse.ArgumentParser(
        description='根据JSON配置文件自动复制文件到目标文件夹',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
JSON配置格式示例:

1. 对象列表格式:
[
    {"src": "C:/path/to/file1.txt", "dst": "D:/backup/file1.txt"},
    {"src": "C:/path/to/file2.txt", "dst": "D:/backup/file2.txt"}
]

2. 键值对格式:
{
    "C:/path/to/file1.txt": "D:/backup/file1.txt",
    "C:/path/to/file2.txt": "D:/backup/file2.txt"
}

3. 简单列表格式 (需配合 --output-dir):
[
    "C:/path/to/file1.txt",
    "C:/path/to/file2.txt"
]
        """
    )
    
    parser.add_argument('json_file', help='JSON配置文件路径')
    parser.add_argument('-o', '--output-dir', help='默认目标目录（用于简单列表格式）')
    parser.add_argument('-d', '--dry-run', action='store_true', 
                        help='试运行模式，只显示要执行的操作，不实际复制')
    parser.add_argument('-v', '--verbose', action='store_true', 
                        help='显示详细信息')
    
    args = parser.parse_args()
    
    # 加载配置
    try:
        data = load_json_config(args.json_file)
    except ValueError as e:
        log(str(e), "ERROR")
        sys.exit(1)
    
    # 解析文件列表
    try:
        files = parse_file_list(data, args.output_dir)
    except ValueError as e:
        log(str(e), "ERROR")
        sys.exit(1)
    
    if not files:
        log("配置文件中没有找到有效的文件映射", "WARNING")
        sys.exit(0)
    
    log(f"共找到 {len(files)} 个文件待复制")
    
    # 统计
    success_count = 0
    fail_count = 0
    skip_count = 0
    
    # 执行复制
    for src, dst in files:
        success, message = copy_file(src, dst, args.dry_run)
        
        if success:
            if "将" in message:  # 试运行模式
                log(message, "INFO")
            else:
                log(message, "SUCCESS")
                success_count += 1
        else:
            log(message, "ERROR")
            fail_count += 1
    
    # 总结
    log("-" * 50)
    mode = "[试运行] " if args.dry_run else ""
    log(f"{mode}操作完成: 成功 {success_count}, 失败 {fail_count}")
    
    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()

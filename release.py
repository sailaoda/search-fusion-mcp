#!/usr/bin/env python3
"""
Search Fusion MCP Release Script
Automates the build and release process for version 2.0.0
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, description):
    """运行命令并处理错误"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - 成功")
        if result.stdout:
            print(f"   输出: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - 失败")
        print(f"   错误: {e.stderr.strip()}")
        return False

def check_prerequisites():
    """检查发布前提条件"""
    print("🔍 检查发布前提条件...")
    
    # 检查是否在正确的目录
    if not Path("pyproject.toml").exists():
        print("❌ 未找到 pyproject.toml 文件，请在项目根目录运行此脚本")
        return False
    
    # 检查是否有未提交的更改
    result = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
    if result.stdout.strip():
        print("⚠️ 检测到未提交的更改:")
        print(result.stdout)
        response = input("是否继续发布? (y/N): ")
        if response.lower() != 'y':
            return False
    
    # 检查必要的工具
    tools = ['python', 'pip', 'git']
    for tool in tools:
        if not shutil.which(tool):
            print(f"❌ 未找到必要工具: {tool}")
            return False
    
    print("✅ 前提条件检查通过")
    return True

def clean_build():
    """清理构建目录"""
    print("🧹 清理构建目录...")
    dirs_to_clean = ['build', 'dist', '*.egg-info']
    for pattern in dirs_to_clean:
        for path in Path('.').glob(pattern):
            if path.is_dir():
                shutil.rmtree(path)
                print(f"   删除目录: {path}")
            elif path.is_file():
                path.unlink()
                print(f"   删除文件: {path}")

def run_tests():
    """运行测试"""
    print("🧪 运行测试...")
    
    # 检查基本导入
    test_commands = [
        "python -c 'import src.config.config_manager; print(\"✅ ConfigManager导入成功\")'",
        "python -c 'import src.server; print(\"✅ Server导入成功\")'",
        "python -c 'import src.search_manager; print(\"✅ SearchManager导入成功\")'",
    ]
    
    for cmd in test_commands:
        if not run_command(cmd, "测试模块导入"):
            return False
    
    # 测试代理检测功能
    proxy_test = """
import sys, os
sys.path.insert(0, os.getcwd())
from src.config.config_manager import ConfigManager
config = ConfigManager()
print(f"✅ 代理检测功能正常: {config.config.http_proxy or '未检测到代理'}")
"""
    
    if not run_command(f'python -c "{proxy_test}"', "测试代理检测功能"):
        return False
    
    return True

def build_package():
    """构建包"""
    print("📦 构建包...")
    
    # 升级构建工具
    if not run_command("pip install --upgrade build twine", "升级构建工具"):
        return False
    
    # 构建包
    if not run_command("python -m build", "构建包"):
        return False
    
    # 检查构建结果
    dist_files = list(Path('dist').glob('*'))
    if not dist_files:
        print("❌ 构建失败，未找到构建文件")
        return False
    
    print("✅ 构建成功，生成文件:")
    for file in dist_files:
        print(f"   📄 {file}")
    
    return True

def validate_package():
    """验证包"""
    print("🔍 验证包...")
    
    # 使用twine检查包
    if not run_command("twine check dist/*", "验证包格式"):
        return False
    
    return True

def create_git_tag():
    """创建Git标签"""
    print("🏷️ 创建Git标签...")
    
    version = "v2.0.0"
    
    # 检查标签是否已存在
    result = subprocess.run(f"git tag -l {version}", shell=True, capture_output=True, text=True)
    if result.stdout.strip():
        print(f"⚠️ 标签 {version} 已存在")
        response = input("是否删除现有标签并重新创建? (y/N): ")
        if response.lower() == 'y':
            run_command(f"git tag -d {version}", f"删除现有标签 {version}")
        else:
            return True
    
    # 创建标签
    tag_message = "Release v2.0.0: Enhanced Proxy Auto-Detection"
    if not run_command(f'git tag -a {version} -m "{tag_message}"', f"创建标签 {version}"):
        return False
    
    print(f"✅ 成功创建标签 {version}")
    return True

def show_release_info():
    """显示发布信息"""
    print("\n" + "="*60)
    print("🎉 Search Fusion MCP v2.0.0 发布准备完成!")
    print("="*60)
    
    print("\n📦 构建文件:")
    for file in Path('dist').glob('*'):
        size = file.stat().st_size / 1024  # KB
        print(f"   📄 {file.name} ({size:.1f} KB)")
    
    print(f"\n🏷️ Git标签: v2.0.0")
    
    print(f"\n🌟 新功能亮点:")
    print(f"   🌐 增强代理自动检测 (参考concurrent-browser-mcp)")
    print(f"   🔍 三层检测策略: 环境变量 → 端口扫描 → 系统代理")
    print(f"   🚀 零配置使用，自动检测常见代理端口")
    print(f"   ⚡ Socket连接测试，3秒超时")
    print(f"   🍎 macOS系统代理支持")
    
    print(f"\n📚 文档更新:")
    print(f"   📖 README.md - 新增代理自动检测说明")
    print(f"   📖 README_zh.md - 中文文档更新")
    print(f"   📋 CHANGELOG.md - 版本更新记录")
    
    print(f"\n🚀 发布命令:")
    print(f"   测试发布: twine upload --repository testpypi dist/*")
    print(f"   正式发布: twine upload dist/*")
    print(f"   推送标签: git push origin v2.0.0")

def main():
    """主函数"""
    print("🚀 Search Fusion MCP v2.0.0 发布脚本")
    print("="*50)
    
    # 检查前提条件
    if not check_prerequisites():
        sys.exit(1)
    
    # 清理构建目录
    clean_build()
    
    # 运行测试
    if not run_tests():
        print("❌ 测试失败，停止发布")
        sys.exit(1)
    
    # 构建包
    if not build_package():
        print("❌ 构建失败，停止发布")
        sys.exit(1)
    
    # 验证包
    if not validate_package():
        print("❌ 包验证失败，停止发布")
        sys.exit(1)
    
    # 创建Git标签
    if not create_git_tag():
        print("❌ 创建Git标签失败")
        sys.exit(1)
    
    # 显示发布信息
    show_release_info()
    
    print(f"\n✅ 发布准备完成! 现在可以执行发布命令。")

if __name__ == "__main__":
    main() 
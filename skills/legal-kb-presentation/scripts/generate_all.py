#!/usr/bin/env python3
"""
Legal-KB 演示材料主生成器
整合 PPT、HTML、配图、视频生成流程
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime


def run_script(script_name, args=None):
    """运行子脚本"""
    script_path = Path(__file__).parent / script_name
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)

    print(f"\n{'='*60}")
    print(f"运行: {script_name}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(f"Stderr: {result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 执行失败: {e}")
        if e.stdout:
            print(f"输出: {e.stdout}")
        if e.stderr:
            print(f"错误: {e.stderr}")
        return False


def check_dependencies():
    """检查依赖"""
    print("检查依赖...")

    deps = {
        'python-pptx': 'pptx',
        'Pillow': 'PIL',
        'requests': 'requests',
        'openai': 'openai'
    }

    missing = []
    for pkg, module in deps.items():
        try:
            __import__(module)
            print(f"  ✅ {pkg}")
        except ImportError:
            print(f"  ❌ {pkg} (缺失)")
            missing.append(pkg)

    if missing:
        print(f"\n安装缺失依赖: pip3 install {' '.join(missing)} --break-system-packages")
        return False
    return True


def check_api_availability():
    """检查 Agnes API 可用性"""
    api_key = os.environ.get("AGNES_API_KEY")
    if not api_key:
        print("\n⚠️  未设置 AGNES_API_KEY")
        print("   影响：配图和视频生成将使用占位图")
        return False

    try:
        import requests
        # 测试图像 API
        r = requests.post(
            "https://apihub.agnes-ai.com/v1/images/generations",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            json={"model": "agnes-image-2.1-flash", "prompt": "test", "size": "256x256", "n": 1},
            timeout=10
        )
        if r.status_code == 200:
            print("\n✅ Agnes API 可用")
            return True
        else:
            print(f"\n⚠️  Agnes API 测试失败: {r.status_code}")
            return False
    except Exception as e:
        print(f"\n⚠️  Agnes API 连接失败: {e}")
        print("   将使用占位图")
        return False


def main():
    parser = argparse.ArgumentParser(description='Legal-KB 演示材料生成器')
    parser.add_argument('--output', '-o', default='/Users/mac/git/Legal-KB-Presentation',
                        help='输出目录')
    parser.add_argument('--kb-path', default='/Users/mac/Legal-KB',
                        help='知识库路径')
    parser.add_argument('--skip-ppt', action='store_true', help='跳过 PPT 生成')
    parser.add_argument('--skip-html', action='store_true', help='跳过 HTML 生成')
    parser.add_argument('--skip-images', action='store_true', help='跳过配图生成')
    parser.add_argument('--skip-video', action='store_true', help='跳过视频生成')
    parser.add_argument('--api-key', default=None, help='Agnes API Key')
    parser.add_argument('--check-only', action='store_true', help='仅检查环境')
    args = parser.parse_args()

    # 设置 API Key
    if args.api_key:
        os.environ["AGNES_API_KEY"] = args.api_key

    # 创建输出目录
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "assets").mkdir(exist_ok=True)

    print(f"输出目录: {output_dir}")
    print(f"知识库路径: {args.kb_path}")
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 检查依赖
    if not check_dependencies():
        print("\n请安装依赖后重试")
        sys.exit(1)

    # 检查 API
    api_available = check_api_availability()

    if args.check_only:
        print("\n环境检查完成")
        return 0

    results = {}

    # 生成 PPT
    if not args.skip_ppt:
        results['ppt'] = run_script('gen_ppt.py', [
            '--output', str(output_dir),
            '--kb-path', args.kb_path
        ])

    # 生成 HTML
    if not args.skip_html:
        results['html'] = run_script('gen_html_demo.py', [
            '--output', str(output_dir),
            '--kb-path', args.kb_path
        ])

    # 生成配图
    if not args.skip_images and api_available:
        results['images'] = run_script('gen_images.py', [
            '--output', str(output_dir),
            '--count', '4'
        ])
    elif not args.skip_images:
        print("\n跳过配图生成（API 不可用）")
        results['images'] = run_script('gen_images.py', [
            '--output', str(output_dir),
            '--count', '4',
            '--placeholder'
        ])

    # 生成视频
    if not args.skip_video and api_available:
        results['video'] = run_script('gen_video.py', [
            '--output', str(output_dir),
            '--duration', '15'
        ])
    else:
        print("\n跳过视频生成（API 不可用或已跳过）")
        results['video'] = True  # 视为成功（跳过）

    # 汇总结果
    print(f"\n{'='*60}")
    print("生成完成!")
    print(f"{'='*60}")

    for name, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {name}")

    # 列出输出文件
    print(f"\n输出文件:")
    for f in sorted(output_dir.rglob('*')):
        if f.is_file():
            size = f.stat().st_size
            print(f"  📄 {f.relative_to(output_dir)} ({size/1024:.1f} KB)")

    return 0


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""
Legal-KB Demo 视频生成器
调用 Agnes AI 视频模型生成展示视频
"""

import argparse
import os
import sys
import time
import requests
from pathlib import Path


class AgnesVideoClient:
    """Agnes AI 视频生成客户端"""

    def __init__(self, api_key=None, base_url="https://apihub.agnes-ai.com/v1"):
        self.api_key = api_key or os.environ.get("AGNES_API_KEY")
        self.base_url = base_url
        self.poll_url = "https://apihub.agnes-ai.com/v1/videos"
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}" if self.api_key else ""
        })

    def generate(self, prompt, duration=15, resolution="720p", model="agnes-video-v2.0",
                 retries=3):
        """生成视频"""
        url = f"{self.base_url}/videos"
        payload = {
            "model": model,
            "prompt": prompt,
            "duration": duration,
            "resolution": resolution
        }

        for attempt in range(retries):
            try:
                print(f"    提交视频生成请求... (尝试 {attempt+1})")
                response = self.session.post(url, json=payload, timeout=60)
                if response.status_code == 200:
                    data = response.json()
                    video_id = data.get("data", {}).get("video_id")
                    if video_id:
                        print(f"    视频已提交，ID: {video_id}")
                        return video_id
                    else:
                        print(f"    响应: {data}")
                elif response.status_code in [429, 500, 502, 503, 504]:
                    wait = 5 * (2 ** attempt)
                    print(f"    ⚠️  API 错误 {response.status_code}, {wait}s 后重试...")
                    time.sleep(wait)
                else:
                    print(f"    ❌ API 错误 {response.status_code}: {response.text[:200]}")
                    break
            except requests.exceptions.Timeout:
                print(f"    ⚠️  请求超时, {5 * (2 ** attempt)}s 后重试...")
                time.sleep(5 * (2 ** attempt))
            except Exception as e:
                print(f"    ❌ 请求失败: {e}")
                break

        return None

    def poll_result(self, video_id, max_wait=300, poll_interval=10):
        """轮询视频生成结果"""
        print(f"    开始轮询视频结果...")
        start_time = time.time()

        while time.time() - start_time < max_wait:
            try:
                url = f"{self.poll_url}/{video_id}"
                response = self.session.get(url, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("data", {}).get("status", "")
                    if status == "completed":
                        video_url = data.get("data", {}).get("video_url")
                        print(f"    ✅ 视频生成完成: {video_url}")
                        return video_url
                    elif status == "failed":
                        print(f"    ❌ 视频生成失败: {data}")
                        return None
                    else:
                        print(f"    ⏳ 状态: {status}, {poll_interval}s 后重试...")
                time.sleep(poll_interval)
            except Exception as e:
                print(f"    ⚠️  轮询失败: {e}, {poll_interval}s 后重试...")
                time.sleep(poll_interval)

        print(f"    ⏱️  轮询超时")
        return None

    def download_video(self, url, output_path):
        """下载视频"""
        try:
            print(f"    下载视频...")
            response = self.session.get(url, timeout=120, stream=True)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"    ✅ 视频已保存: {output_path}")
                return True
        except Exception as e:
            print(f"    ❌ 下载失败: {e}")
        return False


def generate_video(output_dir, duration=15):
    """生成演示视频"""
    output_path = Path(output_dir) / "assets"
    output_path.mkdir(parents=True, exist_ok=True)

    api_key = os.environ.get("AGNES_API_KEY")
    if not api_key:
        print("⚠️  未设置 AGNES_API_KEY，跳过视频生成")
        return None

    print(f"开始生成 {duration} 秒演示视频...")

    client = AgnesVideoClient(api_key)

    # 视频提示词
    prompt = """A futuristic legal tech dashboard with glowing blue neon interfaces,
holographic data panels showing legal documents and case analytics,
smooth camera pan across the interface, cyberpunk aesthetic,
dark background with cyan and magenta highlights,
professional UI/UX presentation, cinematic lighting,
showcasing a lawyer knowledge base system with animated data flows."""

    print(f"提示词: {prompt[:60]}...")

    # 提交生成
    video_id = client.generate(prompt, duration=duration)
    if not video_id:
        print("❌ 视频生成请求失败")
        return None

    # 轮询结果
    video_url = client.poll_result(video_id, max_wait=300)
    if not video_url:
        print("❌ 视频生成超时")
        return None

    # 下载视频
    video_path = output_path / "Legal-KB-Demo.mp4"
    if client.download_video(video_url, video_path):
        return str(video_path)

    return None


def main():
    parser = argparse.ArgumentParser(description='Legal-KB Demo 视频生成器')
    parser.add_argument('--output', '-o', default='/Users/mac/git/Legal-KB-Presentation')
    parser.add_argument('--duration', '-d', type=int, default=15, help='视频时长（秒）')
    parser.add_argument('--api-key', default=None, help='Agnes API Key')
    args = parser.parse_args()

    # 设置 API Key
    if args.api_key:
        os.environ["AGNES_API_KEY"] = args.api_key

    # 测试 API 连接
    api_key = os.environ.get("AGNES_API_KEY")
    if not api_key:
        print("⚠️  请设置 AGNES_API_KEY 环境变量")
        print("   export AGNES_API_KEY='your-api-key'")
        sys.exit(1)

    # 生成视频
    generate_video(args.output, args.duration)


if __name__ == '__main__':
    main()

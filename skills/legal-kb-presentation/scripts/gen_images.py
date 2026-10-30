#!/usr/bin/env python3
"""
Legal-KB 科技感配图生成器
调用 Agnes AI 图像模型生成科技风格配图
"""

import argparse
import os
import sys
import time
import requests
from pathlib import Path


class AgnesImageClient:
    """Agnes AI 图像生成客户端（使用 OpenAI SDK）"""

    def __init__(self, api_key=None, base_url="https://apihub.agnes-ai.com/v1"):
        self.api_key = api_key or os.environ.get("AGNES_API_KEY")
        self.base_url = base_url
        self.client = None
        if self.api_key:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )

    def generate(self, prompt, size="1024x576", model="agnes-image-2.1-flash",
                 n=1, retries=3):
        """生成图像"""
        if not self.client:
            return None
        
        for attempt in range(retries):
            try:
                response = self.client.images.generate(
                    model=model,
                    prompt=prompt,
                    size=size,
                    n=n,
                )
                if response.data:
                    return response.data
            except Exception as e:
                if attempt < retries - 1:
                    wait = 2 ** attempt
                    print(f"  ⚠️  请求失败: {e}, {wait}s 后重试...")
                    time.sleep(wait)
                else:
                    print(f"  ❌ 请求失败: {e}")
        return None

    def download_image(self, url, output_path):
        """下载图像"""
        try:
            import requests
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                return True
        except Exception as e:
            print(f"  ❌ 下载失败: {e}")
        return False


def create_placeholder_image(output_path, width=1024, height=576,
                              text="Legal-KB", bg_color=(10, 14, 39),
                              accent_color=(0, 212, 255)):
    """创建占位图片（当 API 不可用时使用）"""
    try:
        from PIL import Image, ImageDraw, ImageFont

        img = Image.new('RGB', (width, height), bg_color)
        draw = ImageDraw.Draw(img)

        # 尝试使用系统字体
        try:
            font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 48)
            small_font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 24)
        except:
            font = ImageFont.load_default()
            small_font = font

        # 绘制标题
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        y = (height - text_height) // 2 - 20
        draw.text((x, y), text, fill=accent_color, font=font)

        # 绘制副标题
        subtitle = "Lawyer Knowledge Base"
        bbox = draw.textbbox((0, 0), subtitle, font=small_font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        draw.text((x, y + text_height + 20), subtitle, fill=(180, 190, 224),
                  font=small_font)

        # 绘制装饰线
        line_y = y + text_height + 60
        draw.line([(width//2 - 100, line_y), (width//2 + 100, line_y)],
                  fill=accent_color, width=2)

        img.save(output_path)
        return True
    except Exception as e:
        print(f"  ❌ 生成占位图失败: {e}")
        return False


def generate_images(output_dir, count=4):
    """生成演示配图"""
    output_path = Path(output_dir) / "assets"
    output_path.mkdir(parents=True, exist_ok=True)

    prompts = [
        ("A futuristic legal tech dashboard with glowing blue neon interfaces, "
         "holographic data panels showing legal documents and case analytics, "
         "cyberpunk aesthetic, dark background with cyan and magenta highlights, "
         "UI/UX design, sleek tech presentation style"),
        ("3D knowledge graph visualization with interconnected nodes representing "
         "legal cases, laws, and precedents, glowing blue connections, "
         "dark space background, data visualization style, tech presentation"),
        ("Futuristic law library interface with floating holographic books and "
         "documents, blue and cyan neon lighting, cyberpunk aesthetic, "
         "high tech legal research concept"),
        ("Animated data flow visualization showing legal case workflow, "
         "glowing blue lines connecting process stages, dark background, "
         "tech dashboard style, UI/UX presentation"),
        ("Abstract legal tech concept art with digital scales of justice, "
         "neon blue and cyan accents, holographic elements, "
         "futuristic courtroom technology, dark background")
    ]

    api_key = os.environ.get("AGNES_API_KEY")
    if not api_key:
        print("  ⚠️  未设置 AGNES_API_KEY，全部使用占位图")
        results = []
        for i in range(min(count, len(prompts))):
            filename = f"slide_{i+1}.png"
            filepath = output_path / filename
            if create_placeholder_image(filepath, text=f"Slide {i+1}"):
                results.append(str(filepath))
                print(f"    ✅ 占位图: {filepath}")
        return results

    client = AgnesImageClient(api_key)
    results = []

    for i in range(min(count, len(prompts))):
        print(f"  生成配图 {i+1}/{count}...")
        filename = f"slide_{i+1}.png"
        filepath = output_path / filename

        images = client.generate(prompts[i], size="1024x576", n=1)
        if images and len(images) > 0:
            img_data = images[0]
            if "url" in img_data:
                if client.download_image(img_data["url"], filepath):
                    print(f"    ✅ 已保存: {filepath}")
                    results.append(str(filepath))
                else:
                    create_placeholder_image(filepath, text=f"Slide {i+1}")
                    results.append(str(filepath))
            elif "b64_json" in img_data:
                import base64
                with open(filepath, 'wb') as f:
                    f.write(base64.b64decode(img_data["b64_json"]))
                print(f"    ✅ 已保存: {filepath}")
                results.append(str(filepath))
            else:
                create_placeholder_image(filepath, text=f"Slide {i+1}")
                results.append(str(filepath))
        else:
            create_placeholder_image(filepath, text=f"Slide {i+1}")
            results.append(str(filepath))
            print(f"    ⚠️  使用占位图")

        # 避免请求过快
        time.sleep(1)

    return results


def main():
    parser = argparse.ArgumentParser(description='Legal-KB 配图生成器')
    parser.add_argument('--output', '-o', default='/Users/mac/git/Legal-KB-Presentation')
    parser.add_argument('--count', '-n', type=int, default=4, help='生成图片数量')
    parser.add_argument('--api-key', default=None, help='Agnes API Key')
    parser.add_argument('--placeholder', action='store_true', help='仅生成占位图')
    args = parser.parse_args()

    if args.placeholder:
        print("生成占位图片...")
        generate_images(args.output, args.count)
        return

    # 检查 API Key
    api_key = args.api_key or os.environ.get("AGNES_API_KEY")
    if not api_key:
        print("⚠️  未设置 AGNES_API_KEY，使用占位图模式")
        generate_images(args.output, args.count)
        return

    # 测试 API 连接
    print(f"测试 Agnes API 连接...")
    try:
        client = AgnesImageClient(api_key)
        test = client.generate("test", n=1)
        if test:
            print("✅ API 连接正常")
            generate_images(args.output, args.count)
        else:
            print("⚠️  API 测试失败，使用占位图模式")
            generate_images(args.output, args.count)
    except Exception as e:
        print(f"⚠️  API 连接失败: {e}，使用占位图模式")
        generate_images(args.output, args.count)


if __name__ == '__main__':
    main()

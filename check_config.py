#!/usr/bin/env python3
"""
配置验证脚本
检查 .env 文件中的所有配置是否正确
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from seo_gen.config import settings
import requests
import base64


def check_openai_api():
    """检查 OpenAI API 配置"""
    print("\n" + "="*60)
    print("1. OpenAI API 配置检查")
    print("="*60)

    print(f"✓ API Base: {settings.openai_api_base}")
    print(f"✓ API Key: {settings.openai_api_key[:20]}...{settings.openai_api_key[-10:]}")
    print(f"✓ Model: {settings.openai_model}")

    # 测试 API 连接
    try:
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json"
        }
        response = requests.get(
            f"{settings.openai_api_base.rstrip('/v1')}/models",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            print("✅ API 连接成功")
            return True
        else:
            print(f"⚠️  API 返回状态码: {response.status_code}")
            print(f"   响应: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ API 连接失败: {e}")
        return False


def check_google_search_api():
    """检查 Google Search API 配置"""
    print("\n" + "="*60)
    print("2. Google Search API 配置检查")
    print("="*60)

    if not settings.google_search_api_key:
        print("❌ 未配置 GOOGLE_SEARCH_API_KEY")
        return False

    if not settings.google_search_engine_id:
        print("❌ 未配置 GOOGLE_SEARCH_ENGINE_ID")
        return False

    print(f"✓ API Key: {settings.google_search_api_key[:20]}...{settings.google_search_api_key[-10:]}")
    print(f"✓ Engine ID: {settings.google_search_engine_id}")

    # 测试搜索
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": settings.google_search_api_key,
            "cx": settings.google_search_engine_id,
            "q": "test",
            "num": 1
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            print("✅ Google Search API 可用")
            return True
        else:
            print(f"⚠️  API 返回状态码: {response.status_code}")
            print(f"   响应: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ API 测试失败: {e}")
        return False


def check_wordpress_config():
    """检查 WordPress 配置"""
    print("\n" + "="*60)
    print("3. WordPress 配置检查")
    print("="*60)

    if not settings.wordpress_site_url:
        print("❌ 未配置 WORDPRESS_SITE_URL")
        return False

    if not settings.wordpress_username:
        print("❌ 未配置 WORDPRESS_USERNAME")
        return False

    if not settings.wordpress_app_password:
        print("❌ 未配置 WORDPRESS_APP_PASSWORD")
        return False

    print(f"✓ Site URL: {settings.wordpress_site_url}")
    print(f"✓ Username: {settings.wordpress_username}")
    print(f"✓ App Password: {settings.wordpress_app_password[:10]}...")

    # 测试 WordPress 连接
    try:
        # 移除密码中的空格
        password = settings.wordpress_app_password.replace(" ", "")
        auth_string = f"{settings.wordpress_username}:{password}"
        auth_bytes = auth_string.encode('utf-8')
        auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')

        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/json"
        }

        url = f"{settings.wordpress_site_url.rstrip('/')}/wp-json/wp/v2/users/me"
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ WordPress 连接成功 (用户: {user_data.get('name', 'Unknown')})")
            return True
        else:
            print(f"⚠️  WordPress 返回状态码: {response.status_code}")
            print(f"   响应: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ WordPress 连接失败: {e}")
        return False


def check_dataforseo_config():
    """检查 DataForSEO 配置"""
    print("\n" + "="*60)
    print("4. DataForSEO API 配置检查")
    print("="*60)

    if not settings.dataforseo_username:
        print("⚠️  未配置 DATAFORSEO_USERNAME (可选)")
        print("   将使用 LLM 估算关键词数据")
        return None

    if not settings.dataforseo_password:
        print("⚠️  未配置 DATAFORSEO_PASSWORD (可选)")
        return None

    print(f"✓ Username: {settings.dataforseo_username}")

    # 检查密码是否是 Base64 编码
    password = settings.dataforseo_password
    try:
        # 尝试解码
        decoded = base64.b64decode(password).decode('utf-8')
        if ':' in decoded:
            print("⚠️  密码似乎是 Base64 编码的")
            print(f"   解码后: {decoded[:30]}...")
            # 提取实际密码
            actual_password = decoded.split(':')[-1]
            print(f"   实际密码: {actual_password[:10]}...")
        else:
            print(f"✓ Password: {password[:10]}...")
    except:
        print(f"✓ Password: {password[:10]}...")

    print(f"✓ Location Code: {settings.dataforseo_location_code}")

    # 测试 API (需要实际凭证)
    print("ℹ️  DataForSEO API 测试需要有效凭证,跳过在线测试")
    return None


def check_quality_config():
    """检查质量控制配置"""
    print("\n" + "="*60)
    print("5. 质量控制配置检查")
    print("="*60)

    print(f"✓ 最低发布分数: {settings.min_publish_score}/100")
    print(f"✓ 允许强制发布: {settings.allow_force_publish}")
    print(f"✓ 质量阈值: {settings.quality_score_threshold}/100")

    if settings.min_publish_score < 60:
        print("⚠️  最低发布分数过低,建议设置为 75+")

    return True


def check_site_info():
    """检查站点信息配置"""
    print("\n" + "="*60)
    print("6. 站点信息配置检查")
    print("="*60)

    print(f"✓ 作者名称: {settings.author_name}")
    print(f"✓ 站点名称: {settings.site_name}")
    print(f"✓ 站点URL: {settings.site_url}")
    print(f"✓ Logo URL: {settings.site_logo_url}")

    return True


def check_paths():
    """检查路径配置"""
    print("\n" + "="*60)
    print("7. 路径配置检查")
    print("="*60)

    print(f"✓ 输出目录: {settings.output_dir}")
    print(f"✓ 跟踪数据库: {settings.tracker_db_path}")
    print(f"✓ 向量搜索: {settings.use_vector_search}")

    if settings.use_vector_search:
        print(f"✓ 向量数据库路径: {settings.vector_db_path}")
        if not Path(settings.vector_db_path).exists():
            print(f"⚠️  向量数据库路径不存在: {settings.vector_db_path}")

    # 检查输出目录
    output_path = Path(settings.output_dir)
    if not output_path.exists():
        print(f"ℹ️  输出目录不存在,将自动创建: {output_path}")
        output_path.mkdir(parents=True, exist_ok=True)
        print("✅ 输出目录已创建")

    return True


def check_rate_limits():
    """检查速率限制配置"""
    print("\n" + "="*60)
    print("8. 速率限制配置检查")
    print("="*60)

    print(f"✓ Google API QPS: {settings.google_api_max_qps}")
    print(f"✓ LLM RPM: {settings.llm_max_rpm}")
    print(f"✓ 图片并发数: {settings.image_max_concurrent}")
    print(f"✓ 竞品爬取延迟: {settings.competitor_scrape_delay_min}-{settings.competitor_scrape_delay_max}秒")

    if settings.llm_max_rpm > 60:
        print("⚠️  LLM RPM 过高,可能触发速率限制")

    return True


def main():
    """主函数"""
    print("\n" + "="*60)
    print("SEO 内容生成器 - 配置验证")
    print("="*60)

    results = {
        "OpenAI API": check_openai_api(),
        "Google Search API": check_google_search_api(),
        "WordPress": check_wordpress_config(),
        "DataForSEO": check_dataforseo_config(),
        "质量控制": check_quality_config(),
        "站点信息": check_site_info(),
        "路径配置": check_paths(),
        "速率限制": check_rate_limits(),
    }

    # 总结
    print("\n" + "="*60)
    print("配置验证总结")
    print("="*60)

    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)

    for name, result in results.items():
        if result is True:
            print(f"✅ {name}: 通过")
        elif result is False:
            print(f"❌ {name}: 失败")
        else:
            print(f"⚠️  {name}: 跳过")

    print(f"\n总计: {passed} 通过, {failed} 失败, {skipped} 跳过")

    if failed == 0:
        print("\n🎉 所有必需配置都已正确设置!")
        print("   你可以开始使用系统了")
        return 0
    else:
        print("\n⚠️  部分配置存在问题,请检查上述错误信息")
        return 1


if __name__ == "__main__":
    sys.exit(main())

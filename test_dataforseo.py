#!/usr/bin/env python3
"""
DataForSEO API 连接测试脚本
"""

import sys
import requests
import base64
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from seo_gen.config import settings


def test_dataforseo_connection():
    """测试 DataForSEO API 连接"""
    print("\n" + "="*60)
    print("DataForSEO API 连接测试")
    print("="*60)

    # 显示配置
    print(f"\n配置信息:")
    print(f"  Username: {settings.dataforseo_username}")
    print(f"  Password: {settings.dataforseo_password[:10]}...{settings.dataforseo_password[-5:]}")
    print(f"  Location Code: {settings.dataforseo_location_code}")

    # 准备认证
    username = settings.dataforseo_username
    password = settings.dataforseo_password

    # 创建 Basic Auth
    auth_string = f"{username}:{password}"
    auth_bytes = auth_string.encode('utf-8')
    auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')

    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/json"
    }

    print(f"\n正在测试 API 连接...")

    # 测试 1: 获取账户信息
    print("\n[测试 1/3] 获取账户信息...")
    try:
        url = "https://api.dataforseo.com/v3/appendix/user_data"
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get("status_code") == 20000:
                tasks = data.get("tasks", [])
                if tasks and len(tasks) > 0:
                    result = tasks[0].get("result", [])
                    if result and len(result) > 0:
                        user_data = result[0]
                        print(f"✅ 账户信息获取成功")

                        # 安全获取余额
                        money = user_data.get('money', {})
                        if isinstance(money, dict):
                            balance = money.get('value', 0)
                        else:
                            balance = float(money) if money else 0

                        print(f"   余额: ${balance:.2f}")

                        # 获取价格
                        rates = user_data.get('rates', {})
                        if rates:
                            # 获取第一个价格
                            first_rate = next(iter(rates.values()), {})
                            price = first_rate.get('price_per_1000', 0) if isinstance(first_rate, dict) else 0
                            print(f"   价格: ${price:.2f}/1000次")

                        # 检查余额
                        if balance < 1:
                            print(f"⚠️  账户余额不足: ${balance:.2f}")
                            print(f"   建议充值以使用 API")

                        return True
                    else:
                        print(f"❌ 响应格式错误: 无 result 数据")
                        return False
                else:
                    print(f"❌ 响应格式错误: 无 tasks 数据")
                    return False
            else:
                print(f"❌ API 返回错误状态: {data.get('status_code')}")
                print(f"   错误信息: {data.get('status_message', 'Unknown')}")
                return False
        else:
            print(f"❌ HTTP 状态码: {response.status_code}")
            print(f"   响应: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def test_keyword_data():
    """测试关键词数据获取"""
    print("\n[测试 2/3] 测试关键词数据获取...")

    username = settings.dataforseo_username
    password = settings.dataforseo_password

    auth_string = f"{username}:{password}"
    auth_bytes = auth_string.encode('utf-8')
    auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')

    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/json"
    }

    # 测试获取关键词数据
    try:
        url = "https://api.dataforseo.com/v3/keywords_data/google/search_volume/live"

        payload = [{
            "keywords": ["dropshipping", "seo"],
            "location_code": settings.dataforseo_location_code,
            "language_code": "en"
        }]

        response = requests.post(url, json=payload, headers=headers, timeout=15)

        if response.status_code == 200:
            data = response.json()
            if data.get("status_code") == 20000:
                tasks = data.get("tasks", [])
                if tasks and len(tasks) > 0:
                    result = tasks[0].get("result", [])
                    if result and len(result) > 0:
                        keywords = result[0].get("items", [])
                        if keywords:
                            print(f"✅ 关键词数据获取成功")
                            print(f"\n   测试关键词数据:")
                            for kw in keywords[:2]:
                                print(f"   - {kw.get('keyword')}")
                                print(f"     搜索量: {kw.get('search_volume', 0):,}")
                                print(f"     竞争度: {kw.get('competition', 0):.2f}")
                                print(f"     CPC: ${kw.get('cpc', 0):.2f}")
                            return True
                        else:
                            print(f"❌ 无关键词数据返回")
                            return False
                    else:
                        print(f"❌ 响应格式错误: 无 result 数据")
                        return False
                else:
                    print(f"❌ 响应格式错误: 无 tasks 数据")
                    return False
            else:
                print(f"❌ API 返回错误状态: {data.get('status_code')}")
                print(f"   错误信息: {data.get('status_message', 'Unknown')}")

                # 检查是否是余额不足
                if "insufficient" in str(data.get('status_message', '')).lower():
                    print(f"\n⚠️  可能是账户余额不足")
                    print(f"   请访问 https://app.dataforseo.com/ 充值")

                return False
        else:
            print(f"❌ HTTP 状态码: {response.status_code}")
            print(f"   响应: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def test_serp_features():
    """测试 SERP 特征检测"""
    print("\n[测试 3/3] 测试 SERP 特征检测...")

    username = settings.dataforseo_username
    password = settings.dataforseo_password

    auth_string = f"{username}:{password}"
    auth_bytes = auth_string.encode('utf-8')
    auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')

    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/json"
    }

    try:
        url = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"

        payload = [{
            "keyword": "dropshipping",
            "location_code": settings.dataforseo_location_code,
            "language_code": "en",
            "device": "desktop",
            "os": "windows"
        }]

        response = requests.post(url, json=payload, headers=headers, timeout=15)

        if response.status_code == 200:
            data = response.json()
            if data.get("status_code") == 20000:
                tasks = data.get("tasks", [])
                if tasks and len(tasks) > 0:
                    result = tasks[0].get("result", [])
                    if result and len(result) > 0:
                        items = result[0].get("items", [])
                        if items:
                            print(f"✅ SERP 特征检测成功")
                            print(f"\n   检测到的 SERP 特征:")

                            # 统计特征类型
                            feature_types = {}
                            for item in items[:10]:
                                item_type = item.get("type", "unknown")
                                feature_types[item_type] = feature_types.get(item_type, 0) + 1

                            for feature, count in feature_types.items():
                                print(f"   - {feature}: {count}个")

                            return True
                        else:
                            print(f"❌ 无 SERP 数据返回")
                            return False
                    else:
                        print(f"❌ 响应格式错误: 无 result 数据")
                        return False
                else:
                    print(f"❌ 响应格式错误: 无 tasks 数据")
                    return False
            else:
                print(f"❌ API 返回错误状态: {data.get('status_code')}")
                print(f"   错误信息: {data.get('status_message', 'Unknown')}")
                return False
        else:
            print(f"❌ HTTP 状态码: {response.status_code}")
            print(f"   响应: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def main():
    """主函数"""
    print("\n" + "="*60)
    print("DataForSEO API 完整测试")
    print("="*60)

    # 检查配置
    if not settings.dataforseo_username or not settings.dataforseo_password:
        print("\n❌ DataForSEO 配置不完整")
        print("   请在 .env 中配置:")
        print("   DATAFORSEO_USERNAME=your_email")
        print("   DATAFORSEO_PASSWORD=your_password")
        return 1

    # 运行测试
    results = {
        "账户连接": test_dataforseo_connection(),
        "关键词数据": test_keyword_data(),
        "SERP特征": test_serp_features(),
    }

    # 总结
    print("\n" + "="*60)
    print("测试结果总结")
    print("="*60)

    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)

    for name, result in results.items():
        if result is True:
            print(f"✅ {name}: 通过")
        elif result is False:
            print(f"❌ {name}: 失败")
        else:
            print(f"⚠️  {name}: 跳过")

    print(f"\n总计: {passed}/3 通过")

    if passed == 3:
        print("\n🎉 DataForSEO API 完全可用!")
        print("   系统将使用真实关键词数据")
        return 0
    elif passed > 0:
        print("\n⚠️  DataForSEO API 部分可用")
        print("   某些功能可能受限")
        return 1
    else:
        print("\n❌ DataForSEO API 不可用")
        print("   系统将降级使用 LLM 估算")
        print("\n可能的原因:")
        print("   1. 账户余额不足 - 访问 https://app.dataforseo.com/ 充值")
        print("   2. 用户名或密码错误")
        print("   3. 网络连接问题")
        return 1


if __name__ == "__main__":
    sys.exit(main())

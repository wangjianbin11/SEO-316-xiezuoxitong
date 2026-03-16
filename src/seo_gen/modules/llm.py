"""
LLM 客户端模块

支持 OpenAI 兼容的第三方中转 API
"""

import json
import re
import asyncio
from typing import Any, Optional, Union
from pathlib import Path
from datetime import datetime

import httpx
from loguru import logger

from seo_gen.config import settings


class JSONExtractionError(Exception):
    """JSON 提取失败异常"""
    pass


class LLMClient:
    """OpenAI 兼容 API 客户端"""

    def __init__(
        self,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_retries: int = 3,
    ):
        """
        初始化 LLM 客户端

        Args:
            api_base: API 端点，默认从 settings 读取
            api_key: API 密钥，默认从 settings 读取
            model: 默认模型，默认从 settings 读取
            max_retries: 最大重试次数
        """
        self.api_base = (api_base or settings.openai_api_base).rstrip("/")
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model
        self.max_retries = max_retries

        if not self.api_key:
            raise ValueError("API 密钥未配置，请设置 OPENAI_API_KEY 环境变量")

        self.client = httpx.AsyncClient(
            base_url=self.api_base,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=120.0,
        )

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

    async def chat(
        self,
        messages: list[dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[dict[str, str]] = None,
    ) -> str:
        """
        发送聊天请求

        Args:
            messages: 消息列表
            model: 模型名称，默认使用初始化时的模型
            temperature: 温度参数
            max_tokens: 最大 token 数
            response_format: 响应格式，如 {"type": "json_object"}

        Returns:
            模型响应文本
        """
        model = model or self.model
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        if response_format:
            payload["response_format"] = response_format

        logger.debug(f"发送 LLM 请求: model={model}, messages={len(messages)}")

        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = await self.client.post("/chat/completions", json=payload)
                response.raise_for_status()

                data = response.json()
                content = data["choices"][0]["message"]["content"]

                logger.debug(f"收到 LLM 响应: {len(content)} 字符")
                return content

            except (httpx.RemoteProtocolError, httpx.ConnectError, httpx.ReadTimeout) as e:
                last_error = e
                wait_time = (attempt + 1) * 2  # 2, 4, 6 秒递增等待
                logger.warning(f"LLM 请求失败 (尝试 {attempt + 1}/{self.max_retries}): {e}, {wait_time}秒后重试...")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(wait_time)
            except httpx.HTTPStatusError as e:
                logger.error(f"LLM 请求失败: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"LLM 请求异常: {e}")
                raise

        # 所有重试都失败
        logger.error(f"LLM 请求在 {self.max_retries} 次重试后仍然失败")
        raise last_error

    async def chat_json(
        self,
        messages: list[dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.7,
    ) -> dict[str, Any]:
        """
        发送聊天请求，期望返回 JSON 格式

        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数

        Returns:
            解析后的 JSON 对象
        """
        # 在系统消息中要求返回 JSON
        enhanced_messages = messages.copy()
        if enhanced_messages and enhanced_messages[0].get("role") == "system":
            enhanced_messages[0]["content"] += "\n\nIMPORTANT: You must respond with valid JSON only, no other text."
        else:
            enhanced_messages.insert(0, {
                "role": "system",
                "content": "You must respond with valid JSON only, no other text."
            })

        content = await self.chat(
            messages=enhanced_messages,
            model=model,
            temperature=temperature,
            response_format={"type": "json_object"},
        )

        # 使用新的 extract_json 函数
        try:
            return extract_json(content)
        except JSONExtractionError as e:
            logger.error(f"JSON 提取失败: {e}")
            raise ValueError(f"模型未返回有效的 JSON: {e}") from e

    def sync_chat(
        self,
        messages: list[dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        同步版本的聊天方法
        """
        import asyncio

        return asyncio.run(self.chat(messages, model, temperature, max_tokens))

    def sync_chat_json(
        self,
        messages: list[dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.7,
    ) -> dict[str, Any]:
        """
        同步版本的 JSON 聊天方法
        """
        import asyncio

        return asyncio.run(self.chat_json(messages, model, temperature))


# 全局单例
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """获取全局 LLM 客户端单例"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


def extract_json(text: str) -> Union[dict, list]:
    """
    从LLM响应中提取JSON,处理所有常见格式问题

    策略(按顺序尝试):
    1. 直接 json.loads(text)
    2. 去除 ```json ... ``` 围栏后解析
    3. 去除 ``` ... ``` 围栏后解析
    4. 正则提取第一个 { 到最后一个 }
    5. 正则提取第一个 [ 到最后一个 ]
    6. 所有策略失败: 抛出 JSONExtractionError

    Args:
        text: LLM 响应文本

    Returns:
        解析后的 JSON 对象(dict 或 list)

    Raises:
        JSONExtractionError: 无法提取有效 JSON
    """
    if not text or not text.strip():
        raise JSONExtractionError("Empty text provided")

    # 策略列表
    strategies = [
        # 策略1: 直接解析
        lambda t: json.loads(t),

        # 策略2: 去除 ```json ... ``` 围栏
        lambda t: json.loads(re.sub(r'^```json\s*|\s*```$', '', t.strip(), flags=re.MULTILINE)),

        # 策略3: 去除 ``` ... ``` 围栏
        lambda t: json.loads(re.sub(r'^```\s*|\s*```$', '', t.strip(), flags=re.MULTILINE)),

        # 策略4: 提取 { ... }
        lambda t: json.loads(re.search(r'\{.*\}', t, re.DOTALL).group()),

        # 策略5: 提取 [ ... ]
        lambda t: json.loads(re.search(r'\[.*\]', t, re.DOTALL).group()),
    ]

    # 尝试所有策略
    for i, strategy in enumerate(strategies, 1):
        try:
            result = strategy(text)
            if i > 1:
                logger.debug(f"JSON extraction succeeded with strategy {i}")
            return result
        except (json.JSONDecodeError, AttributeError, TypeError):
            continue

    # 所有策略失败,记录错误
    error_msg = f"Cannot extract JSON from text (length: {len(text)})"
    logger.error(error_msg)
    logger.debug(f"Failed text preview: {text[:500]}")

    # 写入失败日志
    _log_json_failure(text)

    raise JSONExtractionError(error_msg)


def _log_json_failure(text: str) -> None:
    """记录 JSON 提取失败的详细信息"""
    try:
        log_dir = Path("outputs/errors")
        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"json_failures_{timestamp}.log"

        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Text length: {len(text)}\n")
            f.write("=" * 80 + "\n")
            f.write(text)
            f.write("\n" + "=" * 80 + "\n")

        logger.info(f"JSON failure logged to: {log_file}")
    except Exception as e:
        logger.warning(f"Failed to log JSON failure: {e}")


async def extract_json_with_retry(
    llm_client: LLMClient,
    messages: list[dict[str, Any]],
    max_retries: int = 2,
    **kwargs
) -> Union[dict, list]:
    """
    带自动修复重试的 JSON 提取

    如果第一次提取失败,会发送修复提示让 LLM 重新生成

    Args:
        llm_client: LLM 客户端实例
        messages: 原始消息列表
        max_retries: 最大重试次数
        **kwargs: 传递给 chat() 的其他参数

    Returns:
        解析后的 JSON 对象

    Raises:
        JSONExtractionError: 重试后仍然失败
    """
    # 第一次尝试
    response = await llm_client.chat(messages, **kwargs)

    for attempt in range(max_retries + 1):
        try:
            return extract_json(response)
        except JSONExtractionError as e:
            if attempt >= max_retries:
                raise

            # 构建修复提示
            logger.warning(f"JSON extraction failed (attempt {attempt + 1}/{max_retries + 1}), requesting fix...")

            fix_messages = messages + [
                {"role": "assistant", "content": response[:500]},
                {
                    "role": "user",
                    "content": (
                        "Your previous response was not valid JSON. "
                        "Respond with ONLY the raw JSON object. "
                        "No markdown code blocks, no explanation, no additional text. "
                        "Just the JSON starting with { or [."
                    )
                }
            ]

            # 重新请求
            response = await llm_client.chat(fix_messages, **kwargs)

    raise JSONExtractionError(f"Failed after {max_retries} retries")

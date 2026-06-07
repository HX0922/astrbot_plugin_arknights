"""
Playwright 渲染器 — 严格对齐 AmiyaBot Chain.html() 渲染行为

AmiyaBot 的行为:
- viewport width: 1600px (chain.html(template, data, width=1600))
- 等待策略: wait_for_load_state('networkidle') (WaitALLRequestsDone)
- 数据注入: window.init(data) via page.evaluate
- file:// 协议加载本地 HTML
- screenshot mode: 由框架处理

此模块复制上述所有设定。
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Optional

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

_playwright_module = None
_browser = None


def _get_playwright():
    global _playwright_module
    if _playwright_module is None:
        from playwright.async_api import async_playwright as pw
        _playwright_module = pw
    return _playwright_module


async def _get_browser():
    """获取复用的 Playwright 浏览器实例（优先使用系统 Chrome/Edge）"""
    global _browser
    if _browser is None:
        pw = _get_playwright()
        p = await pw().__aenter__()
        # 尝试系统 Chrome → Edge → 默认 Chromium
        for channel in ["chrome", "msedge", None]:
            try:
                _browser = await p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox"],
                    channel=channel,
                )
                break
            except Exception:
                continue
    return _browser


async def render_to_image(
    html_path: str,
    data: dict,
    width: int = 1600,       # ← AmiyaBot: Chain.html(..., width=1600)
    wait_networkidle: bool = True,  # ← AmiyaBot: WaitALLRequestsDone
) -> Optional[str]:
    """用 Playwright 渲染 HTML 为图片

    严格对齐 AmiyaBot:
    - width=1600 (不是 800)
    - 默认等待 networkidle (不是固定 500ms)
    - 数据通过 window.init() 注入

    Args:
        html_path: HTML 模板绝对路径
        data: Vue.js 模板数据
        width: 视口宽度 (AmiyaBot 默认 1600)
        wait_networkidle: 是否等待 networkidle

    Returns:
        PNG 图片路径，失败返回 None
    """
    try:
        browser = await _get_browser()
        page = await browser.new_page(viewport={"width": width, "height": 1000})

        # file:// 协议加载（与 AmiyaBot 完全一致）
        await page.goto(
            f"file:///{html_path}",
            wait_until="networkidle" if wait_networkidle else "domcontentloaded",
        )

        # 注入数据（AmiyaBot 方式: window.init(data)）
        data_json = json.dumps(data, ensure_ascii=False)
        await page.evaluate(f"window.init({data_json})")

        # 等待 Vue 渲染（AmiyaBot: WaitALLRequestsDone → networkidle 已在上方完成）
        # 额外等待确保 Vue reactive 更新已提交
        await page.wait_for_timeout(300)

        # 截图
        output = str(Path(tempfile.gettempdir()) / f"arknights_{os.getpid()}.png")
        await page.screenshot(path=output, full_page=True)
        await page.close()
        return output

    except Exception as e:
        from astrbot.api import logger
        logger.error(f"[Arknights] Playwright 渲染失败: {e}")
        return None


async def render_operator_info(star_self, char, char_id: str) -> Optional[str]:
    """渲染干员信息 — 对齐 AmiyaBot operator_func() 中的 data assembly

    注意: 此函数接收的是 OperatorData.get_operator_detail() 已经组装好的完整数据，
    不再在渲染层重新组装（对齐 AmiyaBot 架构）。
    """
    html_path = str(TEMPLATE_DIR / "operatorInfo.html")
    return await render_to_image(html_path, char, width=1600)


async def render_template(
    template_name: str,
    data: dict,
    width: int = 1600,
) -> Optional[str]:
    """通用模板渲染"""
    html_path = str(TEMPLATE_DIR / template_name)
    if not os.path.exists(html_path):
        return None
    return await render_to_image(html_path, data, width=width)

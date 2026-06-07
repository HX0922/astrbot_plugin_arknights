"""
多步对话状态机

替代 AmiyaBot 的 data.wait() 机制。
每个用户维护一个等待状态，下次消息到达时先检查状态。

用法:
    from src.state import wait_for, check_wait

    # 设置等待
    wait_for(user_id, "step_name", {"context": "data"})

    # 检查（在 handler 开头）
    state = check_wait(user_id)
    if state:
        # 用户正在等待中，继续流程
"""

from collections import defaultdict
import time

# {(user_id, session_id): {"step": str, "context": dict, "created_at": float}}
_wait_states: dict[str, dict] = {}

# 超时时间（秒）
TIMEOUT = 120


def _cleanup_expired():
    """清理过期状态"""
    now = time.time()
    expired = [k for k, v in _wait_states.items() if now - v.get("created_at", 0) > TIMEOUT]
    for k in expired:
        del _wait_states[k]


def wait_for(uid: str, step: str, context: dict | None = None):
    """设置用户等待状态"""
    _cleanup_expired()
    _wait_states[uid] = {
        "step": step,
        "context": context or {},
        "created_at": time.time(),
    }


def check_wait(uid: str) -> dict | None:
    """检查并取出用户等待状态。返回 None 表示不在等待。"""
    _cleanup_expired()
    state = _wait_states.pop(uid, None)
    if state and time.time() - state["created_at"] > TIMEOUT:
        return None
    return state


def has_wait(uid: str) -> bool:
    """检查用户是否在等待中（不取出）"""
    _cleanup_expired()
    if uid not in _wait_states:
        return False
    if time.time() - _wait_states[uid]["created_at"] > TIMEOUT:
        del _wait_states[uid]
        return False
    return True

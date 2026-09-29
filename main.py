from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

import asyncio
import sys
from pathlib import Path

try:
    from . import TTDTCP
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    import TTDTCP


@register("OpenTTD服务器数据检测", "等待破产", "检测和播报openttd服务器数据", "0.0.1")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""


    @filter.command("TTDhelp",alias={"帮助","OpenTTDhelp"})
    async def TTDhelp(self, event: AstrMessageEvent):
        """帮助指令""" # 帮助指令
        yield event.plain_result(f"欢迎使用OpenTTD服务器数据检测\n 查询服务器：TTD ip\n[示例：TTD 127.0.0.0：3979 (注：兼容ipv6以及域名)]") # 发送一条纯文本消息
        # 后期打算添加功能：添加服务器： TTD+ serverip name\n 查看已添加服务器: TTD/ name\n

    @filter.command("TTD",alias={"查看TTD"})
    async def TTD(self, event: AstrMessageEvent,target: str = ""):
        """查询指令"""
        target = target.strip()

        if not target:
            yield event.plain_result(
                "请提供服务器地址，格式：TTD ip:port\n"
                "示例：TTD 127.0.0.1:3979"
            )
            return

        try:
            # TTDTCP.query 是阻塞函数
            result = await asyncio.to_thread(TTDTCP.query, target)
        except Exception as e:
            logger.error(f"查询 {target} 出错: {e}")
            yield event.plain_result(f"查询出错：{e}")
            return

        yield event.plain_result(result)


    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""

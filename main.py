# 从 astrbot 框架导入事件过滤器、消息事件对象、消息结果类型
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
# 从 astrbot 框架导入插件上下文和插件基类、注册装饰器
from astrbot.api.star import Context, Star, register
# 从 astrbot 框架导入日志记录器，用于输出错误日志
from astrbot.api import logger

# 导入异步 IO 库，用于把阻塞函数放到线程里执行，避免卡住事件循环
import asyncio
# 导入 sys 库，用于在相对导入失败时手动把当前目录加入模块搜索路径
import sys
# 导入 Path，用于跨平台地获取当前文件所在目录
from pathlib import Path

# 优先尝试相对导入（插件作为包被加载时可用）
try:
    from . import TTDTCP, YQM,GRFTTDTCP,GRFYQM
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    import TTDTCP
    import YQM
    import GRFTTDTCP
    import GRFYQM


# 注册插件：插件名、作者、描述、版本号
@register("OpenTTD服务器数据检测", "等待破产", "检测和播报openttd服务器数据", "0.0.4")
class MyPlugin(Star):
    # 构造函数，接收框架传入的上下文对象
    def __init__(self, context: Context):
        # 调用父类 Star 的构造函数完成初始化
        super().__init__(context)
    # 可选的异步初始化方法，实例化插件后框架会自动调用
    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
    # 注册帮助指令，指令名 TTDhelp，同时可用别名 帮助、OpenTTDhelp
    @filter.command("TTDhelp", alias={"帮助", "OpenTTDhelp"})
    async def TTDhelp(self, event: AstrMessageEvent):
        """帮助指令"""
        # 返回一段纯文本帮助说明，提示两种查询方式及示例
        yield event.plain_result(
            "欢迎使用OpenTTD服务器数据检测\n"
            "   按 IP / 域名查询：TTD ip:port\n"
            "   示例：TTD 127.0.0.1:3979\n"
            "   示例：TTD [::1]:3979\n"
            "  （兼容域名）\n"
            "   按邀请码查询（公开服务器）：\n"
            "   TTD 邀请码\n"
            "   示例：TTD +abcd1234\n"
            "注：如果想同时查看GRF列表请使用GRFTTD\n"
            "（GRFTTD与TTD用法相同）"
        )
    # 注册查询指令，指令名 TTD，别名 查看TTD
    @filter.command("TTD", alias={"查看TTD"})
    async def TTD(self, event: AstrMessageEvent, target: str = ""):
        """查询指令（自动识别 IP 与邀请码）"""
        target = target.strip()
        # 如果没有提供参数，就提示用户正确的输入格式
        if not target:
            yield event.plain_result(
                "请提供服务器地址或邀请码，格式：\n"
                "  TTD ip:port\n"
                "  示例：TTD 127.0.0.1:3979\n"
                "  示例：TTD [::1]:3979\n"
                "  TTD 邀请码\n"
                "  示例：TTD +abcd1234"
            )
            # 直接返回，结束本次处理
            return
        # 把查询工作包在 try 里，防止网络错误导致插件崩溃
        try:
            # 邀请码固定以 '+' 开头，据此选择不同的查询方式
            if target.startswith("+"):
                result = await asyncio.to_thread(YQM.query, target)
            else:
                result = await asyncio.to_thread(TTDTCP.query, target)
        except Exception as e:
            logger.error(f"查询 {target} 出错: {e}")
            yield event.plain_result(f"查询出错：{e}")
            return
        yield event.plain_result(result)

    @filter.command("GRFTTD", alias={"查看GRFTTD"})
    async def GRFTTD(self, event: AstrMessageEvent, target: str = ""):
        """查询指令（自动识别 IP 与邀请码）"""
        target = target.strip()
        # 如果没有提供参数，就提示用户正确的输入格式
        if not target:
            yield event.plain_result(
                "请提供服务器地址或邀请码，格式：\n"
                "  GRFTTD ip:port\n"
                "  示例：GRFTTD 127.0.0.1:3979\n"
                "  示例：GRFTTD [::1]:3979\n"
                "  GRFTTD 邀请码\n"
                "  示例：GRFTTD +abcd1234"
            )
            # 直接返回，结束本次处理
            return
        # 把查询工作包在 try 里，防止网络错误导致插件崩溃
        try:
            # 邀请码固定以 '+' 开头，据此选择不同的查询方式
            if target.startswith("+"):
                result = await asyncio.to_thread(GRFYQM.query, target)
            else:
                result = await asyncio.to_thread(GRFTTDTCP.query, target)
        except Exception as e:
            logger.error(f"查询 {target} 出错: {e}")
            yield event.plain_result(f"查询出错：{e}")
            return
        yield event.plain_result(result)
    # 可选的异步销毁方法，插件被卸载/停用时会调用
    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
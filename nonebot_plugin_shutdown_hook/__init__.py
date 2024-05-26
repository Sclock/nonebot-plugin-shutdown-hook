from asyncio import sleep
from typing import Any, Awaitable, Callable, TypeAlias, Union, cast

from nonebot.log import logger
from nonebot.plugin import PluginMetadata
from nonebot.utils import is_coroutine_callable, run_sync
from uvicorn import Server

__version__ = "0.1.0"

__plugin_meta__ = PluginMetadata(
    name="高优先级关闭信号钩子插件",
    description="提供一个在关闭信号后,Bot断开前执行的钩子函数",
    usage="在 nonebot.run() 之前调用此函数, 用 on_shutdown_before 装饰需要执行的函数即可",
    homepage="https://github.com/Sclock/nonebot-plugin-shutdown-hook",
    type="library",
    supported_adapters=None,
    extra={
        "author": "Sclock",
        "priority": 1,
        "version": __version__,
    },
)


SIGNALS_LIST = []
"""存储接收到的关闭信号"""
HOOK_ENABLED = True
"""标记钩子函数是否可以运行,限制只执行一次"""

SYNC_FUNC: TypeAlias = Callable[[], Any]
ASYNC_FUNC: TypeAlias = Callable[[], Awaitable[Any]]
FUNC: TypeAlias = Union[SYNC_FUNC, ASYNC_FUNC]

_shutdown_before_funcs: list[FUNC] = []
"""存储所有注册的 收到关闭信号后 函数"""


async def run_func(
    funcs: list[FUNC],
) -> None:
    for func in funcs:
        try:
            if is_coroutine_callable(func):
                await cast(ASYNC_FUNC, func)()
            else:
                await run_sync(cast(SYNC_FUNC, func))()
        except Exception as e:
            logger.opt(colors=True).error(
                f"<red>执行 收到关闭信号后函数 {func} 时发生错误 {e}</>")


def on_shutdown_before(func: FUNC) -> FUNC:
    """
    装饰一个函数使他在 收到关闭信号后 立刻执行
    """
    _shutdown_before_funcs.append(func)
    return func


async def shutdown_before() -> None:
    """
    执行所有注册的 收到关闭信号后 函数。
    """
    logger.debug("执行 收到关闭信号后函数")
    await run_func(_shutdown_before_funcs)
    logger.debug("执行 收到关闭信号后函数 完毕")


def override_uvicorn_shutdown_hooks():
    """
    关闭信号钩子
    在 nonebot.run() 之前调用此函数，以接管 uvicorn 的关闭信号处理逻辑。

    通过修改 Server.handle_exit，在 handle_exit 函数接收到中止信号后并不立刻中止，
    而是将信号存储在 SIGNALS_LIST，并立刻执行注册的钩子函数。钩子函数执行完毕后，
    依次从 SIGNALS_LIST 取出信号，重新传入原 handle_exit 函数处理。

    此钩子优先级非常高，如果在钩子时发生错误，可能会导致程序无法正常关闭。
    """
    raw_handle_exit = Server.handle_exit

    def hook_handle_exit(self: Server, sig, frame):
        # 此处如果打印日志会导致信号不及时无法捕捉
        # logger.opt(colors=True).debug(f"<red>接收到关闭信号{sig}</>")
        SIGNALS_LIST.append(sig)
        raw_handle_exit(self, sig, frame)

    async def process_shutdown_signals(self):
        if SIGNALS_LIST:
            await shutdown_before()
            for sig in SIGNALS_LIST:
                logger.debug(f"发送Hook信号 {sig}")
                raw_handle_exit(self, sig, None)
            SIGNALS_LIST.clear()

    async def custom_main_loop(self: Server) -> None:
        counter = 0
        should_exit = await self.on_tick(counter)
        while not should_exit:
            counter += 1
            counter = counter % 864000
            await sleep(0.1)
            should_exit = await self.on_tick(counter)
            await process_shutdown_signals(self)

    Server.handle_exit = hook_handle_exit
    Server.main_loop = custom_main_loop

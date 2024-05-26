# nonebot-plugin-shutdown-hook

该插件提供一个高优先级关闭信号钩子,用于在关闭时,Bot断开之前执行一些操作
例如对所有未关闭的Matcher进行回复,修改Bot昵称或签名为已关机等

在 nonebot.run() 之前调用此函数, 用 on_shutdown_before 装饰需要执行的函数即可

通过修改 Server.handle_exit，在 handle_exit 函数接收到中止信号后并不立刻中止，而是将信号存储在 SIGNALS_LIST，并立刻执行注册的钩子函数。钩子函数执行完毕后，依次从 SIGNALS_LIST 取出信号，重新传入原 handle_exit 函数处理。

此钩子优先级非常高，如果在钩子时发生错误，可能会导致程序无法正常关闭。

## 安装

```shell
pip install nonebot-plugin-shutdown-hook
```

## 使用

### 导入

```python
from nonebot-plugin-shutdown-hook import override_uvicorn_shutdown_hooks, on_shutdown_before
```

### 创建


```python
# bot.py 文件
...
override_uvicorn_shutdown_hooks()
...
if __name__ == "__main__":
    nonebot.run()
...
```


```python
@on_shutdown_before()
async def func():
    # 执行一些操作
    ...
```

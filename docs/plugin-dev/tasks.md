# 后台任务与卸载

> **场景**：我想每隔 10 分钟检查一次某个网站有没有更新；插件卸载或重载时，这个循环得跟着停下，不能留在后台。该怎么写？

这一页讲怎么给插件安排后台工作，以及卸载时怎么收尾。读完你能把任务、计时器和连接安排得干净退出。

用 `server.schedule_task` 安排插件的后台工作。请把插件创建的任务、计时器、连接和其他资源保存下来，在卸载时显式收尾。

## 调度工作

接口签名为：

```python
server.schedule_task(callable_or_coroutine, block=False, timeout=None)
```

传入无参 callable，或已经创建的协程对象。同步工作交给同步执行器，协程交给异步执行器。参数类型错误会抛出 `TypeError`。

```python
future = server.schedule_task(lambda: calculate_result())
```

```python
async def calculate_async():
    return await fetch_result()

future = server.schedule_task(calculate_async())
```

接口返回 `concurrent.futures.Future`。`block=True` 会等待完成后返回同一个 Future。`timeout` 是阻塞等待的秒数，`None` 表示持续等待。等待超时或任务抛出异常时，阻塞调用会暴露对应异常。等待超时与任务取消要分别处理，工作本身仍需收尾。

异步代码通过 `await asyncio.wrap_future(future)` 等待结果，同步代码使用 `.result()`。Future 回调只做简短的结果处理。耗时工作请另行调度，所需数据和命令上下文显式传入。QQ 发送结果见[回复消息](reply.md)。

## 让同步工作自己停下来

正在运行的同步工作需要定期检查停止信号，收到信号后自己退出。下面示例在加载时创建信号，卸载时发出信号并尝试取消待执行任务：

```python
import threading

_stop = None
_task = None

def worker(server, stop):
    while not stop.wait(1):
        server.logger.debug('Background task tick')

def on_load(server, prev_module):
    global _stop, _task
    stop = threading.Event()
    _stop = stop
    _task = server.schedule_task(lambda: worker(server, stop))

def on_unload(server):
    if _stop is not None:
        _stop.set()
    if _task is not None:
        _task.cancel()
```

`Future.cancel()` 只负责可取消的 Future 状态。已经在运行的同步工作由工作本身自己退出。请把循环里的每一步都做成能结束的操作。资源关闭安排在工作退出之后，避免任务继续使用已关闭的资源。

## 完成卸载

卸载就像收拾东西离场：先停止提交新事情，告诉正在干活的任务"该停了"，等它们收尾，最后关灯、关门。

在 `on_unload` 中按资源依赖安排清理：

1. 停止提交新工作和回复。
2. 向任务发出取消或停止信号。
3. 协调正在运行的工作退出。
4. 关闭插件创建的计时器、连接、文件和其他外部资源。

命令、帮助、事件和翻译登记随插件生命周期清除。插件创建的后台工作与外部资源由插件负责清理。加载过程中发生异常时，也由插件自身清理已创建的资源。

重载时，先结束旧模块的回复和命令登记工作，再交给新模块。使用 `prev_module` 迁移状态时，同步安排旧资源的归属与关闭。

实例进入停止状态后，会拒绝新注册、新任务和新 QQ 操作。此时调用 `schedule_task` 会抛出 `RuntimeNotReadyError`。连接状态与加载生命周期分别处理，参见[插件是怎么运行的](basic.md#插件的生命周期)。

接下来，阅读[元数据](metadata.md)，准备发布插件时写好身份信息和依赖。

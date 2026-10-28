# 后台任务与卸载

> **场景**：我想每隔 10 分钟检查一次某个网站有没有更新；插件卸载或重载时，这个循环得跟着停下，不能留在后台。该怎么写？

这一页讲怎么给插件安排后台工作，以及卸载时怎么收尾。读完这一页，你能让任务、计时器和连接都干净地退出。

短时工作交给 `server.schedule_task`，长期循环放到独立的线程或协程里。插件创建的线程、任务、计时器、连接和其他资源，请自己保存好，卸载时亲手收尾。框架不会替你停止它们。

## 调度工作

`schedule_task` 的签名是：

```python
server.schedule_task(callable_or_coroutine, *, block=False, timeout=None)
```

第一个参数可以是无参的 callable，也可以是已经创建好的协程对象；`block` 和 `timeout` 只能用关键字传入。同步工作会交给同步执行器，协程会交给异步执行器。参数类型不对会抛出 `TypeError`。

同步执行器只有一个线程。QQ 事件、命令回调以及插件的加载和卸载，都在这个线程上排队执行。所以交给它的 callable 要尽快结束，否则会拖住整个机器人。协程在异步执行器的事件循环里运行，需要等待时请用 `await`，不要调用会阻塞的函数。

```python
future = server.schedule_task(lambda: calculate_result())
```

```python
async def calculate_async():
    return await fetch_result()

future = server.schedule_task(calculate_async())
```

`schedule_task` 返回一个 `concurrent.futures.Future`。`block=True` 时，它会等任务完成，再返回同一个 Future。`timeout` 是阻塞等待的秒数，`None` 表示一直等下去。

- 等待超时，会抛出 `concurrent.futures.TimeoutError`（Python 3.11 起它就是内置的 `TimeoutError`）。
- 任务抛出异常，阻塞调用会把这个异常重新抛出来。

注意，超时只是不再等待，任务本身还在运行，该收尾的还得收尾。

异步代码用 `await asyncio.wrap_future(future)` 等待结果，同步代码用 `.result()`。

不要在执行这个任务的执行器线程上等它。比如在命令回调或 `on_load` 里，对同步任务使用 `block=True` 或 `.result()`，会立即抛出 `RuntimeError`（MCDR 的 `SelfJoinError`）。

Future 回调里只做简短的结果处理。耗时的工作请另外调度，并把需要的数据和命令上下文作为参数传进去。QQ 发送结果的处理见[回复消息](reply.md)。

## 让同步工作自己停下来

正在运行的同步工作要定期检查停止信号，收到信号后自己退出。长期循环不要交给 `schedule_task` 的同步执行器：它会一直占着处理事件和命令的线程，连 `on_unload` 都排不上队。下面的示例用 `new_thread` 开一个独立线程，每 10 分钟检查一次；加载时创建停止信号，卸载时发出信号，并等待线程结束：

```python
import threading

from botqraft.api.decorator import new_thread

_stop = None
_worker = None

@new_thread('UpdateChecker')
def check_updates(server, stop):
    # wait() returns True as soon as the stop signal is set.
    while not stop.wait(600):
        server.logger.info('Checking for updates')

def on_load(server, prev_module):
    global _stop, _worker
    _stop = threading.Event()
    _worker = check_updates(server, _stop)

def on_unload(server):
    if _stop is not None:
        _stop.set()
    if _worker is not None:
        _worker.join(timeout=5)
```

对 `schedule_task` 返回的 Future 调用 `cancel()`，只能拦下还在排队的同步任务。已经开始运行的同步任务和协程都不会被打断：即使 `cancel()` 返回了 `True`，也得靠工作自己检查信号后退出。所以，请让循环里的每一步都能结束。关闭资源要放在工作退出之后，免得任务还在用已经关掉的资源。

## 完成卸载

卸载就像收拾东西离场：先停止提交新事情，告诉正在干活的任务“该停了”，等它们收尾，最后关灯、关门。

在 `on_unload` 里，按资源之间的依赖关系依次清理：

1. 停止提交新工作和回复。
2. 向任务发出取消或停止信号。
3. 等正在运行的工作收尾退出。
4. 关闭插件创建的计时器、连接、文件和其他外部资源。

命令、帮助、事件和翻译的登记，会随插件的生命周期自动清除。但插件自己创建的后台工作和外部资源，要由插件自己清理。如果加载过程中出了异常，已经创建的资源同样由插件自己清理。

重载时，框架先调用旧模块的 `on_unload`，再导入新模块，调用它的 `on_load(server, prev_module)`，这里的 `prev_module` 就是旧模块。如果要通过 `prev_module` 迁移状态，记得同时想清楚旧资源归谁、由谁关闭。

实例进入停止状态后，会拒绝新的注册、任务和 QQ 操作，这时调用 `schedule_task` 会抛出 `RuntimeNotReadyError`。实例关闭时，正是在停止状态下逐个卸载插件的，所以 `on_unload` 里的收尾要当场完成，不要再交给 `schedule_task`。连接状态和加载生命周期是两回事，要分开处理，参见[插件是怎么运行的](basic.md#插件的生命周期)。

接下来，阅读[元数据](metadata.md)，准备发布插件时写好身份信息和依赖。

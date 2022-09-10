# bilibili live websocket danmaku (?)

## 声明

请勿滥用！本文件夹内的文件仅用于学习和测试。上传至GitHub仅为了方便和备份。

使用或修改本文件夹内的文件所引发的争议及后果与本人无关。

一旦出现任何情况，本人随时可删除本文件夹。

**程序并不考虑交互**

使用的编程语言: [Python](https://www.python.org/)

## 文件

### [bili_live_ws.py]

直播信息流

**仅实现核心功能**

> 需要依赖: `requests` , `websockets`

具体的选项请输入 `-h` 或 `--help` 来查看帮助

一些异常并未进行捕捉，遇到解释器打印异常时，请不用惊慌，这是正常现象。因为该程序并未考虑用户交互，也不完善。

```shell
python bili_live_ws.py -h
```

注: 实际使用可能出现一些shell命令调用，并且使用的是无效命令。此情况很可能是本人将自用的文件直接复制过来。遇到此情况可打开issue来通知，但不保证会进行修正。

**非BUG相关请开讨论！**

### [bili_live_msg.py]

在 bili_live_ws.py 的基础上增加了信息获取。

### [default_args.txt]

~~默认命令行参数~~

### [bili_args.txt]

仿照互动区域可能显示的内容来显示信息

### [msg_args.txt]

只显示弹幕或留言(理论上是这样)

### [bili live msg.py]

获取信息流

仅支持zlib解压缩

自动切割数据包

用法:
```shell
python "bili live msg.py" [roomid]
```
> 参数: roomid可选,输入实际房间号

### [bilibili live data.py]

找出未知的命令

## 参考

[SocialSisterYi/bilibili-API-collect](https://github.com/SocialSisterYi/bilibili-API-collect) 提供数据包格式和URL

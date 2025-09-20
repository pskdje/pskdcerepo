# mcws

Minecraft 基岩版 WebSocket 服务器框架

## 依赖

Python >3.10 (未在旧版本测试)

- websockets

## 使用

直接启动该文件将会调用 `RunMCWS` 的 start 方法启动服务器，该服务器仅有打印客户端发回消息和加入服务器时向客户端订阅玩家聊天功能。

请继承 `MinecraftWS` 类来定制你所需要的功能。

在游戏内通过 `/wsserver` 命令或别名来连接到服务器。[zh Minecraft Wiki 页面](https://zh.minecraft.wiki/w/命令/wsserver)

## 编写指引

通过继承 `MinecraftWS` 类来实现具体功能，详细信息请查看源代码。

主要需要重写的异步方法: `mcws_handle` `mcws_join_event` `mcws_exit_event`

该类有提供一些工具方法。

关于如何处理数据包和订阅事件请参见[中文Minecraft Wiki](https://zh.minecraft.wiki/) 的 [教程:WebSocket](https://zh.minecraft.wiki/w/Tutorial:WebSocket) 页面。

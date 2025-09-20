"""Minecraft WebSocket
用于Minecraft的WebSocket功能的服务器框架
在游戏内使用 "/wsserver" 或 "/connect" 命令连接
参考: https://zh.minecraft.wiki/w/Tutorial:WebSocket
"""

import asyncio,uuid,json
import websockets

class MinecraftWS:
    """Minecraft的WS服务器"""

    MCWS_server=None
    """服务器容纳"""

    def error(self)->None:
        """错误处理"""
        from traceback import print_exc
        print_exc()

    async def MCWS(self,port:int=19134):
        """启动服务器"""
        self.MCWS_server=await websockets.serve(
            self.mcws_server,
            port=port
        )
        return self.MCWS_server

    def mcws_close(self)->None:
        """关闭服务器"""
        self.broadcast_mc_pack(self.create_close_command())
        if self.MCWS_server:
            self.MCWS_server.close()

    async def mcws_server(self,ws)->None:
        """监听会话运行周期"""
        try:
            await self.mcws_join_event(ws)
            async for msg in ws:
                try:
                    await self.mcws_handle(json.loads(msg),ws)
                except Exception:
                    self.error(msg)
        except websockets.ConnectionClosed:
            pass
        except(KeyboardInterrupt,asyncio.CancelledError,SystemExit):
            raise
        except:
            self.error()
        finally:
            await self.mcws_exit_event(ws)

    async def mcws_handle(self,msg:dict,ws)->None:
        """发回处理"""

    async def mcws_join_event(self,ws)->None:
        """ws会话加入"""

    async def mcws_exit_event(self,ws)->None:
        """ws会话退出"""

    def create_mc_pack(self,messagePurpose:str)->dict:
        """创建数据包"""
        return {
            "body":{},
            "header":{
                "requestId":str(uuid.uuid4()),
                "messagePurpose":messagePurpose,
                "version":1,
            }
        }

    def create_subscribe(self,event:str)->dict:
        """创建订阅请求"""
        d=self.create_mc_pack("subscribe")
        d["body"]["eventName"]=str(event)
        return d

    def create_unsubscribe(self,event:str)->dict:
        """创建取消订阅请求"""
        d=self.create_mc_pack("unsubscribe")
        d["body"]["eventName"]=str(event)
        return d

    def create_commandRequest(self,command:str,version:int=1)->dict:
        """创建命令请求"""
        d=self.create_mc_pack("commandRequest")
        d["body"]={
            "origin":{
                "type":"player"
            },
            "commandLine":command,
            "version":version,
        }
        return d

    def create_close_command(self)->dict:
        """创建关闭WS命令"""
        return self.create_commandRequest("closewebsocket")

    def broadcast_mc_pack(self,msg:dict,*,has_ignore_nostart:bool=False)->None:
        """广播数据"""
        if self.MCWS_server is None:
            if has_ignore_nostart:
                return
            raise RuntimeError("未检测到 MC WS 服务器启动")
        return websockets.broadcast(self.MCWS_server.connections,json.dumps(msg))

    def broadcast_command(self,command:str,version:int=1,**other)->None:
        """广播Minecraft命令"""
        d=self.create_commandRequest(command,version)
        return self.broadcast_mc_pack(d,**other)

    def broadcast_say(self,msg:str,**other)->None:
        """广播say命令"""
        self.broadcast_command(f"say {msg}",**other)

    def broadcast_me(self,msg:str,**other)->None:
        """广播me命令"""
        self.broadcast_command(f"me {msg}",**other)

class RunMCWS(MinecraftWS):
    """运行MCWS，用于测试"""

    async def mcws_handle(self,msg,ws):
        print(ws.remote_address,"=>",msg)

    async def mcws_join_event(self,ws):
        print(ws.remote_address,"加入服务器")
        await ws.send(json.dumps(self.create_subscribe("PlayerMessage")))

    async def mcws_exit_event(self,ws):
        print(ws.remote_address,"退出服务器")

    async def start(self):
        s=await self.MCWS()
        print("MCWS 测试会话已在 19134 端口启动。")
        await s.wait_closed()

if __name__=="__main__":
    s=RunMCWS()
    asyncio.run(s.start())

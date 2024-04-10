#!/usr/bin/env python
"""哔哩哔哩直播信息流
直接使用bili_live_ws的功能
在该基础上增加一些功能
使用的第三方库: requests
还需注意bili_live_ws使用的第三方库
可以尝试给予本文件执行权限来直接运行
"""

import time
from sys import exit
import requests
import bili_live_ws as blw

ua=blw.UA

def __getattr__(name):
    return getattr(blw,name)
def get_room_init(roomid:int)->dict:
    try:
        r=requests.get(
            "https://api.live.bilibili.com/room/v1/Room/room_init?id="+str(roomid),
            headers={"User-Agent":ua}
        )
    except Exception:
        blw.error()
        exit("获取房间初始化信息失败")
    if r.status_code!=200:
        print(r.text)
        blw.save_http_error(r,"状态码")
        exit("服务器错误")
    d=r.json()
    if d["code"]==60004:
        print("直播间不存在")
        exit(0)
    if d["code"]!=0:
        print("room_init接口返回的code不为0")
        print(d["code"],"-",d["message"])
        blw.save_http_error(r,"键code")
        exit(1)
    return d["data"]

def get_room_info(mid:int)->dict:
    try:
        r=requests.get(
            "https://api.live.bilibili.com/room/v1/Room/get_info?room_id="+str(mid),
            headers={"User-Agent":ua}
        )
    except Exception:
        blw.error()
        exit("获取直播间信息失败")
    if r.status_code!=200:
        print(r.text)
        save_http_error(r,"状态码")
        exit("服务器错误")
    d=r.json()
    if d["code"]!=0:
        print("room_info获取到的code不为0")
        print(d["code"],"-",d["message"])
        save_http_error(r,"键code")
        exit(1)
    return d["data"]

def main():
    try:
        o=blw.pararg()
        if blw.DEBUG:
            print("版本信息:",blm.VERSIONINFO)
            print("命令行参数:",o)
            blw.set_wslog()
        print("获取数据…")
        ri=get_room_init(o.roomid)
        ru=get_room_info(ri["room_id"])
        print("直播间:",ri["room_id"],""if ri["short_id"]==0 else f"({ri['short_id']})")
        print("用户ID:",ri["uid"])
        print("状态:",end=" ")
        lis=ri["live_status"]
        if lis==0:
            print("未开播")
        elif lis==1:
            print("直播中")
        elif lis==2:
            print("轮播中")
        else:
            print(lis)
        del lis
        print("开播时间:",end=" ")
        if ri["live_time"]>0:
            print(time.strftime(blw.TIMEFORMAT,time.localtime(ri["live_time"])))
        else:
            print("未开播")
        print("标题:",ru["title"])
        print("封面:",ru["user_cover"])
        print("背景图:",ru["background"])
        print("关键帧:",ru["keyframe"])
        print("《简介》:`",ru["description"],"`")
        print("分区:",ru["parent_area_name"],">",ru["area_name"])
        print("开始时间:",ru["live_time"])
        print("观看人数:",ru["online"])
        print("标签:",ru["tags"])
        if ru["live_status"]==0:
            print("当前直播间未直播，将自动退出。")
            exit(0)
        # live
        print("载入数据…")
        if o.shielding_words:
            blw.shielding_words(o.shielding_words)
        if o.blocking_rules:
            blw.blocking_rules(o.blocking_rules)
        if o.atirch:
            r_ich=blw.import_cmd_handle()
            if blw.DEBUG:print("导入命令处理的结果:",r_ich)
        print("连接直播间…")
        blw.start(ri["room_id"],o)
    except Exception:
        print("出现错误")
        blw.error()
        exit(1)
    except KeyboardInterrupt:
        print("关闭")
        if blw.DEBUG or o.print_pack_count:
            print("被测试的cmd计数:")
            blw.print_test_pack_count()
        exit(0)

if __name__=="__main__":
    print("哔哩哔哩直播信息流")
    print("额外获取一些信息")
    main()

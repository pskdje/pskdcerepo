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

ua="Mozilla/5.0 (X11; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0"

def get_room_init(roomid:int)->dict:
    try:
        r=requests.get("https://api.live.bilibili.com/room/v1/Room/room_init?id="+str(roomid),headers={"User-Agent":ua})
    except:
        blw.error()
        exit("获取房间初始化信息失败")
    if r.status_code!=200:
        print(r.text)
        exit("服务器错误")
    d=r.json()
    if d["code"]==60004:
        print("直播间不存在")
        exit(0)
    assert d["code"]==0,"room_init code not 0"
    return d["data"]

def get_room_info(mid:int)->dict:
    try:
        r=requests.get("https://api.live.bilibili.com/room/v1/Room/get_info?room_id="+str(mid),headers={"User-Agent":ua})
    except:
        blw.error()
        exit("获取直播间信息失败")
    if r.status_code!=200:
        print(r.text)
        exit("服务器错误")
    d=r.json()
    if d["code"]!=0:
        print(d["code"],d["message"])
        exit(1)
    return d["data"]

def main():
    try:
        o=blw.pararg()
        if not __debug__:
            print("命令行参数:",o)
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
        print("连接直播间…")
        blw.main(ri["room_id"],o)
    except Exception:
        print("出现错误")
        blw.error()
        exit(1)

if __name__=="__main__":
    print("哔哩哔哩直播信息流")
    print("额外获取一些信息")
    try:
        main()
    except KeyboardInterrupt:
        print("关闭")
        exit(0)

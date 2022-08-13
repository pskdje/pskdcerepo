# bilibili live 数据分析

import os
import json

cmdl=(
    "INTERACT_WORD",# 活动
    "DANMU_MSG",# 弹幕
    "WATCHED_CHANGE",# 看过
    "ENTRY_EFFECT",# 进场
    "SEND_GIFT",# 礼物
    "SUPER_CHAT_MESSAGE",# 醒目留言
    "SUPER_CHAT_MESSAGE_JPN",# 醒目留言(日本)
    "LIVE_INTERACTIVE_GAME",
    "ONLINE_RANK_COUNT",
    "STOP_LIVE_ROOM_LIST",# 停止直播房间列表
    "ROOM_REAL_TIME_MESSAGE_UPDATE",# 数据更新
    "HOT_RANK_CHANGED",# 当前直播间的排行
    "HOT_RANK_CHANGED_V2",
    "ONLINE_RANK_TOP3",# 前三个第一次成为高能用户
    "ONLINE_RANK_V2",
    "WIDGET_BANNER",
    "NOTICE_MSG",# 通知
    "GUARD_BUY",# 舰队购买
    "USER_TOAST_MSG",
)
fl=os.listdir("bili live msg data")
for i in fl:
    with open("bili live msg data/"+i)as f:
        try:
            l=json.load(f)
        except:
            print("file:",i)
            raise
        else:
            for item in l:
                if item["cmd"]not in cmdl:
                    print("file:",i)
                    print(item)

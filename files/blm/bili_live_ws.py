"""哔哩哔哩直播信息流
使用的第三方库: requests , websockets
数据包参考自: https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/live/message_stream.md
数据分析由我自己进行(日期:2022/08/20，请注意时效)
本文件计划只实现基本功能
"""

import sys
import time
import json
import re
import zlib
import traceback
import requests
import asyncio
import websockets

if not(sys.version_info[0]==3 and sys.version_info[1]>=10):
    print("Python 版本需要大于等于3.10")
    print("否则会出现语法错误")
    print("Python version >= 3.10")
    sys.exit(1)

DEBUG=not __debug__
TIMEFORMAT="%Y/%m/%d-%H:%M:%S"
runoptions=None
sequence=0
hpst=None
swd=[]
brs=[]

def error(d=None):
    with open("bili_live_ws_err.txt","w")as f:
        f.write("哔哩哔哩直播信息流\n时间:")
        f.write(time.strftime("%Y/%m/%d-%H:%M:%S%z"))
        f.write("\n命令行选项: "+str(runoptions))
        f.write("\n部分参数:\n")
        f.write("\tDEBUG= "+str(DEBUG))
        f.write("\n\tsequence= "+str(sequence))
        f.write("\n\thpst: "+repr(hpst))
        f.write("\n\tlen(swd)="+str(len(swd)))
        f.write("\n\tlen(brs)="+str(len(brs)))
        f.write("\n异常:\n")
        traceback.print_exc(file=f)
        f.flush()
        if d!=None:
            f.write("\n其它信息:\n\n"+str(d))

def bilipack(t,da):
    global sequence
    d=str(da).encode()
    db=b""
    db+=bytes.fromhex("{:0>8X}".format(16+len(d)))
    db+=b"\0\x10"b"\0\x01"
    db+=b"\0\0\0"+bytes.fromhex("0"+str(t))
    db+=bytes.fromhex("{:0>8X}".format(sequence))
    db+=d
    sequence+=1
    return db

def joinroom(id,k):
    return bilipack(7,json.dumps({"roomid":id,"key":k},separators=(",",":")))

def hp():
    return bilipack(2,"")

async def hps(ws):
    while not ws.closed:
        await ws.send(hp())
        await asyncio.sleep(30)

def fahp(data):
    num=0
    if not isinstance(data,bytes):
        raise TypeError("bytes")
    for i in data:
        num+=i
    return num

def femsgd(msg):
    data=msg.split(b"\0\x10\0\0\0\0\0\x05\0\0\0\0")[1:]
    packlist=[]
    for item in data:
        if item[-4]==0:
            packlist.append(json.loads(item[:-4]))
        else:
            packlist.append(json.loads(item))
    return packlist

def pac(pack,o):
    match pack["cmd"]:
        case "DANMU_MSG":# 弹幕
            l_danmu_msg(pack["info"])
        case "INTERACT_WORD":# 交互
            if not o.no_interact_word:
                l_interact_word(pack["data"],o)
        case "ENTRY_EFFECT":# 进场
            if not o.no_entry_effect:
                l_entry_effect(pack["data"])
        case "SEND_GIFT":# 礼物
            if not o.no_send_gift:
                l_send_gift(pack["data"])
        case "COMBO_SEND":
            if not o.no_combo_send:
                l_combo_send(pack["data"])
        case "WATCHED_CHANGE":# 看过
            if not o.no_watched_change:
                l_watched_change(pack["data"])
        case "SUPER_CHAT_MESSAGE":# 醒目留言
            if not o.no_super_chat_message:
                l_super_chat_message(pack["data"])
        case "SUPER_CHAT_MESSAGE_JPN":# 醒目留言(日本)
            pass
        case "LIVE_INTERACTIVE_GAME":
            pass
        case "ROOM_CHANGE":# 直播间更新(推测)
            print("[直播]","分区:",pack["data"]["parent_area_name"],">",pack["data"]["area_name"],",标题:",pack["data"]["title"])
        case "LIVE":# 开始直播(推测)
            print("[直播]",pack["roomid"],"开始直播")
        case "PREPARING":# 结束直播(推测)
            print("[直播]",pack["roomid"],"结束直播")
        case "ROOM_REAL_TIME_MESSAGE_UPDATE":# 数据更新
            l_room_real_time_message_update(pack["data"])
        case "STOP_LIVE_ROOM_LIST":# 停止直播的房间列表(推测)
            if not o.no_stop_live_room_list:
                l_stop_live_room_list(pack["data"])
        case "HOT_RANK_CHANGED":# 当前直播间的排行
            if not o.no_hot_rank_changed:
                l_hot_rank_changed(pack["data"])
        case "HOT_RANK_CHANGED_V2":
            pass
        case "ONLINE_RANK_COUNT":# (确认)
            if not o.no_online_rank_count:
                print("[信息]","高能用户计数:",pack["data"]["count"])
        case "ONLINE_RANK_TOP3":# 前三个第一次成为高能用户
            if not o.no_online_rank_top3:
                l_online_rank_top3(pack["data"])
        case "ONLINE_RANK_V2":
            if not o.no_online_rank_v2:
                l_online_rank_v2(pack["data"],o.no_print_enable)
        case "HOT_RANK_SETTLEMENT":# 热门通知
            if not o.no_hot_rank_settlement:
                l_hot_rank_settlement(pack["data"])
        case "HOT_RANK_SETTLEMENT_V2":# 同上
            pass
        case "HOT_ROOM_NOTIFY":
            pass
        case "COMMON_NOTICE_DANMAKU":# 普通通知
            if not o.no_common_notice_danmaku:
                l_common_notice_danmaku(pack["data"])
        case "NOTICE_MSG":# 公告
            if not o.no_notice_msg:
                l_notice_msg(pack)
        case "GUARD_BUY":
            if not o.no_guard_buy:
                l_guard_buy(pack["data"])
        case "USER_TOAST_MSG":
            if not o.no_user_toast_msg:
                l_user_toast_msg(pack["data"])
        case "WIDGET_BANNER":# 小部件
            if not o.no_widget_banner:
                l_widget_banner(pack["data"])
        case "ROOM_SKIN_MSG":# 直播间皮肤更新
            l_room_skin_msg(pack)
        case "LIVE_MULTI_VIEW_CHANGE":
            print("[信息]","LIVE_MULTI_VIEW_CHANGE",pack["data"])
        case _:# 未知命令
            if not o.no_print_enable:
                print(f"[支持] 不支持'{pack['cmd']}'命令")

def pacs(packlist,o):
    for pack in packlist:
        try:
            pac(pack,o)
        except:
            error("出现异常的数据包:\n"+json.dumps(pack,ensure_ascii=False,indent="\t"))
            sys.exit("数据错误")

async def bililivemsg(url,roomid,o,token):
    global hpst
    if DEBUG:
        print("连接服务器…")
    async with websockets.connect(url)as ws:
        if DEBUG:
            print("服务器已连接")
        await ws.send(joinroom(roomid,token))
        hpst=asyncio.create_task(hps(ws))
        async for msg in ws:
            if msg[7]==1 and msg[11]==3:
                print("[人气]",fahp(msg[16:20]))
            elif msg[7]==1 and msg[11]==8:
                print("[认证]",msg[16:])
            elif msg[7]==0:
                pacs(femsgd(msg),o)
            elif msg[7]==2:
                pacs(femsgd(zlib.decompress(msg[16:])),o)
            else:
                if o.no_print_enable:
                    continue
                print("[支持] 未知的协议版本")
                if DEBUG:
                    print(msg)

def main(roomid,o):
    if DEBUG:
        print("获取直播信息流地址…")
    try:
        r=requests.get("https://api.live.bilibili.com/xlive/web-room/v1/index/getDanmuInfo?id="+str(roomid))
    except:
        print(sys.exc_info()[1])
        if DEBUG:
            raise
    else:
        if r.status_code!=200:
            print("数据获取失败")
            print("HTTP",r.status_code)
            sys.exit(1)
        d=r.json()
        assert d["code"]==0,"code not 0"
        u=d["data"]["host_list"][0]
        try:
            asyncio.run(bililivemsg(f"""ws://{u["host"]}:{u["ws_port"]}/sub""",roomid,o,d["data"]["token"]))
        except websockets.exceptions.ConnectionClosedError as e:
            error()
            print("异常关闭\n"+e.__class__.__name__+": "+str(e))
            sys.exit(1)

def shielding_words(f):
    print("解析屏蔽词…")
    t=None
    try:
        t=f.readline()
        while t!="":
            if t[0]=="#":
                t=f.readline()
                continue
            swd.append(t)
            t=f.readline()
    except:
        print("处理屏蔽词时出现错误",file=sys.stderr)
        error()
    finally:
        f.close()

def blocking_rules(f):
    print("解析屏蔽规则…")
    t=None
    try:
        t=f.readline()
        while t!="":
            if t[0]=="#":
                t=f.readline()
                continue
            brs.append(re.compile(t))
            t=f.readline()
    except:
        print("处理屏蔽规则时出现错误",file=sys.stderr)
        error()
    finally:
        f.close()

# 命令处理调用处(开始)
def l_danmu_msg(d):
    if d[1]in swd:
        return
    for b in brs:
        if b.search(d[1]):
            return
    print("[弹幕]",f"{d[2][1]}:",d[1])
def l_interact_word(d,o):
    info="[交互]"
    if d["msg_type"]==1:
        if not o.no_enter_room:
            print(info,d["uname"],"进入直播间",sep=" ")
    elif d["msg_type"]==2:
        print(info,d["uname"],"关注直播间",sep=" ")
    elif d["msg_type"]==3:
        print(info,d["uname"],"分享直播间",sep=" ")
    else:
        if not o.no_print_enable:
            print("[支持]","未知的交互类型:",d["msg_type"])
def l_entry_effect(d):
    print("[进场]",d["copy_writing"])
def l_send_gift(d):
    print("[礼物]",d["uname"],d["action"],d["giftName"],"*",d["num"],sep=" ")
def l_combo_send(d):
    print("[礼物]",d["uname"],d["action"],d["gift_name"],"*",d["total_num"],sep=" ")
def l_watched_change(d):
    if __debug__:
        print("[观看]",d["num"],"人看过")
    else:
        print("[观看]",d["num"],"人看过;","text_large:",d["text_large"])
def l_super_chat_message(d):
    print("[留言]",f"{d['user_info']['uname']}(￥{d['price']}):",d["message"])
def l_room_real_time_message_update(d):
    print("[信息]",d["roomid"],"直播间",d["fans"],"粉丝",sep=" ")
def l_stop_live_room_list(d):
    print("[直播]","停止直播的房间列表:",f"len({len(d['room_id_list'])})")
def l_hot_rank_changed(d):
    print("[排行]",d["area_name"],"第",d["rank"],"名")
def l_online_rank_top3(d):
    if __debug__:
        print("[排行]",d["list"][0]["msg"],f"rank:{d['list'][0]['rank']}")
    else:
        print("[排行]",f"len({len(d['list'])})",d["list"][0]["msg"],f"rank:{d['list'][0]['rank']}")
def l_online_rank_v2(d,npe):
    if d["rank_type"]=="gold-rank":
        print("[排行]","高能用户部分列表:",f"len({len(d['list'])})")
    else:
        if not npe:
            print("[支持]","未知的排行类型:",d["rank_type"])
def l_hot_rank_settlement(d):
    print("[排行]",d["dm_msg"])
def l_common_notice_danmaku(d):
    for cse in d["content_segments"]:
        print("[通知]",cse["text"])
def l_notice_msg(d):
    if "name"in d:
        print("[公告]",d["name"],"=>",d["msg_self"])
    else:
        print("[公告]",d["msg_self"])
def l_guard_buy(d):
    print("[礼物]",d["username"],"购买了",d["num"],"个",d["gift_name"])
def l_user_toast_msg(d):
    print("[提示]",d["toast_msg"])
def l_widget_banner(d):
    for wi in d["widget_list"]:
        if d["widget_list"][wi]==None:
            continue
        print("[小部件]",f"key:{wi}","id",d["widget_list"][wi]["id"],"标题:",d["widget_list"][wi]["title"])
def l_room_skin_msg(d):
    print("[信息]","直播间皮肤更新","id:",d["skin_id"],",status:",d["status"],",结束时间:",time.strftime(TIMEFORMAT,time.gmtime(d["end_time"])),",当前时间:",time.strftime(TIMEFORMAT,time.gmtime(d["current_time"])),sep=" ")
# 命令处理调用处(结束)

if __name__=="__main__":
    import argparse
    desc="哔哩哔哩直播信息流处理\n允许使用@来引入参数文件"
    parser=argparse.ArgumentParser(usage="%(prog)s [options] roomid",description=desc,formatter_class=argparse.RawDescriptionHelpFormatter,fromfile_prefix_chars="@")
    parser.add_argument("roomid",help="直播间ID",type=int,default=23058)
    parser.add_argument("--no-print-enable",help="不打印不支持的信息",action="store_true")
    parser.add_argument("--no-interact-word",help="关闭直播间交互信息",action="store_true")
    parser.add_argument("--no-entry-effect",help="关闭进场信息",action="store_true")
    parser.add_argument("--no-send-gift",help="关闭礼物信息",action="store_true")
    parser.add_argument("--no-combo-send",help="关闭组合礼物信息",action="store_true")
    parser.add_argument("--no-watched-change",help="关闭看过信息",action="store_true")
    parser.add_argument("--no-super-chat-message",help="关闭醒目留言信息",action="store_true")
    parser.add_argument("--no-stop-live-room-list",help="关闭停止直播的房间列表信息",action="store_true")
    parser.add_argument("--no-hot-rank-changed",help="关闭当前直播间的排行信息",action="store_true")
    parser.add_argument("--no-online-rank-count",help="关闭高能用户计数信息",action="store_true")
    parser.add_argument("--no-online-rank-top3",help="关闭前三个第一次成为高能用户信息",action="store_true")
    parser.add_argument("--no-online-rank-v2",help="关闭ONLINE_RANK_V2信息",action="store_true")
    parser.add_argument("--no-hot-rank-settlement",help="关闭热门通知信息",action="store_true")
    parser.add_argument("--no-common-notice-danmaku",help="关闭普通通知信息",action="store_true")
    parser.add_argument("--no-notice-msg",help="关闭公告信息",action="store_true")
    parser.add_argument("--no-guard-buy",help="关闭购买舰队信息",action="store_true")
    parser.add_argument("--no-user-toast-msg",help="关闭USER_TOAST_MSG信息",action="store_true")
    parser.add_argument("--no-widget-banner",help="关闭小部件信息",action="store_true")
    parser.add_argument("--no-enter-room",help="关闭进入直播间信息",action="store_true")
    parser.add_argument("--shielding-words",help="屏蔽词(完全匹配)",type=argparse.FileType("rt"))
    parser.add_argument("--blocking-rules",help="屏蔽规则",type=argparse.FileType("rt"))
    args=parser.parse_args()
    print("哔哩哔哩直播信息流")
    if not __debug__:
        print("命令行选项: ",args)
    runoptions=args
    roomid=args.roomid
    print("直播间ID:",roomid)
    if args.shielding_words:
        shielding_words(args.shielding_words)
    if args.blocking_rules:
        blocking_rules(args.blocking_rules)
    print("连接直播间…")
    try:
        main(roomid,args)
    except KeyboardInterrupt:
        print("关闭")
        sys.exit(0)
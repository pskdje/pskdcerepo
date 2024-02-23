"""哔哩哔哩直播信息流
使用的第三方库: requests , websockets
可选的第三方库: brotli
数据包参考自: https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/live/message_stream.md
数据分析由我自己进行，请注意时效(更新日期:2024/02/22,更新条目)
已存在的cmd很难确认是否需要更新
本文件计划只实现基本功能
本文件自带一个异常保存功能，出现异常时调用error函数即可。
但要注意：它能记录的信息是有限的，并要尽快记录一些信息。因此，你可能需要自行处理一些信息。
"""

import sys,os,time,json,re,zlib
import errno,logging,traceback
import requests
import asyncio
import websockets
from pathlib import Path
try:
    import brotli
except ImportError:
    brotli=None

if not(sys.version_info[0]==3 and sys.version_info[1]>=10):
    print("Python 版本需要大于等于3.10",file=sys.stderr)
    print("否则会出现语法错误",file=sys.stderr)
    print("Python version >= 3.10",file=sys.stderr)
    sys.exit(1)

DEBUG=not __debug__
TIMEFORMAT="%Y/%m/%d-%H:%M:%S"
UA="Mozilla/5.0 (X11; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0"
VERSIONINFO=f"""Python/{sys.version.split()[0]}({sys.platform}) requests/{requests.__version__} websockets/{websockets.__version__}{" brotli/"+brotli.version if brotli else""}"""
starttime=time.time()
wslog=logging.getLogger("websockets.client")
cumulative_error_count=0
runoptions=None
sequence=0
hpst=None
swd=[]
brs=[]
test_pack_count={}
wslog.setLevel(logging.DEBUG)

def error(d=None):
    # 错误记录
    global cumulative_error_count
    dirpath=Path("bili_live_ws_err")
    filepath=dirpath/f"{time.time_ns()}.txt"
    if not dirpath.is_dir():
        dirpath.mkdir()
    try:
        with open(filepath,"w")as f:
            f.write("哔哩哔哩直播信息流\n时间: ")
            f.write(time.strftime("%Y/%m/%d-%H:%M:%S%z"))
            f.write("\n是否为执行入口: "+str(__name__=="__main__"))
            f.write("\n版本信息: "+VERSIONINFO)
            f.write("\n命令行选项: "+str(runoptions))
            f.write("\n用户代理常量: "+str(UA))
            f.write("\n启动时间戳: "+str(starttime))
            f.write("\n累计错误数: "+str(cumulative_error_count))
            f.write("\n部分参数:\n")
            f.write("\tDEBUG= "+str(DEBUG))
            f.write("\n\tsequence= "+str(sequence))
            f.write("\n\thpst: "+repr(hpst))
            f.write("\n\tlen(swd)="+str(len(swd)))
            f.write("\n\tlen(brs)="+str(len(brs)))
            f.write("\n\ttest_pack_count="+str(test_pack_count))
            f.write("\n异常信息:\n")
            f.write("str(exception)=\""+str(sys.exc_info()[1])+"\"\n")
            traceback.print_exc(file=f)
            f.flush()
            if d!=None:
                f.write("\n[其它信息]:\n\n"+str(d))
    except PermissionError as e:
        print("无权限保存异常信息:",e)
    except OSError as e:
        print("无法保存异常信息")
        print("OSError:",e)
    except:
        print("写入异常信息到文件失败！")
        traceback.print_exc()
    else:
        if DEBUG:
            print("错误信息已存储至",str(filepath))
    cumulative_error_count+=1

def bilipack(t,da):
    """返回要发送的数据包\nt: 数据包类型\nda: 数据包内容"""
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

def joinroom(id,k,uid=0):
    """返回加入直播间数据包\n连接后要立即发送
	id: 直播间id
	k: 令牌
	uid: 用户id
	2023/10/04增: 现在需要登录才能获得用户昵称（这么搞有什么用处？）"""
    protover=3 if brotli else 2
    return bilipack(7,json.dumps({"roomid":id,"key":k,"uid":uid,"platform":"web","protover":protover},separators=(",",":")))

def hp():
    """返回心跳包"""
    return bilipack(2,"")

async def hps(ws):
    """每过30秒发送心跳包"""
    try:
        while not ws.closed:
            await ws.send(hp())
            await asyncio.sleep(30)
    except(# 捕捉正常关闭时会引发的异常
           KeyboardInterrupt,
           websockets.exceptions.ConnectionClosedOK
    ):pass# 忽略
    except Exception:
        error()

def fahp(data):
    """合并(用于处理人气值)"""
    if not isinstance(data,bytes):
        raise TypeError("variable 'data' instance not bytes")
    return int.from_bytes(data,"big")

def femsgd(msg):
    """分割数据包"""
    data=msg.split(b"\0\x10\0\0\0\0\0\x05\0\0\0\0")[1:]
    packlist=[]
    try:
        for item in data:
            if len(item)==4:continue
            if item[-4]==0:
                packlist.append(json.loads(item[:-4]))
            else:
                packlist.append(json.loads(item))
        return packlist
    except:
        error("分割数据包时出现错误，原始字节串信息:\n"+str(msg))
        print("无法解析数据")
        return

def save_http_error(r:requests.Response,t:str):
    """保存HTTP错误"""
    header="header:\n"
    for k,v in r.headers.items():
        header+=f"\t{k}: {v}\n"
    blw.error(f"info: {t}\nurl: {r.url}"
        f"status: {r.status_code} {r.reason}\n"+
        header+"body:\n"+r.text+"\n")

class SavePack(RuntimeError):
    """保存数据包"""
    pass

def savepack(d):
    # 保存数据包
    dp=Path("bili_live_ws_pack")
    fp=dp/f"{time.time_ns()}.json"
    if not dp.is_dir():
        dp.mkdir()
    with open(fp,"w")as f:
        f.write(json.dumps(d,ensure_ascii=False,indent="\t",sort_keys=False))

def test_pack_add(c):
    # 对数据包进行计数(理论上能对任何数据进行计数)
    if c not in test_pack_count:
        test_pack_count[c]=1
    else:
        test_pack_count[c]+=1

def pac(pack,o):
    # 匹配cmd,处理内容
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
        case "COMBO_SEND":# 组合礼物(推测)
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
        case "SUPER_CHAT_MESSAGE_DELETE":# 醒目留言删除(推测)
            if not o.no_super_chat_message:
                l_super_chat_message_delete(pack)
        case "LIVE_INTERACTIVE_GAME":# 类似弹幕，未确定
            if not o.no_live_interactive_game:
                l_live_interactive_game(pack["data"])
        case "ROOM_CHANGE":# 直播间更新
            print("[直播]","分区:",pack["data"]["parent_area_name"],">",pack["data"]["area_name"],",标题:",pack["data"]["title"])
        case "LIVE":# 开始直播
            print("[直播]","直播间",pack["roomid"],"开始直播")
        case "PREPARING":# 结束直播
            print("[直播]","直播间",pack["roomid"],"结束直播")
        case "ROOM_REAL_TIME_MESSAGE_UPDATE":# 数据更新
            l_room_real_time_message_update(pack["data"])
        case "STOP_LIVE_ROOM_LIST":# 停止直播的房间列表(推测)
            if not o.no_stop_live_room_list:
                l_stop_live_room_list(pack["data"])
        case "ROOM_BLOCK_MSG":# 用户被禁言
            print("[直播]","用户",pack["uname"],"已被禁言")
        case "CUT_OFF":# 警告
            print("[直播]","直播间",pack["roomid"],"被警告:",pack["msg"])
        case "ROOM_LOCK":# 封禁
            print("[直播]","直播间",pack["roomid"],"被封禁，解除时间:",pack["expire"])
        case "DANMU_AGGREGATION":# 弹幕聚集(?)
            pass
        case "HOT_RANK_CHANGED":# 当前直播间的排行
            test_pack_add(pack["cmd"])# 该功能可能被替代，确认一下
            if not o.no_hot_rank_changed:
                l_hot_rank_changed(pack["data"])
        case "HOT_RANK_CHANGED_V2":
            test_pack_add(pack["cmd"])
        case "ONLINE_RANK_COUNT":# 在线排名
            if not o.no_online_rank_count:
                l_online_rank_count(pack["data"])
        case "VOICE_JOIN_LIST":# 连麦列表(推测,原始数据已删除，暂时不打算重新确定)
            if not o.no_voice_join_list:
                l_voice_join_list(pack["data"])
        case "VOICE_JOIN_ROOM_COUNT_INFO":# 同上，现在无法确定是否与上面的数据相同
            if not o.no_voice_join_list:
                l_voice_join_list(pack["data"])
        case "ONLINE_RANK_TOP3":# 前三个第一次成为高能用户
            if not o.no_online_rank_top3:
                l_online_rank_top3(pack["data"])
        case "VOICE_JOIN_STATUS":# 连麦状态
            if not o.no_voice_join_status:
                l_voice_join_status(pack["data"])
        case "ONLINE_RANK_V2":
            if not o.no_online_rank_v2:
                l_online_rank_v2(pack["data"],o.no_print_enable)
        case "HOT_RANK_SETTLEMENT":# 热门通知
            if not o.no_hot_rank_settlement:
                l_hot_rank_settlement(pack["data"])
        case "HOT_RANK_SETTLEMENT_V2":# 同上
            pass
        case "COMMON_NOTICE_DANMAKU":# 普通通知
            if not o.no_common_notice_danmaku:
                l_common_notice_danmaku(pack["data"])
        case "NOTICE_MSG":# 公告
            if not o.no_notice_msg:
                l_notice_msg(pack)
        case "GUARD_BUY":# 舰队购买
            if not o.no_guard_buy:
                l_guard_buy(pack["data"])
        case "USER_TOAST_MSG":# 舰队续费
            if not o.no_user_toast_msg:
                l_user_toast_msg(pack["data"])
        case "WIDGET_BANNER":# 小部件
            if not o.no_widget_banner:
                l_widget_banner(pack["data"])
        case "SUPER_CHAT_ENTRANCE":# 醒目留言入口变化
            if not o.no_super_chat_entrance:
                l_super_chat_entrance(pack["data"])
        case "ROOM_SKIN_MSG":# 直播间皮肤更新
            l_room_skin_msg(pack)
        case "LIVE_MULTI_VIEW_CHANGE":
            print("[信息]","LIVE_MULTI_VIEW_CHANGE",pack["data"])
        case "POPULARITY_RED_POCKET_NEW":# 新红包(?)
            if not o.no_popularity_red_pocket_new:
                l_popularity_red_pocket_new(pack["data"])
        case "POPULARITY_RED_POCKET_START":# 增加屏蔽词(才怪)
            l_popularity_red_pocket_start(pack["data"])
        case "LIKE_INFO_V3_UPDATE":
            if not o.no_like_info_update:
                print("[计数]","点赞点击数量:",pack["data"]["click_count"])
        case "LIKE_INFO_V3_CLICK":# 点赞点击(推测)
            if not o.no_interact_word:# 使用屏蔽交互信息的选项
                l_like_info_v3_click(pack["data"])
        case "POPULAR_RANK_CHANGED":# 人气排行更新
            if not o.no_popular_rank_changed:
                l_popular_rank_changed(pack["data"])
        case "AREA_RANK_CHANGED":# 大航海排行更新
            if not o.no_area_rank_changed:
                l_area_rank_changed(pack["data"])
        case "DM_INTERACTION":# 弹幕合并
            if not o.no_dm_interaction:
                l_dm_interaction(pack["data"])
        case "PK_BATTLE_PRE"|"PK_BATTLE_PRE_NEW":# PK即将开始
            if not o.no_pk_message:
                l_pk_battle_pre(pack)
        case "PK_BATTLE_START_NEW"|"PK_BATTLE_START":# PK开始
            if not o.no_pk_message:
                l_pk_battle_start(pack)
        case "PK_BATTLE_PROCESS"|"PK_BATTLE_PROCESS_NEW":# PK过程
            if not o.no_pk_message or not o.no_pk_battle_process:
                l_pk_battle_process(pack)
        case "PK_BATTLE_FINAL_PROCESS":# PK结束流程变化(推测)
            if not o.no_pk_message:
                l_pk_battle_final_process(pack)
        case "PK_BATTLE_END":# PK结束
            if not o.no_pk_message:
                l_pk_battle_end(pack)
        case "PK_BATTLE_SETTLE":# PK结算1
            pass
        case "PK_BATTLE_SETTLE_V2":# PK结算2
            if not o.no_pk_message:
                l_pk_battle_settle_v2(pack)
        case "RECOMMEND_CARD":# 推荐卡片
            if not o.no_recommend_card:
                l_recommend_card(pack["data"],o.save_recommend_card)
        case "GOTO_BUY_FLOW":# 购买推荐(?)
            if not o.no_goto_buy_flow:
                l_goto_buy_flow(pack["data"])
        case "LOG_IN_NOTICE":# 登录通知
            print("[需要登录]",pack["data"]["notice_msg"])
        case "ANCHOR_LOT_CHECKSTATUS":# 天选时刻审核状态(?)
            if not o.no_anchor_lot:
                l_anchor_lot_checkstatus(pack["data"])
        case "ANCHOR_LOT_START":# 天选时刻开始
            if not o.no_anchor_lot:
                l_anchor_lot_start(pack["data"])
        case "ANCHOR_LOT_END":# 天选时刻结束
            if not o.no_anchor_lot:
                print("[天选时刻]","id为",pack["data"]["id"],"的天选时刻已结束")
        case "ANCHOR_LOT_AWARD":# 天选时刻开奖
            if not o.no_anchor_lot:
                l_anchor_lot_award(pack["data"])
        case(# 不进行支持
            "HOT_ROOM_NOTIFY"|# 未知，内容会在哔哩哔哩直播播放器日志中显示
            "WIDGET_GIFT_STAR_PROCESS"|# 礼物星球(礼物名)
            "WIDGET_WISH_LIST"|# 愿望清单(机翻)
            "PK_BATTLE_SETTLE_USER"|# 不支持原因: 懒
            "SEND_GIFT_V2"# 礼物第二版(没搞懂意义何在)
        ): test_pack_add(pack["cmd"])
        case _:# 未知命令
            if not o.no_print_enable:
                print(f"[支持] 不支持'{pack['cmd']}'命令")
            if DEBUG or o.save_unknow_datapack:
                savepack(pack)

def pacs(packlist,o):
    # 将数据包列表遍历发送给pac处理
    # 记录出现异常的数据包
    if packlist is None:
        if DEBUG:print("数据包处理函数pacs未收到数据包列表")
        return
    this_error_count=0
    for pack in packlist:
        try:
            pac(pack,o)
        except SavePack:
            if DEBUG or o.save_unknow_datapack:
                savepack(pack)
        except:
            error("出现异常的数据包:\n"+json.dumps(pack,ensure_ascii=False,indent="\t"))
            this_error_count+=1
            print("数据错误",file=sys.stderr)
            ie=o.pack_error_no_exit
            if DEBUG:
                ie=False
            if this_error_count>2:
                ie=True
                print("单个处理列表错误次数过多，强制进行关闭")
            if ie:
                sys.exit(1)

def print_rq(rq):# 打印人气值
    hp=fahp(rq)
    txt=str(hp)
    if DEBUG:
        txt+=" "+str(rq)
    if hp==1:
        txt+=" (未开播或不显示)"
    print("[人气]",txt)

async def bililivemsg(url,roomid,o,token,uid):
    """使用提供的参数连接直播间"""
    global hpst
    if DEBUG:
        print("连接服务器…")
    if o.sessdata and not uid:
        print("提示: 使用了sessdata但未提供uid")
    async with websockets.connect(url,user_agent_header=UA)as ws:
        if DEBUG:
            print("服务器已连接")
        await ws.send(joinroom(roomid,token,uid))
        hpst=asyncio.create_task(hps(ws),name="重复发送心跳包")
        async for msg in ws:
            if msg[7]==1 and msg[11]==3:
                print_rq(msg[16:20])
            elif msg[7]==1 and msg[11]==8:
                print("[认证]",msg[16:])
            elif msg[7]==0:
                pacs(femsgd(msg),o)
            elif msg[7]==2:
                pacs(femsgd(zlib.decompress(msg[16:])),o)
            elif msg[7]==3:
                if brotli:
                    pacs(femsgd(brotli.decompress(msg[16:])),o)
                elif o.no_print_enable:
                    print("[支持] 未安装brotli，无法处理相关数据，请尝试使用其它协议版本。（正常情况下程序会自动切换协议版本，不过由于设备限制，相关代码未测试）")
            else:
                if o.no_print_enable:
                    continue
                print("[支持] 未知的协议版本")
                if DEBUG:
                    print(msg)

def start(roomid,o):
    """程序入口"""
    if DEBUG:
        print("获取直播信息流地址…")
    try:
        r=requests.get(
            "https://api.live.bilibili.com/xlive/web-room/v1/index/getDanmuInfo?id="+str(roomid),
            headers={
                "Origin":"https://live.bilibili.com/",
                "User-Agent":UA
            },
            cookies={
                "SESSDATA":o.sessdata
            }
        )
    except KeyboardInterrupt:
        print("获取信息操作被中断")
    except:
        print("获取信息流地址失败:",sys.exc_info()[1])
        error()
    else:
        if r.status_code!=200:
            print("数据获取失败")
            print("HTTP",r.status_code)
            save_http_error(r,"状态码不为200")
            sys.exit(1)
        d=r.json()
        if d["code"]!=0:
            print("获取信息流地址时code不为0")
            print(d["code"],"-",d["message"])
            save_http_error(r,"获取的code不为0")
            sys.exit(1)
        u=d["data"]["host_list"][0]
        ws_host=f"{u['host']}:{u['wss_port']}"
        try:
            asyncio.run(bililivemsg(f"wss://{ws_host}/sub",roomid,o,d["data"]["token"],o.uid))
        except websockets.exceptions.ConnectionClosedError as e:
            error()
            print("连接关闭:",e)
            if o.sessdata and time.time()-starttime<30:
                print("检测到使用了会话SESSDATA信息，请检查相关参数的正确性和有效性。")
            sys.exit(1)
        except websockets.exceptions.InvalidMessage as e:
            error()
            print("信息错误:",e)
            sys.exit(1)
        except TimeoutError:
            error()
            print("内部超时")
            print("请检查网络是否通畅。")
            sys.exit(errno.ETIMEDOUT)
        except OSError:
            error()
            print("出现OS异常，详细信息请查看错误记录文件。")
            print("可以先检查一下网络。大部分异常都由网络问题引起的。")
            sys.exit(1)
        except Exception:
            error("捕捉函数 bililivemsg 抛出的异常\n"f"WebSocket Server: {ws_host}"f"\nroomid: {roomid}\ntoken: {d['data']['token']}")
            print("=出现内部异常=\n请查看错误记录文件自行排除问题或在你获取本文件的git仓库开一个issue。")
            print("开issus请检查是否有相同的问题，若有就附加上去。记得附上错误文件，也不要忘记检查是否有敏感信息。")
            print("若使用登录信息，请将错误文件中命令行选项内的sessdata替换为'SESSDATA'字符串，切勿改成None，否则无法确定是否为登录时发生的问题。")
            print("uid也不要替换为0，随便一个正数。如果uid为0，这边会更偏向于没有正确使用参数导致出现问题。")
            sys.exit(1)

def set_wslog():
    import logging.handlers
    rp=Path("bili_live_ws_log")
    if not rp.is_dir():
        rp.mkdir()
    h=logging.handlers.RotatingFileHandler(rp/"ws.log",maxBytes=1024*1024*2,backupCount=6)
    h.setLevel(logging.DEBUG)
    h.setFormatter(logging.Formatter("{asctime} {levelname}: {message}",style="{"))
    wslog.addHandler(h)
    print("已启用ws记录")

def shielding_words(f):
    """屏蔽词"""
    print("解析屏蔽词…")
    try:
        for l in f:
            t=l.rstrip("\r\n")
            if t:
                if t[0]=="#":
                    continue
                swd.append(t)
    except:
        print("处理屏蔽词时出现错误",file=sys.stderr)
        error()
    finally:
        f.close()
        if DEBUG:
            print(swd)
def blocking_rules(f):
    """屏蔽规则"""
    print("解析屏蔽规则…")
    try:
        for l in f:
            t=l.rstrip("\r\n")
            if t:
                if t[0]=="#":
                    continue
                brs.append(re.compile(t))
    except:
        print("处理屏蔽规则时出现错误",file=sys.stderr)
        error()
    finally:
        f.close()
        if DEBUG:
            print(brs)

def print_test_pack_count():
    # 打印数据包计数
    if len(test_pack_count)==0:
        print("无内容")
    for k,v in test_pack_count.items():
        print("cmd",k,"计数",v)

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
    mt=d["msg_type"]
    if mt==1:
        if not o.no_enter_room:
            print(info,d["uname"],"进入直播间",sep=" ")
    elif mt==2:
        print(info,d["uname"],"关注直播间",sep=" ")
    elif mt==3:
        print(info,d["uname"],"分享直播间",sep=" ")
    else:
        if not o.no_print_enable:
            print("[支持]","未知的交互类型:",d["msg_type"])
        raise SavePack("未知的交换类型")
def l_entry_effect(d):
    print("[进场]",d["copy_writing"])
def l_send_gift(d):
    print("[礼物]",d["uname"],d["action"],d["giftName"],"*",d["num"],sep=" ")
def l_combo_send(d):
    print("[礼物]",d["uname"],d["action"],d["gift_name"],"*",d["total_num"],sep=" ")
def l_watched_change(d):
    if DEBUG:
        print("[观看]",d["num"],"人看过;","text_large:",d["text_large"])
    else:
        print("[观看]",d["num"],"人看过")
def l_super_chat_message(d):
    print("[留言]",f"{d['user_info']['uname']}(￥{d['price']}):",d["message"])
def l_super_chat_message_delete(d):
    print("[留言]","醒目留言删除:",d["data"]["ids"])
def l_live_interactive_game(d):
    if d["msg"]in swd:
        return
    for b in brs:
        if b.search(d["msg"]):
            return
    print("[弹幕](LIG)",f"{d['uname']}:",d["msg"])
def l_room_real_time_message_update(d):
    print("[信息]",d["roomid"],"直播间",d["fans"],"粉丝",sep=" ")
def l_stop_live_room_list(d):
    print("[停播]","停止直播的房间列表:",f"len({len(d['room_id_list'])})")
def l_hot_rank_changed(d):
    print("[排行]",d["area_name"],"第",d["rank"],"名")
def l_online_rank_count(d):
    olc=""
    if "online_count"in d:
        olc="在线计数: "+str(d["online_count"])
    print("[计数]","高能用户计数:",d["count"],olc)
def l_voice_join_list(d):
    print("[连麦]","申请计数:",d["apply_count"])
def l_online_rank_top3(d):
    if DEBUG:
        print("[排行]",f"len({len(d['list'])})",d["list"][0]["msg"],f"rank:{d['list'][0]['rank']}")
    else:
        print("[排行]",d["list"][0]["msg"],f"rank:{d['list'][0]['rank']}")
def l_voice_join_status(d):
    if d["status"]==0:
        print("[连麦]","停止连麦")
    elif d["status"]==1:
        print("[连麦]","正在与",d["user_name"],"连麦")
    else:
        raise SavePack("未知状态")
def l_online_rank_v2(d,npe):
    rt=d["rank_type"]
    if rt=="gold-rank":
        print("[排行]","高能用户部分列表(gr):",f"len({len(d['list'])})")
    elif rt=="online_rank":
        print("[排行]","高能用户部分列表:",f"len({len(d['online_list'])})")
    else:
        if not npe:
            print("[支持]","未知的排行类型:",d["rank_type"])
        raise SavePack("未知的排行类型")
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
        if d["widget_list"][wi]is None:
            continue
        print("[小部件]",f"key:{wi}","id",d["widget_list"][wi]["id"],"标题:",d["widget_list"][wi]["title"])
def l_super_chat_entrance(d):
    if d["status"]==0:
        print("[信息]","关闭醒目留言入口")
    else:
        print("[支持]","未知的'SUPER_CHAT_ENTRANCE'status数字:",d["status"])
        print("因为样本稀少，暂不提供屏蔽该不支持信息")
        raise SavePack("未知的status")
def l_room_skin_msg(d):
    print("[信息]","直播间皮肤更新","id:",d["skin_id"],",status:",d["status"],",结束时间:",time.strftime(TIMEFORMAT,time.gmtime(d["end_time"])),",当前时间:",time.strftime(TIMEFORMAT,time.gmtime(d["current_time"])),sep=" ")
def l_popularity_red_pocket_new(d):
    print("[通知]",d["uname"],d["action"],"价值",d["price"],"电池的",d["gift_name"],sep=" ")
def l_popularity_red_pocket_start(d):
    if d["danmu"]not in swd:
        swd.append(d["danmu"])
        print("[屏蔽]","屏蔽词增加:",d["danmu"])
def l_like_info_v3_click(d):
    print("[交互]",d["uname"],d["like_text"])
def l_popular_rank_changed(d):
    print("[排行]","人气榜第",d["rank"],"名")
def l_area_rank_changed(d):
    print("[排行]",d["rank_name"],"第",d["rank"],"名")
def l_dm_interaction(d):
    n=json.loads(d["data"])
    for c in n["combo"]:
        print("[弹幕合并]",c["guide"],c["content"],"×"+str(c["cnt"]))
def l_pk_battle_pre(d):
    print("[PK]","PK即将开始",f"id:{d['pk_id']}",f"s:{d['pk_status']}","对方直播间",d["data"]["room_id"],"昵称:",d["data"]["uname"])
def l_pk_battle_start(d):
    a=d["data"]
    print("[PK]","PK开始",f"id:{d['pk_id']}",f"s:{d['pk_status']}","计数名称:",a["pk_votes_name"],f"增量:{a['pk_votes_add']}")
def l_pk_battle_process(d):
    a=d["data"]
    i=a["init_info"]
    m=a["match_info"]
    print("[PK]","计数更新",f"id:{d['pk_id']}",f"s:{d['pk_status']}","直播间",i["room_id"],"已有",i["votes"],"票，直播间",m["room_id"],"已有",m["votes"],"票")
def l_pk_battle_final_process(d):
    print("[PK]","PK结束流程变化",f"id:{d['pk_id']}",f"s:{d['pk_status']}")
def l_pk_battle_end(d):
    a=d["data"]
    i=a["init_info"]
    m=a["match_info"]
    print("[PK]","PK结束",f"id:{d['pk_id']}",f"s:{d['pk_status']}","直播间",i["room_id"],"已有",i["votes"],"票，直播间",m["room_id"],"已有",m["votes"],"票")
def l_pk_battle_settle_v2(d):
    a=d["data"]
    print("[PK]","PK结算",f"id:{d['pk_id']}",f"s:{d['pk_status']}","主播获得",a["result_info"]["pk_votes"],a["result_info"]["pk_votes_name"])
def l_recommend_card(d,s):
    print("[广告]","推荐卡片","推荐数量:",len(d["recommend_list"]),"更新数量:",len(d["update_list"]))
    if s:
        raise SavePack("保存推荐卡片")
def l_goto_buy_flow(d):
    print("[广告]",d["text"])
def l_anchor_lot_checkstatus(d):
    print("[天选时刻]","状态更新",f"id:{d['id']},status:{d['status']},uid:{d['uid']}",f"reject_danmu:{repr(d['reject_danmu'])} reject_reason:{repr(d['reject_reason'])}")
def l_anchor_lot_start(d):
    print("[天选时刻]",d["award_name"],f"{d['award_num']}人",f'''发送"{d['danmu']}"参与,需要"{d['require_text']}"''',f"id:{d['id']}",f"最大时间{d['max_time']}秒,剩余{d['time']}秒")
def l_anchor_lot_award(d):
    print("[天选时刻]",d["award_name"],f"{d['award_num']}人","已开奖",f"id:{d['id']}",f"中奖用户数量{len(d['award_users'])}")
# 命令处理调用处(结束)

def get_SESSDATA(s):# 获取登录会话标识
    print("警告: 错误记录文件会自动记录命令行参数，其中有SESSDATA数据。")
    p=Path(s)
    if p.is_file():
        if p.stat().st_size>65536:
            print("[错误] 会话文件过大")
            raise ValueError("file large")
        return p.read_text().splitlines()[0].split("\t")[-1]
    return s

def pararg():
    import argparse
    global DEBUG
    global runoptions
    if runoptions:
        raise RuntimeError("检测到已进行过一次命令行参数获取")
    desc="哔哩哔哩直播信息流处理\n允许使用@来引入参数文件"
    parser=argparse.ArgumentParser(usage="%(prog)s [options] roomid",description=desc,formatter_class=argparse.RawDescriptionHelpFormatter,fromfile_prefix_chars="@")
    parser.add_argument("roomid",help="直播间ID",type=int,default=23058)
    parser.add_argument("-d","--debug",help="开启调试模式",action="store_true")
    parser.add_argument("--no-print-enable",help="不打印不支持的信息",action="store_true")
    parser.add_argument("-u","--save-unknow-datapack",help="保存未知的数据包",action="store_true")
    parser.add_argument("--pack-error-no-exit",help="数据包处理异常时不退出",action="store_false")
    parser.add_argument("--sessdata",help="使用登录会话标识",type=get_SESSDATA,metavar="SESSDATA|FILE")
    parser.add_argument("--uid",help="用户UID，使用SESSDATA时必须",type=int,default=0)
    # 关闭一个或多个cmd显示
    cmd=parser.add_argument_group("关闭某个cmd的显示")
    cmd.add_argument("--no-interact-word",help="关闭直播间交互信息",action="store_true")
    cmd.add_argument("--no-entry-effect",help="关闭进场信息",action="store_true")
    cmd.add_argument("--no-send-gift",help="关闭礼物信息",action="store_true")
    cmd.add_argument("--no-combo-send",help="关闭组合礼物信息",action="store_true")
    cmd.add_argument("--no-watched-change",help="关闭看过信息",action="store_true")
    cmd.add_argument("--no-super-chat-message",help="关闭醒目留言信息",action="store_true")
    cmd.add_argument("--no-live-interactive-game",help="关闭特殊数据格式弹幕",action="store_true")
    cmd.add_argument("--no-stop-live-room-list",help="关闭停止直播的房间列表信息",action="store_true")
    cmd.add_argument("--no-hot-rank-changed",help="关闭当前直播间的排行信息",action="store_true")
    cmd.add_argument("--no-online-rank-count",help="关闭高能用户计数信息",action="store_true")
    cmd.add_argument("--no-voice-join-list",help="关闭连麦列表信息",action="store_true")
    cmd.add_argument("--no-online-rank-top3",help="关闭前三个第一次成为高能用户信息",action="store_true")
    cmd.add_argument("--no-voice-join-status",help="关闭连麦状态信息",action="store_true")
    cmd.add_argument("--no-online-rank-v2",help="关闭高能用户列表信息(暂定)",action="store_true")
    cmd.add_argument("--no-hot-rank-settlement",help="关闭热门通知信息",action="store_true")
    cmd.add_argument("--no-common-notice-danmaku",help="关闭普通通知信息",action="store_true")
    cmd.add_argument("--no-notice-msg",help="关闭公告信息",action="store_true")
    cmd.add_argument("--no-guard-buy",help="关闭购买舰队信息",action="store_true")
    cmd.add_argument("--no-user-toast-msg",help="关闭续费舰队信息",action="store_true")
    cmd.add_argument("--no-widget-banner",help="关闭小部件信息",action="store_true")
    cmd.add_argument("--no-super-chat-entrance",help="关醒目留言入口信息",action="store_true")
    cmd.add_argument("--no-enter-room",help="关闭进入直播间信息",action="store_true")
    cmd.add_argument("--no-popularity-red-pocket-new",help="关闭新红包(?)信息",action="store_true")
    cmd.add_argument("--no-like-info-update",help="关闭点赞计数信息",action="store_true")
    cmd.add_argument("--no-popular-rank-changed",help="关闭人气排行更新",action="store_true")
    cmd.add_argument("--no-area-rank-changed",help="关闭大航海排行更新",action="store_true")
    cmd.add_argument("--no-dm-interaction",help="关闭弹幕合并信息",action="store_true")
    cmd.add_argument("--no-pk-message",help="关闭全部PK信息",action="store_true")
    cmd.add_argument("--no-pk-battle-process",help="关闭PK过程信息",action="store_true")
    cmd.add_argument("--no-recommend-card",help="关闭推荐卡片信息",action="store_true")
    cmd.add_argument("--save-recommend-card",help="保存推荐卡片信息(调试)",action="store_true")
    cmd.add_argument("--no-goto-buy-flow",help="关闭购买推荐商品信息",action="store_true")
    cmd.add_argument("--no-anchor-lot",help="关闭天选时刻信息",action="store_true")
    # 附加功能
    parser.add_argument("-S","--shielding-words",help="屏蔽词(完全匹配)",type=argparse.FileType("rt"),metavar="FILE")
    parser.add_argument("-B","--blocking-rules",help="屏蔽规则",type=argparse.FileType("rt"),metavar="FILE")
    parser.add_argument("--print-pack-count",help="打印数据包计数",action="store_true")
    args=parser.parse_args()
    runoptions=args
    DEBUG=DEBUG or args.debug
    return args

def main():
    args=pararg()
    if DEBUG:
        print("版本信息:",VERSIONINFO)
        print("命令行选项:",args)
        set_wslog()
    roomid=args.roomid
    print("直播间ID:",roomid)
    if args.shielding_words:
        shielding_words(args.shielding_words)
    if args.blocking_rules:
        blocking_rules(args.blocking_rules)
    print("连接直播间…")
    try:
        start(roomid,args)
    except KeyboardInterrupt:
        print("关闭连接")
        if DEBUG or args.print_pack_count:
            print("被测试的cmd计数:")
            print_test_pack_count()
        sys.exit(0)
if __name__=="__main__":
    print("=[哔哩哔哩直播信息流]=")
    main()

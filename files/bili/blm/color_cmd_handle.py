"""额外的命令处理
由bili_live_ws.py的命令处理调用处派生而来
进行额外的上色，仅适用于shell"""

import re,json,time
from __main__ import DEBUG,TIMEFORMAT,swd,brs,SavePack

def cbt(n):# 生成颜色操作
    return f"\33[{n}m"
def cfc(n):# 生成前景颜色
    return f"\33[38;5;{n}m"
def cfb(n):#生成背景颜色
    return f"\33[48;5;{n}m"
DF=cbt(0)# 重置全部
DB=cbt(1)# 加粗
DD=cbt(2)# 变暗
DI=cbt(3)# 斜体
DU=cbt(4)# 下划线
DC=cbt(5)# 闪烁
# 重置
EB=cbt(21)# 加粗
ED=cbt(22)# 变暗
EI=cbt(23)# 斜体
EU=cbt(24)# 下划线
EC=cbt(25)# 闪烁
# 字体颜色
CD=cbt(39)# 默认
C_00=cbt(30)# 黑
C_01=cbt(31)# 红
C_02=cbt(32)# 绿
C_03=cbt(33)# 黄
C_04=cbt(34)# 蓝
C_05=cbt(35)# 品红
C_06=cbt(36)# 青
C_07=cbt(37)# 浅灰
C_10=cbt(90)# 深灰
C_11=cbt(91)# 亮红
C_12=cbt(92)# 亮绿
C_13=cbt(93)# 亮黄
C_14=cbt(94)# 浅蓝
C_15=cbt(95)# 浅品红
C_16=cbt(96)# 亮青
C_17=cbt(97)# 白
# 背景颜色
BD=cbt(49)# 默认
B_00=cbt(40)# 黑
B_01=cbt(41)# 红
B_02=cbt(42)# 绿
B_03=cbt(43)# 黄
B_04=cbt(44)# 蓝
B_05=cbt(45)# 品红
B_06=cbt(46)# 青
B_07=cbt(47)# 浅灰
B_10=cbt(100)# 深灰
B_11=cbt(101)# 亮红
B_12=cbt(102)# 亮绿
B_13=cbt(103)# 亮黄
B_14=cbt(104)# 浅蓝
B_15=cbt(105)# 浅品红
B_16=cbt(106)# 亮青
B_17=cbt(107)# 白

# 对某种情况统一使用的颜色,命名规则: "T"+标记
TRTG=C_04# 最前面的那个[]的颜色
TUSR=C_03# 用户名
TNUM=C_06# 数字、数量
TRMI=C_14# 房间号

# 正则表达式
USER=re.compile("<%(.+?)%>")

def cuse(m):# 渲染用户颜色
    return USER.sub(TUSR+"\\1"+CD,m)

def p(n:str,*d,**t)->None:
    print(f"{TRTG}{DB}[{n}]{DF}",*d,DF,**t)

def l_danmu_msg(d):# 弹幕
    if d[1]in swd:
        return
    for b in brs:
        if b.search(d[1]):
            return
    tc=""
    if d[2][2]==1:
        tc+=f"{C_13}(房管){CD}"
    # tc+=f"{C_01}(主播){CD}"
    p("弹幕",f"{tc}{TUSR}{d[2][1]}{CD}:{C_07}",d[1])
def l_interact_word(d,o):# 交互
    info="交互"
    mt=d["msg_type"]
    nm=f"{TUSR}{d['uname']}{CD}"
    if mt==1:
        if not o.no_enter_room:
            p(info,nm,"进入直播间")
    elif mt==2:
        p(info,nm,"关注直播间")
    elif mt==3:
        p(info,nm,"分享直播间")
    else:
        if not o.no_print_enable:
            p("支持","未知的交互类型:",d["msg_type"])
        raise SavePack("未知的交换类型")
def l_entry_effect(d):# 进场
    p("进场",cuse(d["copy_writing"]))
def l_send_gift(d):# 礼物
    p("礼物",f'{TUSR}{d["uname"]}{CD}',d["action"],d["giftName"],TNUM+"×",d["num"])
def l_combo_send(d):# 组合礼物
    p("礼物",f'{TUSR}{d["uname"]}{CD}',d["action"],d["gift_name"],TNUM+"×",d["total_num"])
def l_watched_change(d):# 看过
    if DEBUG:
        p("观看",f"{TNUM}{d['num']}{CD} 人看过;","text_large:",d["text_large"])
    else:
        p("观看",f"{TNUM}{d['num']}{CD} 人看过")
def l_super_chat_message(d):# 醒目留言
    p("留言",f"{TUSR}{d['user_info']['uname']}{CD}({C_11}￥{d['price']}{CD}):{C_07}",d["message"])
def l_super_chat_message_delete(d):# 醒目留言删除
    p("留言","醒目留言删除:",d["data"]["ids"])
def l_live_interactive_game(d):# 某种相同弹幕
    if d["msg"]in swd:
        return
    for b in brs:
        if b.search(d["msg"]):
            return
    p("弹幕(LIG)",f"{TUSR}{d['uname']}{CD}:{C_10}",d["msg"])
def l_room_change(d):# 直播间更新
    print(f"{B_05}{TRTG}[直播]{CD} 分区:{C_06} {d['parent_area_name']} {C_02}>{C_06} {d['area_name']} {CD}标题: {C_06}{d['title']}{DF}")
def l_live(p):# 开始直播
    print(f"{B_05}{TRTG}[直播]{CD} 直播间 {TRMI}{p['roomid']}{CD} 开始直播{DF}")
def l_preparing(p):# 结束直播
    print(f"{B_05}{TRTG}[直播]{CD} 直播间 {TRMI}{p['roomid']}{CD} 结束直播{DF}")
def l_room_real_time_message_update(d):# 数据更新
    p("信息",f"{TRMI}{d['roomid']}{CD} 直播间 {TNUM}{d['fans']}{CD} 粉丝")
def l_stop_live_room_list(d):# 停止直播的房间列表
    p("停播","停止直播的房间列表:",f"len({len(d['room_id_list'])})")
def l_room_block_msg(p):# 用户被禁言
    p("直播","用户"+TUSR,p["uname"],CD+"已被禁言")
def l_cut_off(p):# 警告
    p("直播","直播间"+TRMI,p["room_id"],CD+"被警告:"+B_01,p["msg"])
def l_room_lock(p):# 封禁
    p("直播","直播间"+TRMI,p["roomid"],CD+"被封禁，解除时间:",p["expire"])
def l_room_admins(p):# 房管列表
    p("直播",f"房管列表: len({len(p['uids'])})")
def l_hot_rank_changed(d):
    p("排行",d["area_name"],"第"+TNUM,d["rank"],CD+"名")
def l_online_rank_count(d):# 在线计数
    olc=""
    if "online_count"in d:
        olc=CD+"在线计数: "+TNUM+str(d["online_count"])
    p("计数","高能用户计数:"+TNUM,d["count"],olc)
def l_little_tips(d):# 小提示
    p("提示",f"{C_15}{d['msg']}")
def l_little_message_box(d):# 弹框提示
    p("弹框",f"{B_04}{C_17}{d['msg']}{BD}")
def l_voice_join_list(d):# 连麦列表
    p("连麦","申请计数:"+TNUM,d["apply_count"])
def l_online_rank_top3(d):# 前三个第一次成为高能用户
    ts=d["list"][0]
    if DEBUG:
        p("排行",f"len({len(d['list'])}) {cuse(ts['msg'])} rank:{ts['rank']}")
    else:
        p("排行",f"{cuse(ts['msg'])} rank:{TNUM}{ts['rank']}")
def l_voice_join_status(d):# 连麦状态
    if d["status"]==0:
        p("连麦","停止连麦")
    elif d["status"]==1:
        p("连麦","正在与"+TUSR,d["user_name"],CD+"连麦")
    else:
        raise SavePack("未知状态")
def l_online_rank_v2(d,npe):
    rt=d["rank_type"]
    if rt=="gold-rank":
        p("排行","高能用户部分列表(gr):",f"len({len(d['list'])})")
    elif rt=="online_rank":
        p("排行","高能用户部分列表:",f"len({len(d['online_list'])})")
    else:
        if not npe:
            p("支持","未知的排行类型:",d["rank_type"])
        raise SavePack("未知的排行类型")
def l_hot_rank_settlement(d):
    p("排行",d["dm_msg"])
def l_common_notice_danmaku(d):# 通知
    for cse in d["content_segments"]:
        cset=cse["type"]
        if cset==1:
            p("通知",cse["text"])
        elif cset==2:
            p("通知","图片:",f"{DU}{cse.get('img_url')}")
def l_notice_msg(d):# 公告(广播)
    msg=d["msg_self"]
    msg=cuse(msg)
    if "name"in d:
        p("公告",d["name"],C_04+"=>"+CD,msg)
    else:
        p("公告",msg)
def l_guard_buy(d):# 舰队购买
    p("礼物",d["username"],"购买了",d["num"],"个",d["gift_name"])
def l_user_toast_msg(d):# 舰队续费
    p("提示",d["toast_msg"])
def l_widget_banner(d):# 小部件
    for wi in d["widget_list"]:
        if d["widget_list"][wi]is None:
            continue
        p("小部件",f"key:{wi}","id",d["widget_list"][wi]["id"],"标题:",d["widget_list"][wi]["title"])
def l_super_chat_entrance(d):# 醒目留言入口变化
    if d["status"]==0:
        p("信息","关闭醒目留言入口")
    else:
        p("支持","未知的'SUPER_CHAT_ENTRANCE'status数字:",d["status"])
        print(DB+DI+"因为样本稀少，暂不提供屏蔽该不支持信息"+DF)
        raise SavePack("未知的status")
def l_room_skin_msg(d):# 直播间皮肤更新
    p("信息","直播间皮肤更新","id:",d["skin_id"],",status:",d["status"],",结束时间:",time.strftime(TIMEFORMAT,time.gmtime(d["end_time"])),",当前时间:",time.strftime(TIMEFORMAT,time.gmtime(d["current_time"])))
def l_live_multi_view_change(d):
    p("信息","LIVE_MULTI_VIEW_CHANGE",d)
def l_popularity_red_pocket_new(d):
    p("通知",d["uname"],d["action"],"价值",d["price"],"电池的",d["gift_name"])
def l_popularity_red_pocket_start(d):
    if d["danmu"]not in swd:
        swd.append(d["danmu"])
        p("屏蔽","屏蔽词增加:",d["danmu"])
def l_like_info_v3_update(d):# 点赞数量
    p("计数","点赞点击数量:"+TNUM,d["click_count"])
def l_like_info_v3_click(d):# 点赞点击
    p("交互",f"{TUSR}{d['uname']}{CD} {d['like_text']}")
def l_popular_rank_changed(d):# 人气排行更新
    p("排行","人气榜第"+TNUM,d["rank"],CD+"名")
def l_area_rank_changed(d):# 大航海排行更新
    p("排行",d["rank_name"],"第"+TNUM,d["rank"],CD+"名")
def l_dm_interaction(d):# 弹幕合并
    n=json.loads(d["data"])
    for c in n["combo"]:
        p("弹幕合并",f"{C_10}{c['guide']}",c["content"],TNUM+"×"+str(c["cnt"]))
def l_pk_battle_pre(d):# PK即将开始
    p("PK","PK即将开始",f"id:{d['pk_id']}",f"s:{d['pk_status']}",f"对方直播间 {TRMI}{d['data']['room_id']}{CD}","昵称:"+TUSR,d["data"]["uname"])
def l_pk_battle_start(d):# PK开始
    a=d["data"]
    p("PK","PK开始",f"id:{d['pk_id']}",f"s:{d['pk_status']}","计数名称:",a["pk_votes_name"],f"增量:{a['pk_votes_add']}")
def l_pk_battle_process(d):# PK过程
    a=d["data"]
    i=a["init_info"]
    m=a["match_info"]
    p("PK","计数更新",f"id:{d['pk_id']}",f"s:{d['pk_status']}",f"直播间{TRMI}{i['room_id']}{CD}已有{TNUM}{i['votes']}{CD}票，直播间{TRMI}{m['room_id']}{CD}已有{TNUM}{m['votes']}{CD}票")
def l_pk_battle_final_process(d):# PK结束流程变化
    p("PK","PK结束流程变化",f"id:{d['pk_id']}",f"s:{d['pk_status']}")
def l_pk_battle_end(d):# PK结束
    a=d["data"]
    i=a["init_info"]
    m=a["match_info"]
    p("PK","PK结束",f"id:{d['pk_id']}",f"s:{d['pk_status']}",f"直播间{TRMI}{i['room_id']}{CD}已有{TNUM}{i['votes']}{CD}票，直播间{TRIM}{m['room_id']}{CD}已有{TNUM}{m['votes']}{CD}票")
def l_pk_battle_settle_v2(d):# PK结算2
    a=d["data"]
    p("PK","PK结算",f"id:{d['pk_id']}",f"s:{d['pk_status']}","主播获得",a["result_info"]["pk_votes"],a["result_info"]["pk_votes_name"])
def l_recommend_card(d,s):# 推荐卡片
    p("广告","推荐卡片","推荐数量:",len(d["recommend_list"]),"更新数量:",len(d["update_list"]))
    if s:
        raise SavePack("保存推荐卡片")
def l_goto_buy_flow(d):# 购买推荐
    p("广告",d["text"])
def l_log_in_notice(d):# 登录通知
    print(f"{B_02}{TRTG}[需要登录]{CD}",d["notice_msg"],DF)
def l_anchor_lot_checkstatus(d):# 天选时刻审核状态
    p("天选时刻","状态更新",f"id:{d['id']},status:{d['status']},uid:{d['uid']}",f"reject_danmu:{repr(d['reject_danmu'])} reject_reason:{repr(d['reject_reason'])}")
def l_anchor_lot_start(d):# 天选时刻开始
    p("天选时刻",d["award_name"],f"{TNUM}{d['award_num']}{CD}人",f'''发送{C_07}"{d['danmu']}"{CD}参与,需要"{d['require_text']}"''',f"id:{d['id']}",f"最大时间{TNUM}{d['max_time']}{CD}秒,剩余{TNUM}{d['time']}{CD}秒")
def l_anchor_lot_end(d):# 天选时刻结束
    p("天选时刻","id为",d["id"],"的天选时刻已结束")
def l_anchor_lot_award(d):# 天选时刻开奖
    p("天选时刻",d["award_name"],f"{d['award_num']}人","已开奖",f"id:{d['id']}",f"中奖用户数量{len(d['award_users'])}")

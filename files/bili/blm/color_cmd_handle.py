"""额外的命令处理
由bili_live_ws.py的命令处理调用处派生而来
进行额外的上色，仅适用于shell"""

import re,json
from __main__ import DEBUG,swd,brs,SavePack

def cbt(n):# 生成颜色操作
    return f"\33[{n}m"
DF=cbt(0)# 重置
DB=cbt(1)# 加粗
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

# 正则表达式
USER=re.compile("<%(.+?)%>")

def p(n:str,*d,**t)->None:
    print(f"\33[34m\33[1m[{n}]\33[0m",*d,"\33[0m",**t)

def l_danmu_msg(d):
    if d[1]in swd:
        return
    for b in brs:
        if b.search(d[1]):
            return
    p("弹幕",f"{C_03}{d[2][1]}{CD}:",d[1])
def l_interact_word(d,o):
    info="交互"
    mt=d["msg_type"]
    nm=f"{C_03}{d['uname']}{CD}"
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
def l_entry_effect(d):
    p("进场",USER.sub(C_03+"\\1"+CD,d["copy_writing"]))
def l_send_gift(d):
    p("礼物",f'{C_03}{d["uname"]}{CD}',d["action"],d["giftName"],C_06+"×",d["num"])
def l_combo_send(d):
    p("礼物",f'{C_03}{d["uname"]}{CD}',d["action"],d["gift_name"],C_06+"×",d["total_num"])
def l_watched_change(d):
    if DEBUG:
        p("观看",d["num"],"人看过;","text_large:",d["text_large"])
    else:
        p("观看",d["num"],"人看过")
def l_super_chat_message(d):
    p("留言",f"{C_03}{d['user_info']['uname']}{CD}(￥{d['price']}):",d["message"])
def l_super_chat_message_delete(d):
    p("留言","醒目留言删除:",d["data"]["ids"])
def l_live_interactive_game(d):
    if d["msg"]in swd:
        return
    for b in brs:
        if b.search(d["msg"]):
            return
    p("弹幕(LIG)",f"{C_03}{d['uname']}{CD}:",d["msg"])
def l_room_change(d):
    print(f"{B_05}{C_04}[直播]{CD} 分区:{C_06} {d['parent_area_name']} {C_02}>{C_06} {d['area_name']} {CD}标题: {C_06}{d['title']}{DF}")
def l_live(p):
    print(f"{B_05}{C_04}[直播]{CD} 直播间 {p['roomid']} 开始直播{DF}")
def l_preparing(p):
    print(f"{B_05}{C_04}[直播]{CD} 直播间 {p['roomid']} 结束直播{DF}")
def l_room_real_time_message_update(d):
    p("信息",d["roomid"],"直播间",d["fans"],"粉丝")
def l_stop_live_room_list(d):
    p("停播","停止直播的房间列表:",f"len({len(d['room_id_list'])})")
def l_room_block_msg(p):
    p("直播","用户"+C_03,p["uname"],CD+"已被禁言")
def l_cut_off(p):
    p("直播","直播间",p["room_id"],"被警告:",p["msg"])
def l_room_lock(p):
    p("直播","直播间",p["roomid"],"被封禁，解除时间:",p["expire"])
def l_hot_rank_changed(d):
    p("排行",d["area_name"],"第",d["rank"],"名")
def l_online_rank_count(d):
    olc=""
    if "online_count"in d:
        olc="在线计数: "+str(d["online_count"])
    p("计数","高能用户计数:",d["count"],olc)
def l_voice_join_list(d):
    p("连麦","申请计数:",d["apply_count"])
def l_online_rank_top3(d):
    if DEBUG:
        p("排行",f"len({len(d['list'])})",d["list"][0]["msg"],f"rank:{d['list'][0]['rank']}")
    else:
        p("排行",d["list"][0]["msg"],f"rank:{d['list'][0]['rank']}")
def l_voice_join_status(d):
    if d["status"]==0:
        p("连麦","停止连麦")
    elif d["status"]==1:
        p("连麦","正在与"+C_03,d["user_name"],CD+"连麦")
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
def l_common_notice_danmaku(d):
    for cse in d["content_segments"]:
        p("通知",cse["text"])
def l_notice_msg(d):
    msg=d["msg_self"]
    if not isinstance(msg,str):raise SavePack("类型错误")
    msg=USER.sub(C_03+r"\1"+CD,msg)
    if "name"in d:
        p("公告",d["name"],"=>",msg)
    else:
        p("公告",msg)
def l_guard_buy(d):
    p("礼物",d["username"],"购买了",d["num"],"个",d["gift_name"])
def l_user_toast_msg(d):
    p("提示",d["toast_msg"])
def l_widget_banner(d):
    for wi in d["widget_list"]:
        if d["widget_list"][wi]is None:
            continue
        p("小部件",f"key:{wi}","id",d["widget_list"][wi]["id"],"标题:",d["widget_list"][wi]["title"])
def l_super_chat_entrance(d):
    if d["status"]==0:
        p("信息","关闭醒目留言入口")
    else:
        p("支持","未知的'SUPER_CHAT_ENTRANCE'status数字:",d["status"])
        print("因为样本稀少，暂不提供屏蔽该不支持信息")
        raise SavePack("未知的status")
def l_room_skin_msg(d):
    p("信息","直播间皮肤更新","id:",d["skin_id"],",status:",d["status"],",结束时间:",time.strftime(TIMEFORMAT,time.gmtime(d["end_time"])),",当前时间:",time.strftime(TIMEFORMAT,time.gmtime(d["current_time"])),sep=" ")
def l_live_multi_view_change(d):
    p("信息","LIVE_MULTI_VIEW_CHANGE",d)
def l_popularity_red_pocket_new(d):
    p("通知",d["uname"],d["action"],"价值",d["price"],"电池的",d["gift_name"],sep=" ")
def l_popularity_red_pocket_start(d):
    if d["danmu"]not in swd:
        swd.append(d["danmu"])
        p("屏蔽","屏蔽词增加:",d["danmu"])
def l_like_info_v3_update(d):
    p("计数","点赞点击数量:",d["click_count"])
def l_like_info_v3_click(d):
    p("交互",f"{C_03}{d['uname']}{CD} {d['like_text']}")
def l_popular_rank_changed(d):
    p("排行","人气榜第",d["rank"],"名")
def l_area_rank_changed(d):
    p("排行",d["rank_name"],"第",d["rank"],"名")
def l_dm_interaction(d):
    n=json.loads(d["data"])
    for c in n["combo"]:
        p("弹幕合并",f"{C_07}{c['guide']}",c["content"],C_06+"×"+str(c["cnt"]))
def l_pk_battle_pre(d):
    p("PK","PK即将开始",f"id:{d['pk_id']}",f"s:{d['pk_status']}","对方直播间",d["data"]["room_id"],"昵称:",d["data"]["uname"])
def l_pk_battle_start(d):
    a=d["data"]
    p("PK","PK开始",f"id:{d['pk_id']}",f"s:{d['pk_status']}","计数名称:",a["pk_votes_name"],f"增量:{a['pk_votes_add']}")
def l_pk_battle_process(d):
    a=d["data"]
    i=a["init_info"]
    m=a["match_info"]
    p("PK","计数更新",f"id:{d['pk_id']}",f"s:{d['pk_status']}","直播间",i["room_id"],"已有",i["votes"],"票，直播间",m["room_id"],"已有",m["votes"],"票")
def l_pk_battle_final_process(d):
    p("PK","PK结束流程变化",f"id:{d['pk_id']}",f"s:{d['pk_status']}")
def l_pk_battle_end(d):
    a=d["data"]
    i=a["init_info"]
    m=a["match_info"]
    p("PK","PK结束",f"id:{d['pk_id']}",f"s:{d['pk_status']}","直播间",i["room_id"],"已有",i["votes"],"票，直播间",m["room_id"],"已有",m["votes"],"票")
def l_pk_battle_settle_v2(d):
    a=d["data"]
    p("PK","PK结算",f"id:{d['pk_id']}",f"s:{d['pk_status']}","主播获得",a["result_info"]["pk_votes"],a["result_info"]["pk_votes_name"])
def l_recommend_card(d,s):
    p("广告","推荐卡片","推荐数量:",len(d["recommend_list"]),"更新数量:",len(d["update_list"]))
    if s:
        raise SavePack("保存推荐卡片")
def l_goto_buy_flow(d):
    p("广告",d["text"])
def l_log_in_notice(d):
    print(f"{B_02}{C_04}[需要登录]{CD}",d["notice_msg"],DF)
def l_anchor_lot_checkstatus(d):
    p("天选时刻","状态更新",f"id:{d['id']},status:{d['status']},uid:{d['uid']}",f"reject_danmu:{repr(d['reject_danmu'])} reject_reason:{repr(d['reject_reason'])}")
def l_anchor_lot_start(d):
    p("天选时刻",d["award_name"],f"{d['award_num']}人",f'''发送"{d['danmu']}"参与,需要"{d['require_text']}"''',f"id:{d['id']}",f"最大时间{d['max_time']}秒,剩余{d['time']}秒")
def l_anchor_lot_end(d):
    p("天选时刻","id为",d["id"],"的天选时刻已结束")
def l_anchor_lot_award(d):
    p("天选时刻",d["award_name"],f"{d['award_num']}人","已开奖",f"id:{d['id']}",f"中奖用户数量{len(d['award_users'])}")

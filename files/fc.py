#!/bin/python
"""文件校验 file_check
使用的哈希算法: SHA256
"""

import hashlib
import logging
import argparse
from pathlib import Path

pathinfo=str|Path

log=logging.getLogger("fc")
is_print_progress=False
GLOBAL_FILE_TOP="CHECK FILE"# 校验文件的头部
SCF_TNF="请检查要保存的校验文件的上级目录是否存在"
check_ok=[]
check_no=[]

def get_file_object_sha256(fb:"file object")->str:
    """获取文件对象的SHA256"""
    return hashlib.file_digest(fb,"sha256").hexdigest()

def get_file_sha256(filepath:pathinfo)->str|None:
    """获取文件的SHA256
返回值: SHA256字符串，不是文件时返回None"""
    fp=Path(filepath)
    if not fp.is_file():
        return None
    with fp.open("rb")as f:
        return get_file_object_sha256(f)

def check_file(filepath:pathinfo,checkdata:str)->bool|None:
    """校验文件"""
    h=get_file_sha256(filepath)
    if not isinstance(checkdata,str):
        return None
    if isinstance(h,str):
        return checkdata==h
    else:return h

def save_list_check_file(checkfilepath:pathinfo,iter:"可迭代对象")->str|None:
    """保存可迭代对象内容的校验文件"""
    cfp=Path(checkfilepath)
    ft=GLOBAL_FILE_TOP
    is_not_check_file=True
    try:
        with cfp.open("wt")as f:
            f.write(ft+"|list\n")
            for item in iter:
                fid=Path(item)
                if not fid.is_file():continue
                if is_print_progress:
                    print("保存",fid.name,"的校验值…")
                f.write(fid.name+"|"+get_file_sha256(fid)+"\n")
                log.debug(f"保存'{fid.name}'的校验值")
                is_not_check_file=False
    except(FileNotFoundError,NotADirectoryError):
        return SCF_TNF
    if is_not_check_file:
        return "警告: 检测到没有文件被获取"

def save_dir_check_file(cfp:pathinfo,dirpath:pathinfo,is_sort:bool=False)->str|None:
    """保存目录内文件的校验数据"""
    dp=Path(dirpath)
    if not dp.is_dir():
        return "不是目录"
    iter=dp.iterdir()
    if is_sort:
        iter=sorted(iter)
    return save_list_check_file(cfp,iter)

def save_ofl_check_file(checkfilepath:pathinfo,filepath:pathinfo)->str|None:
    """保存单个文件的校验数据"""
    cfp=Path(checkfilepath)
    fp=Path(filepath)
    ft=GLOBAL_FILE_TOP
    if not fp.is_file():
        return "不是文件"
    try:
        with cfp.open("wt")as f:
            f.write(ft+"|file\n")
            f.write("one file|"+get_file_sha256(fp)+"\n")
    except(FileNotFoundError,NotADirectoryError):
        return SCF_TNF

def save_check_file(cfp:pathinfo,path:pathinfo,args:argparse.Namespace)->None:
    """推算保存校验文件"""
    p=Path(path)
    def ep(t):
        log.debug("保存校验文件结果: "+str(t))
        if t:print(t)
    if p.is_file():
        print("计算文件校验…")
        ep(save_ofl_check_file(cfp,p))
    elif p.is_dir():
        print("迭代计算校验…")
        ep(save_dir_check_file(cfp,p,args.sort))
    elif p.exists():
        print("不支持除了文件和目录之外的类型")
    else:
        print("路径不存在")

def g_cf_l(f:"file object")->tuple[str,str]|None:
    """获取一行校验信息"""
    l=f.readline().rstrip("\r\n")
    if not l:
        return None
    try:
        fn,ck=l.rsplit("|",1)
        return (fn,ck)
    except ValueError:
        return None

def i_cf_l(f:"file object")->tuple[str,str]:
    iswhi=True
    while iswhi:
        fc=g_cf_l(f)
        if fc is None:
            iswhi=False
            return "内部认为已达到文件末尾"
        yield fc

def check_one_file(f:"file object",path:pathinfo)->str|bool:
    """校验单个文件"""
    fc=g_cf_l(f)
    p=Path(path)
    if fc is None:
        return "校验文件无内容"
    if not p.is_file():
        return "被校验的路径不是文件"
    if check_file(p,fc[1]):
        return "校验成功"
    else:return "校验失败"

def check_df_ok(name:pathinfo)->None:
    """校验成功时执行"""
    check_ok.append(str(name))

def check_df_no(name:pathinfo)->None:
    """校验失败时执行"""
    check_no.append(str(name))

def print_check_no():
    if len(check_no)<1:return
    print("==校验失败的文件==")
    for i in check_no:
        print(i)
    print("==================")

def check_dir_file(f:"file object",path:pathinfo)->None:
    """校验一个目录"""
    p=Path(path)
    la=lf=ls=le=0
    for fc in i_cf_l(f):
        ip=Path(fc[0])
        ph=p/ip
        la+=1
        if not ph.is_relative_to(p):
            log.error(f"校验文件内的数据路径不在提供的路径中。\n传入的路径: {p}\n文件中的路径: {ip}\n拼合的路径: {ph}")
            return "校验文件内的数据路径错误"
        if not ph.is_file():
            et=f"目标路径'{ph}'不是文件"
            log.warning(et)
            print(et)
            continue
        lf+=1
        log.debug(f"""校验"{ph}"…""")
        if is_print_progress:
            print("校验",ph,"中…")
        if check_file(ph,fc[1]):
            ls+=1
            log.debug(f"""校验"{ph}"成功""")
            check_df_ok(ip)
        else:
            le+=1
            log.debug(f"""校验"{ph}"失败""")
            check_df_no(ip)
    print(f"列表总数:{la},有效数量:{lf},校验成功:{ls},校验失败:{le}")
    print_check_no()

def check_list_one(f:"file object",path:pathinfo)->bool|None:
    """校验列表中的某个文件"""
    p=Path(path)
    fn=p.name
    for fc in i_cf_l(f):
        if fn!=fc:continue
        return check_file(p,fc[1])

def check_list_file(f:"file object",path:pathinfo)->None:
    """校验列表文件"""
    p=Path(path)
    def ep(t):
        if t:print(t)
    if p.is_dir():
        print("迭代校验文件…")
        ep(check_dir_file(f,p))
    elif p.is_file():
        print("迭代查找文件后校验…")
        c=check_list_one(f,p)
        log.debug("找到的文件校验结果: "+str(c))
        if c is None:
            print("未找到目标文件")
        elif c:
            print("校验成功")
        else:
            print("校验失败")

def check_path_file(checkfile:pathinfo,path:pathinfo)->None:
    """校验路径中的文件"""
    p=Path(path)
    cf=Path(checkfile)
    ft=GLOBAL_FILE_TOP
    if not cf.is_file():
        print("提供的校验文件不存在")
        return
    with cf.open()as f:
        top=f.readline().rstrip("\r\n")
        gft,tp=top.rsplit("|",1)
        if gft!=ft:
            print("不是校验文件")
            return
        if tp=="file":
            print(check_one_file(f,p))
        elif tp=="list":
            check_list_file(f,p)
        else:
            print("未知的校验类型'",tp,"'，请确保是正确的文件。")

def main():
    global is_print_progress
    p=argparse.ArgumentParser(description="文件校验")
    p.add_argument("path",help="路径",type=Path)
    p.add_argument("-p","--print-progress",help="打印进度",action="store_true")
    sac=p.add_mutually_exclusive_group()# 保存和检查不可共存
    sac.add_argument("-S","--save-check",help="保存校验文件",type=Path,metavar="PATH")
    p.add_argument("--sort",help="当保存校验文件时，对列表进行排序",action="store_true")
    sac.add_argument("-C","--check",help="校验文件",type=Path,metavar="FILE")
    args=p.parse_args()
    fp=args.path
    log.debug("校验文件头部: "+str(GLOBAL_FILE_TOP))
    log.debug("参数: "+str(args))
    is_print_progress=args.print_progress
    if args.save_check:
        save_check_file(args.save_check,fp,args)
        return
    if args.check:
        check_path_file(args.check,fp)
        return
    print("文件:",fp.resolve())
    print("校验数据:",get_file_sha256(fp))

if __name__=="__main__":
    main()

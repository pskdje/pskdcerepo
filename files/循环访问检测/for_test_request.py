#!/bin/env python
"""循环检测是否可以访问
依赖: requests
"""
import os
from urllib.parse import urlparse
import requests

args=None
timeout=5
isokcode=False
resobj=None
runshell=None

def req(url:str):
    """发出请求，获取响应对象。"""
    return requests.head(url,timeout=timeout)

def isexc_req(url:str):
    """获取响应，捕获异常。"""
    try:
        return req(url)
    except requests.exceptions.Timeout:
        return "timeout"
    except requests.exceptions.ConnectionError:
        return "connection"
    except requests.exceptions.RequestException:
        return "request"
    except KeyboardInterrupt:
        return "stop"
    return "unknow"

def isok(rs:requests.Response):
    """检查是否可用"""
    if isokcode:
        if rs.status_code < 400:return True
        else:return False
    return True

def fortest(url:str):
    """循环检测可用性。"""
    global resobj
    count=0
    while True:
        count+=1
        print("循环",count)
        rq=isexc_req(url)
        if isinstance(rq,str):
            if rq=="timeout" or rq=="connection":continue
            elif rq=="stop":return "stop"
            else:return "error"
        ok=isok(rq)
        resobj=rq
        if ok:return "success"
        else:return "bodyerror"

def prompt(url:str):
    """URL可用时执行\n在此扩充功能来自定义提示方式。"""
    print("请求成功")
    if isinstance(resobj,requests.Response):
        print("状态码:",resobj.status_code)
    if runshell:
        os.system(runshell)

def URL(s:str):
    """检查URL字符串是否正确"""
    p=urlparse(s)
    if p.scheme!="http"and p.scheme!="https":raise ValueError("scheme")
    if p.netloc==""or "."not in p.netloc:raise ValueError("origin")
    return s

def main():
    import argparse
    global args
    global timeout
    global isokcode
    global runshell
    p=argparse.ArgumentParser(
        description="循环检测能否访问"
    )
    p.add_argument("url",help="要检测的链接",type=URL)
    p.add_argument("--timeout","-t",help="指定超时时间",type=int,default=5,metavar="INT")
    p.add_argument("--isokcode","-K",help="指定是否必须为成功的响应代码",action="store_true")
    p.add_argument("--run-shell","-r",help="当可访问时执行的shell代码",metavar="SHELLCODE")
    args=a=p.parse_args()
    timeout=a.timeout
    isokcode=a.isokcode
    runshell=a.run_shell
    url=a.url
    print("URL:",url)
    rt=fortest(url)
    if rt=="success":
        prompt(url)
    elif rt=="stop":
        print("停止运行")
    elif rt=="error":
        print("出现错误")

if __name__=="__main__":
    main()

#!/usr/bin/env python
"""HTTP Server

一个简单的HTTP服务器
映射目录
从 http.server 修改而成
"""

import os
import io
import sys
import time
import html
import contextlib
import http.server
import urllib.parse
from typing import Any, NoReturn
from traceback import print_exc

TIME_FORMAT: str = "%Y/%m/%d-%H:%M:%S"
DEFAULT_ERROR_MESSAGE: str = """<!DOCTYPE html>
<html>
	<head>
		<meta charset="UTF-8" />
		<title>错误响应</title>
		<meta name="viewport" content="width=device-width,initail-scale=1.0" />
	</head>
	<body>
		<h1>响应错误</h1>
		<p>错误代码: %(code)d</p>
		<p>消息: %(message)s.</p>
		<br />
		<p>%(explain)s.</p>
	</body>
</html>
"""
directory: str | None = None

class WebServer(http.server.ThreadingHTTPServer):
    """服务器类"""

    def server_bind(self)-> Any:
        # http.server L1294
        with contextlib.suppress(Exception):
            self.socket.setsockopt(
                socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        return super().server_bind()
    def finish_request(self, request, client_address):
        self.RequestHandlerClass(request, client_address, self, directory=directory)

class FileHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """文件"""

    server_version: str = "fs/0.1"
    error_message_format: str = DEFAULT_ERROR_MESSAGE

    def log_date_time_string(self)-> str:
        """返回当前时间给日志"""
        return time.strftime(TIME_FORMAT)
    def address_string(self)-> str:
        """返回地址字符串"""
        host = self.client_address[0]
        try:
            port = str(self.client_address[1])
            if ":" in host:
                return f"[{host}]:{port}"
            else:
                return f"{host}:{port}"
        except IndexError:
            return self.client_address[0]
    def log_message(self, format: str, *args, file: "IO"=sys.stdout)-> NoReturn:
        """日志"""
        message = format % args
        file.write("%s - - [%s] %s\n" %
                   (self.address_string(),
                    self.log_date_time_string(),
                    message.translate(self._control_char_table)))
    def log_error(self, format: str, *args, file: "IO"=sys.stderr)-> NoReturn:
        """错误日志"""
        self.log_message(format, *args, file=file)
    def do_GET(self):
        """GET请求"""
        try:
            f = self.send_head()
            if f:
                try:
                    self.copyfile(f, self.wfile)
                finally:
                    f.close()
        except BrokenPipeError:
            self.log_error("管道已关闭")
        except ConnectionResetError:
            self.log_error("连接被重置")
    def list_directory(self, path: str)-> "BytesIO|None":
        """列出目录下的文件列表

        直接照搬继承链上对应的函数，并进行修改
        """
        try:
            list = os.listdir(path)
        except OSError:
            self.send_error(404, "无权列出目录")
            return None
        list.sort(key=lambda a: a.lower())
        r = []
        try:
            displaypath = urllib.parse.unquote(self.path,
                                               errors='surrogatepass')
        except UnicodeDecodeError:
            displaypath = urllib.parse.unquote(path)
        displaypath = html.escape(displaypath, quote=False)
        enc = sys.getfilesystemencoding()
        title = f'路径 {displaypath} 的目录列表'
        r.append('<!DOCTYPE HTML>')
        r.append('<html>\n<head>')
        r.append(f'<meta charset="{enc}" />')
        r.append('<meta name="viewport" content="width=device-width,initail-scale=1.0" />')
        r.append(f'<title>{title}</title>\n</head>')
        r.append(f'<body>\n<h1>{title}</h1>')
        r.append('<hr />\n<ul id="list">')
        for name in list:
            fullname = os.path.join(path, name)
            displayname = linkname = name
            # Append / for directories or @ for symbolic links
            if os.path.isdir(fullname):
                displayname = name + "/"
                linkname = name + "/"
            if os.path.islink(fullname):
                displayname = name + "@"
                # Note: a link to a directory displays with @ and links with /
            r.append('<li class="list_item"><a class="href" href="%s">%s</a></li>'
                    % (urllib.parse.quote(linkname,
                                          errors='surrogatepass'),
                       html.escape(displayname, quote=False)))
        r.append('</ul>\n<hr />\n</body>\n</html>\n')
        encoded = '\n'.join(r).encode(enc, 'surrogateescape')
        f = io.BytesIO()
        f.write(encoded)
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=%s" % enc)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        return f

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--bind", metavar="ADDRESS",
                        help="绑定到此地址")
    parser.add_argument('-d', '--directory', default=os.getcwd(),
                        help="目录路径 (默认值: 当前路径)")
    parser.add_argument('port', default=8000, type=int, nargs='?',
                        help="绑定到此端口 (默认值: %(default)s)")
    args = parser.parse_args()
    directory = args.directory

    WebServer.address_family, addr = http.server._get_best_family(args.bind, args.port)
    try:
        with WebServer(addr, FileHTTPRequestHandler) as httpd:
            host, port = httpd.socket.getsockname()[:2]
            url_host: str = f"[{host}]" if ":" in host else host
            print(f"HTTP服务器监听 {host} 端口 {port} "
                  f"(http://{url_host}:{port}/) ...")
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("=> exit\n检测到中断键被按下，关闭服务器。")
                sys.exit(0)
    except OSError as e:
        if e.errno == 98:
            print("地址已被使用", file=sys.stderr)
        else:
            print_exc()
        sys.exit(1)

# 我就是想直接访问

因为众所周知的原因，一些网站可以直接访问，但是很不稳定。

这个文件可以一直尝试访问这个链接，当认为可以访问时停止并提示。

**注意:** 默认的提示方法仅为在标准输出打出一些信息和执行传入的shell代码。

**提示:** 可以修改提示的函数来自定义提示方法。

如果是不能直接访问的网站就别指望本文件了。

## 声明和版权

本文件夹按照[CC0](https://creativecommons.org/publicdomain/zero/1.0/)进行共享。

若不正确不正当使用所造成的损失与本人无关。

使用前请审查源代码。

## 依赖

合适的Python解释器和内置库

requests

## 命令行参数

### `url`

指定要检测的链接。

不会跟踪重定向。

协议，域名都不能少。协议只支持`http`和`https`。不支持不含`.`的域名。

### `--timeout`

> `--tiomeout` | `-t`

指定连接超时时间，单位：秒。

***类型:*** `int` (整数)

***默认值:*** `5`

### `--isokcode`

> `--isokcode` | `-K`

指定必须要成功的状态码。

当响应状态码小于400时认为成功；否则失败，继续循环。

### `--run-shell`

> `--run-shell` | `-r`

指定可访问时执行的shell代码。

## 函数

### `main()`

入口。

### `URL()`

检查输入的URL。

### `prompt(url:str)`

当认为可以访问时将调用此函数。

扩写此函数来定制自己的提示方法吧。

### 其它

**自己看源代码，我懒得写。**

# 末尾

本仓库的其它文件可不一定是同样的共享状态。

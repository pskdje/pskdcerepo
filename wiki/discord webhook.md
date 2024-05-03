# Discord Webhook

**更新时间:** `2024/05/02`

[Discord](https://discord.com/) [文档](https://discord.com/developers/docs/resources/webhook#execute-webhook)

## 信息

### 根对象

| 键 | 类型 | 说明 |
|:---:|:---:|:--- |
| content | string | 正文，显示在最前面，可使用markdown。 |
| username | string | 设定本次使用的名称 |
| avatar_url | string | 设定本次使用的头像 |
| embeds | array | 嵌入内容 |

### `embeds`数组

| 索引 | 类型 | 说明 |
| --- | --- |:--- |
| 0~10 | object | 各自指定一个组件 |

`embeds`数组内对象:

这些都是可选的，按照可能的显示顺序排列。

| 键 | 类型 | 说明 |
|:---:|:---:|:--- |
| color | integer | 指定左侧竖线的颜色值 |
| description | string | 描述(不可见) |
| author | object | 设置作者部分 |
| title | string | 标题 |
| url | string | 标题的链接 |
| thumbnail | object | 缩略图(部分平台可见) |
| fields | array | 字段列表 |
| image | object | 设置图片 |
| video | object | 设置视频(目前不可用) |
| footer | object | 设置末尾内容 |

#### `author`对象

类型均为字符串，除`name`外都可选。

| 键 | 说明 |
|:---:|:--- |
| name | (必须)作者名称 |
| url | 点击作者名称进入的链接 |
| icon_url | 作者图标(头像) |

#### `thumbnail`对象

| 键 | 类型 | 必要? | 说明 |
|:---:|:---:| --- |:--- |
| url | string | 必须 | 图片链接 |

#### `fields`数组

| 索引 | 类型 | 说明 |
| --- | --- |:--- |
| 0~25 | object | 按顺序指定字段 |

`fields`数组内对象:

| 键 | 类型 | 必要? | 说明 |
|:---:|:---:| --- |:--- |
| name | string | 必须 | 名称，展示在该字段的开头 |
| value | string | 必须 | 内容，可使用markdown语法 |
| inline | boolean | 可选 | 决定行内展示(特定平台可见) |

#### `image`对象

| 键 | 类型 | 必要? | 说明 |
|:---:|:---:| --- |:--- |
| url | string | 必须 | 图片链接 |

#### `footer`对象

类型均为字符串。

| 键 | 必要? | 说明 |
|:---:| --- |:--- |
| text | 必须 | 末尾内容 |
| icon_url | 可选 | 图标链接 |

## 结构

```json
{
	"content": "**正文** `markdown`可用",
	"username": "XXX Bot",
	"avatar_url": "http://u.l/avatar.png",
	"embeds":[
		{
			"color": 2483,
			"description": "描述",
			"author":{
				"name": "XXX作者",
				"url": "http://u.l/author/XXX",
				"icon_url": "http://u.l/a/author/XXX.png"
			},
			"title": "标题，使用url来指定标题的链接",
			"url": "http://u.l/blog/383",
			"thumbnail":{
				"url": "http://u.l/a/blog/383_1.png"
			},
			"fields":[
				{
					"name": "abcd",
					"value": "a **and** b **and** c **and** d"
				},
				{
					"name": "book 1",
					"value": "annine outing opt end",
					"inline": true
				},
				{
					"name": "book 2",
					"value": "annity img okbe fong",
					"inline": true
				}
			],
			"image":{
				"url": "http://u.l/a/blog/383_5.png"
			},
			"footer":{
				"text": "by url",
				"icon_url": "http://u.l/favicon.ico"
			}
		},
		{},{},{},{},{},{},{},{},{}
	]
}
```

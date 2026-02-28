# 2026 OpenClaw必装Skills

**来源**: https://x.com/AYi_AInotes/status/2027180893316813008
**作者**: 阿绎 · 认知代码
**类型**: 产品使用指南
**日期**: 2026-02-27

---

Title: 阿绎 · 认知代码 on X: "2026 OpenClaw必装Skills——不装等于白部署（含新手必看7大skill安装避坑指南，代码指令一键复制即可）" / X

URL Source: https://x.com/AYi_AInotes/status/2027180893316813008

Published Time: Fri, 27 Feb 2026 10:22:45 GMT

Markdown Content:
Article
-------

Conversation
------------

[![Image 1: Image](https://pbs.twimg.com/media/HCGixUfaAAAVlBk?format=jpg&name=small)](https://x.com/AYi_AInotes/article/2027180893316813008/media/2027080275491160064)

2026 OpenClaw必装Skills——不装等于白部署（含新手必看7大skill安装避坑指南，代码指令一键复制即可）

OpenClaw部署完成后，默认仅具备基础对话能力，需安装必装Skills才能解锁实操功能。以下详细拆解4个必装Skills的安装、配置与实战用法，所有代码命令均可直接复制执行，同时补充技能组合最佳实践，帮助新手快速上手。

（一）2026版OpenClaw核心升级亮点

1.   Skills生态完善：ClawHub作为官方技能市场，已收录3000+款实用Skills，且支持一键安装、即插即用，无需复杂配置，新手也能快速上手，同时支持自定义开发技能，适配个性化需求；

2.   安全性与稳定性提升：新增权限管控、日志审计、指令白名单等功能，可限制文件访问范围、禁止高危操作，避免部署后出现安全风险；同时优化后台运行机制；

（二）必装Skills核心价值：不装等于白部署

OpenClaw的核心能力完全依赖Skills扩展，ClawHub上现有3000+技能，但90%实用性较低。以下4个Skills是基础必备，装上后才能真正发挥AI的主动执行能力，解决80%的日常使用场景，覆盖技能发现、全网搜索、AI优化查询等核心需求，是新手入门的必装选项：

1.   Find Skills（技能导航仪）：作为“元Skill”，核心作用是帮用户快速发现、安装、更新所需技能，解决“不知道有什么技能可用”“找不到对应功能插件”的痛点，是探索OpenClaw生态的必备工具[3]；

2.   Tavily Search（精准搜索利器）：专为AI助手设计的搜索引擎，返回结果经过结构化处理，简洁且相关性强，避免AI处理冗余信息，同时支持深度搜索、新闻专题搜索等功能，让OpenClaw具备“实时联网获取信息”的能力[2][3]；

3.   Multi Search Engine（全网搜索聚合器）：集成17个搜索引擎（8个国内+9个国际），无需API Key即可实现全网搜索，支持隐私搜索、知识计算、快捷指令等高级功能，是OpenClaw的“信息获取中枢”；

4.   Office-Automation（办公自动化技能）：覆盖日程管理、邮件处理、文档编辑、数据统计等核心办公场景，可自动生成周报、同步日程、处理Excel表格，是提升个人与企业办公效率的核心技能。

（一）Skills管理核心命令（通用，必记）

在安装Skills前，先掌握以下核心命令，用于Skills的安装、卸载、启用、禁用与管理，适配所有Skills，全程在服务器终端执行：

```
# 查看已安装Skills（查看状态，确保正常启用）
openclaw skills list --status ready
# 安装Skills（两种方式，推荐ClawHub CLI，稳定无报错）
npx clawhub@latest install <skill-slug>  # 官方推荐方式，适配2026版
openclaw skills install <skill-slug>     # 备选方式，兼容旧版本
# 卸载不需要的Skills
openclaw skills uninstall <skill-slug>
# 启用/禁用Skills（无需卸载，灵活开关）
openclaw skills enable <skill-slug>
openclaw skills disable <skill-slug>
# 检查Skills更新，更新所有已安装Skills
npx skills check
npx skills update all
# 查看Skills详细信息（了解功能与配置方法）
openclaw skills info <skill-slug>
```

（二）必装Skill 1：Find Skills（技能导航仪，必装首选）

核心定位

作为“元Skill”，Find Skills的核心作用是帮用户快速发现、安装、更新所需技能，解决“不知道有什么技能可用”“找不到对应功能插件”的痛点，是探索OpenClaw生态的必备工具，新手必装[3]。

安装与配置（一键完成，无需额外配置）

```
# 安装Find Skills（官方推荐方式，适配2026版）
npx clawhub@latest install find-skills
# 验证安装结果，显示"find-skills"且状态为"ready"即成功
openclaw skills list --status ready
# （可选）更新Find Skills至最新版本
npx skills update find-skills
```

配置：无需额外配置，开箱即用，支持通过自然语言或命令行搜索技能

实战用法（新手必备）

1.   搜索特定功能技能（自然语言指令）：在Web控制台或已对接的IM平台发送指令，例如“帮我找一个能批量处理Excel的技能”“搜索邮件自动化相关的Skills”，Find Skills会自动推荐相关插件，并给出安装命令[3]；

2.   命令行搜索与安装：

```
# 搜索Excel处理相关技能
openclaw skills search excel
# 搜索邮件自动化相关技能
openclaw skills search email
# 一键安装搜索到的技能（替换为实际技能名称）
npx clawhub@latest install excel-processor
```

3. 技能更新与管理：

```
# 检查所有已安装技能的更新
npx skills check
# 更新指定技能（以find-skills为例）
npx skills update find-skills
# 查看已安装技能的详细信息
openclaw skills info find-skills
```

三）必装Skill 2：Tavily Search（精准搜索利器，联网必备）

核心定位

专为AI助手设计的搜索引擎，返回结果经过结构化处理，简洁且相关性强，避免AI处理冗余信息，同时支持深度搜索、新闻专题搜索等功能，让OpenClaw具备“实时联网获取信息”的能力，解决OpenClaw默认无法联网、知识滞后的问题[2][3]。

安装与配置（简单配置，开箱即用）

```
# 安装Tavily Search
npx clawhub@latest install tavily-search
# 验证安装结果
openclaw skills list --status ready
# 配置Tavily Search（设置搜索语言为中文，优化搜索结果）
openclaw skills configure tavily-search
# 按提示输入配置：language=zh-CN，其他保持默认，回车确认
```

实战用法（高频场景）

1.   实时资讯搜索（自然语言指令）：指令1：“帮我用Tavily Search搜索2026年OpenClaw最新版本更新内容，返回结构化结果”； 指令2：“用Tavily Search查询阿里云百炼最新免费额度政策，带来源链接”； 实战效果：2分钟内返回带来源链接的结构化信息，无需手动筛选冗余内容[3]；

2.   深度搜索（复杂问题调研）：

```
# 深度搜索Python代码报错解决方案（替换为实际报错信息）
openclaw chat "用tavily-search --deep 搜索'Python ValueError: invalid literal for int() with base 10'的解决方案"
```

3. 新闻专题搜索：

```
# 搜索近期AI领域热门新闻，返回5条核心内容
openclaw chat "用tavily-search --news 搜索近期AI领域热门新闻，返回5条，每条包含标题、摘要、来源"
```

（四）必装Skill 3：Multi Search Engine（全网搜索聚合器，多源验证）

核心定位

集成17个搜索引擎（8个国内+9个国际），无需API Key即可实现全网搜索，支持隐私搜索、知识计算、快捷指令等高级功能，是OpenClaw的“信息获取中枢”，适合需要多来源对比验证信息的场景[3]。

支持的搜索引擎（核心亮点）

[![Image 2: Image](https://pbs.twimg.com/media/HCGeNZ1akAACkKA?format=jpg&name=small)](https://x.com/AYi_AInotes/article/2027180893316813008/media/2027075260403847168)

安装与配置（无需额外配置，开箱即用）

```
# 安装Multi Search Engine
npx clawhub@latest install multi-search-engine
# 验证安装结果，显示"multi-search-engine"且状态为"ready"即成功
openclaw skills list --status ready
# （可选）配置默认搜索引擎（如设置百度为默认国内搜索引擎）
openclaw config set skills.multi-search-engine.default-engine baidu
```

实战用法与选型指南

1.   多来源搜索验证： # 用多个搜索引擎搜索同一问题，对比验证结果 openclaw chat "用multi-search-engine搜索'2026年阿里云轻量应用服务器最新价格'，对比3个不同搜索引擎的结果"

2.   隐私搜索（无需登录，不追踪行为）： # 用DuckDuckGo进行隐私搜索 openclaw chat "用multi-search-engine --engine duckduckgo 搜索'OpenClaw自定义技能开发教程'"

3.   知识计算（数学、单位转换等）： # 用WolframAlpha进行知识计算（如数学公式、单位转换） openclaw chat "用multi-search-engine --engine wolframalpha 计算sin(60°)的值，转换100美元为人民币"

4.   选型指南（Tavily vs Multi Search Engine）[3]：快速获取精准信息：选Tavily Search（AI优化结果，结构化呈现）； 多来源对比验证：选Multi Search Engine（17个引擎全覆盖）； 深度研究复杂问题：选Tavily Search（--deep模式，深度挖掘信息）； 隐私保护需求：选Multi Search Engine（DuckDuckGo/Startpage）； 知识计算（数学/单位转换）：选Multi Search Engine（WolframAlpha）。

（五）必装Skill 4：Office-Automation（办公自动化，效率神器）

核心定位

覆盖日程管理、邮件处理、文档编辑、数据统计等核心办公场景，可自动生成周报、同步日程、处理Excel表格、发送邮件，是提升个人与企业办公效率的核心技能，适合日常办公、团队协作场景[2][3]。

安装与配置（需简单配置，适配办公场景）

```
# 安装Office-Automation技能
npx clawhub@latest install office-automation
# 验证安装结果
openclaw skills list --status ready
# 配置办公自动化技能（邮件账号、日程同步等）
openclaw skills configure office-automation
```

配置步骤（按终端提示操作）

1.   邮件配置：输入个人/企业邮箱账号、密码（或授权码），设置SMTP服务器（如QQ邮箱SMTP：smtp.qq.com，端口465）；

2.   日程配置：选择同步方式（如飞书日程、Outlook日程），输入对应平台凭证，完成同步；

3.   文档配置：设置默认文档保存路径（如/root/office-files），选择文档格式（默认PDF/Excel/Word）；

4.   配置完成后，执行以下命令重启服务，使配置生效： openclaw gateway restart

实战用法（高频办公场景）

1.   生成后会自动保存至默认文档路径，同时可发送至指定邮箱；自动生成工作周报： # 生成本周工作周报，包含工作内容、成果、下周计划 openclaw chat "用office-automation生成本周工作周报，工作内容：部署OpenClaw、安装必装Skills；成果：完成阿里云部署与技能配置，实现自动化搜索与办公；下周计划：学习自定义技能开发、对接飞书渠道"

2.   邮件自动化处理： # 发送邮件，带附件（替换为实际邮箱、主题、内容和附件路径） openclaw chat "用office-automation发送邮件，收件人：xxx@163.com，主题：OpenClaw部署总结，内容：已完成阿里云OpenClaw部署与必装Skills配置，附件：/root/office-files/OpenClaw部署总结.pdf" # 查看未读邮件并汇总 openclaw chat "用office-automation查看我的未读邮件，汇总邮件主题和发件人"

3.   Excel数据处理： # 批量处理Excel表格，统计数据并生成图表 openclaw chat "用office-automation处理/root/office-files/销售数据.xlsx，统计各产品月度销售额，生成柱状图，保存至原路径"

4.   日程管理： # 添加日程提醒（替换为实际时间和内容） openclaw chat "用office-automation添加日程提醒：明天上午10点，OpenClaw技能测试，提醒方式：邮件+钉钉" # 查看本周日程 openclaw chat "用office-automation查看本周所有日程，按时间排序"

（六）Skills组合最佳实践（新手推荐）

单一Skills的功能有限，通过技能组合可实现更复杂的自动化任务，以下推荐2个高频组合场景，新手可直接复用[3]：

1.   信息调研+报告生成：Multi Search Engine（多源搜索）→ Tavily Search（深度挖掘）→ Office-Automation（生成报告），例如： openclaw chat "先用multi-search-engine搜索2026年AI自动化工具发展趋势，再用tavily-search --deep 挖掘核心数据，最后用office-automation生成分析报告，保存为PDF并发送至我的邮箱"

2.   办公自动化闭环：Find Skills（搜索所需技能）→ Office-Automation（执行办公任务）→ Tavily Search（补充实时信息），例如： openclaw chat "先用find-skills搜索'Excel批量数据导入'相关技能，安装后批量导入数据，再用tavily-search查询最新数据统计标准，最后用office-automation生成统计报表"

在部署OpenClaw及安装Skills过程中，新手容易遇到各类报错，以下整理了2026年最新高频问题，包含报错现象、核心原因和详细解决方案，快速定位并解决问题，避免卡壳[1][2][5]。

问题1：OpenClaw初始化提示“API-Key invalid”（模型授权失败）

*   现象：执行初始化命令后，输入API-Key提示“密钥无效”，无法对接阿里云百炼模型；

*   核心原因：API-Key输入错误、密钥已过期/被禁用、模型提供商选择错误；

*   解决方案：重新核对API-Key，确保无拼写错误、无多余空格（API-Key区分大小写）； 登录阿里云百炼控制台，进入“密钥管理”，确认密钥处于“启用”状态，若已过期或泄露，删除旧密钥并重新创建； 重新执行初始化命令，确保模型提供商选择“Qwen (OAuth)”（阿里云百炼），避免选错其他模型平台。

问题2：Skills安装提示“网络超时”或“安装失败”

*   现象：执行Skills安装命令时，提示“timeout”“failed to download”或“npm install failed”；

*   核心原因：国内网络访问海外服务器延迟过高，导致下载失败；或服务器内存不足；

*   解决方案： 配置国内镜像源，加速插件下载[3]： # 配置国内Skills安装镜像源 openclaw config set plugins.registry

# 重新安装Skills npx clawhub@latest install <skill-slug>若提示内存不足，添加虚拟内存（参考前文“内存优化”步骤），重启服务后重新安装； 更换安装方式，用备选命令安装[4]： openclaw skills install <skill-slug> 

问题3：启动服务提示“端口18789被占用”

*   现象：执行openclaw gateway start后，提示“Port 18789 is already in use”；

*   核心原因：18789端口被其他程序占用；

*   解决方案[2]： # 查找占用18789端口的程序PID lsof -i:18789 # 终止占用端口的程序（替换PID为实际查到的进程ID） kill -9 程序PID # 重新启动服务 openclaw gateway restart # （备选）若无法终止进程，修改OpenClaw默认端口 nano ~/.openclaw/openclaw.json # 修改"server":{"port":18790}（将端口改为18790） openclaw gateway restart

问题4：Skills安装成功但无法使用，提示“skill not ready”

*   现象：openclaw skills list显示Skills已安装，但状态为“not ready”，发送指令无响应；

*   核心原因：Skills未启用，或缺少依赖，或配置未生效；

*   解决方案： # 启用Skills openclaw skills enable <skill-slug># 检查并安装Skills所需依赖 openclaw skills install-deps <skill-slug># 重启OpenClaw服务，使配置生效 openclaw gateway restart # 重新查看Skills状态，确保为"ready" openclaw skills list --status ready

问题5：Web控制台登录提示“unauthorized”（Token无效）

*   现象：输入Token登录Web控制台时，提示“未授权，Token无效或过期”；

*   原因：Token输入错误、Token已过期，或服务未正常启动；

*   解决方案[2][5]：重新生成Token：openclaw token generate --expire 365d； 复制终端输出的完整Token，确保无多余空格，重新登录； 若仍失败，重启网关服务：openclaw gateway restart，重新生成Token后登录。

问题6：Office-Automation技能无法发送邮件

*   现象：执行邮件发送指令后，提示“邮件发送失败”，无其他报错；

*   核心原因：SMTP服务器配置错误、邮箱授权码错误、端口未放行；

*   解决方案：重新配置Office-Automation技能，核对SMTP服务器地址和端口（如QQ邮箱：smtp.qq.com，端口465；163邮箱：smtp.163.com，端口465）； 确认邮箱授权码正确（部分邮箱需开启第三方授权，获取授权码替代密码）； 放行邮箱SMTP端口（如465端口），执行以下命令： ufw allow 465/tcp && ufw reload重启服务后重新测试邮件发送。

问题7：服务器重启后，OpenClaw与Skills无法自动启动

*   现象：服务器重启后，执行openclaw status显示“stopped”，Skills无法使用；

*   核心原因：未设置OpenClaw开机自启，或开机自启配置失效；

*   解决方案[2][5]： # 重新设置OpenClaw开机自启 openclaw gateway enable # 验证开机自启配置，显示"yes"即成功 openclaw gateway is-enabled # 启动服务 openclaw gateway start # 检查Skills状态，确保所有必装Skills已启用 openclaw skills list --status ready

（一）Skills优化：提升运行效率

1.   关闭无用Skills：避免多余Skills占用服务器资源，提升运行速度： # 查看所有已安装Skills openclaw skills list # 禁用无用Skills（替换为实际技能名称） openclaw skills disable <skill-slug>

2.   清理Skills缓存：定期清理Skills运行缓存，释放磁盘空间： # 清理所有Skills缓存 openclaw skills clean-cache # 清理指定Skills缓存（替换为实际技能名称） openclaw skills clean-cache <skill-slug>

（二）自定义Skills开发（技术用户可选）

若必装Skills无法满足个性化需求，可自定义开发Skills，部署到OpenClaw中使用，核心步骤如下[4][5]：

1.   创建Skills开发目录： # 创建自定义Skills目录 mkdir -p ~/.openclaw/skills/my-custom-skill cd ~/.openclaw/skills/my-custom-skill

2.   创建核心配置文件（skill.json）： nano skill.json写入以下内容（自定义修改技能名称、描述、功能）： { "name": "my-custom-skill", "version": "1.0.0", "description": "自定义办公自动化技能，实现批量重命名文件", "author": "自定义作者", "dependencies": { }, "entry": "index.js" }

3.   编写技能逻辑（index.js），实现具体功能（如批量重命名文件）；

4.   安装自定义Skills：# 安装本地自定义Skills openclaw skills install ~/.openclaw/skills/my-custom-skill # 启用自定义Skills openclaw skills enable my-custom-skill # 验证安装结果 openclaw skills list --status ready


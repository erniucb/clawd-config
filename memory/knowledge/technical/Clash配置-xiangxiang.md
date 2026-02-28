# OpenClaw Clash配置

**来源**: https://x.com/xiangxiang103/status/2026962270316847289
**作者**: xiangxiang103
**类型**: 技术配置
**日期**: 2026-02-27

---

Title: 雨哥向前冲 on X: "200W 浏览的小火箭教程被催爆了！今天填坑：大部分人的 Clash 都在裸奔，一文教你配置终极防封号规则！" / X

URL Source: https://x.com/xiangxiang103/status/2026962270316847289

Published Time: Fri, 27 Feb 2026 09:47:03 GMT

Markdown Content:
Article
-------

Conversation
------------

[![Image 1: Image](https://pbs.twimg.com/media/HCE0zuibAAAN3mg?format=jpg&name=small)](https://x.com/xiangxiang103/article/2026962270316847289/media/2026959370563813376)

200W 浏览的小火箭教程被催爆了！今天填坑：大部分人的 Clash 都在裸奔，一文教你配置终极防封号规则！

前天我读到泊舟

关于小火箭分流的文章，马上提炼了核心内容，给「小火箭（Shadowrocket）」做了一张配置截图分享出来。 万万没想到，那条推文直接爆了，获得了 200w+ 浏览量！

雨哥向前冲

@xiangxiang103

用小火箭的朋友建议配置下，无论是刷推特还是搞ai都是刚需，我给大家提炼了精华，复制懒人链接，打开小火箭配置这两个地方就行了

[![Image 2: Image](https://pbs.twimg.com/media/HB7eQg_bgAAYbj7?format=jpg&name=small)](https://x.com/xiangxiang103/status/2026301452566884782/photo/1)

[![Image 3: Image](https://pbs.twimg.com/media/HB7eT3ubcAAcYxL?format=jpg&name=small)](https://x.com/xiangxiang103/status/2026301452566884782/photo/2)

Quote

泊舟

@bozhou_ai

Feb 24

![Image 4: Article cover image](https://pbs.twimg.com/media/HB6P_RIaQAAhcMT?format=jpg&name=small)

教你如何配置小火箭规则，防止裸奔

上个月我一个朋友找我，说他推特账号被封了。 他很郁闷，说自己就正常刷刷推特，看看新闻，怎么就被封了呢？ 我让他把小火箭的配置发给我看了一下，马上就明白了。他根本没配置规则，所有流量都在乱走。...

在评论区，我的私信几乎被同一个问题塞爆了： “大佬，小火箭讲完了，求出一期 Clash 怎么配置规则啊！”

没错，不仅是小火箭，其实绝大多数用 Clash 的人，也都在网络上“裸奔”。 买了机场，导入订阅，选个节点，能连上 Google 就算完事。甚至根本不知道有「配置规则」这回事，导致经常连不上 TikTok（黑屏无网络）、Netflix（提示使用代理）。

这是我写这篇文章的初衷。 今天就跟你聊透，Clash 的规则到底是什么，为什么要配，以及怎么一键搞定！

先说说规则是干什么的

很多人以为，你连上代理后，Clash 会自动用 AI 般的大脑判断哪些网站该翻墙，哪些该直连。 其实不是的！

如果你不配精细的规则，Clash 根本不知道该怎么智能处理流量。 结果就是：你访问淘宝、微信、B站这些国内网站，流量也会傻乎乎地绕到美国节点去。 这不仅慢得像蜗牛，浪费了你宝贵的机场流量，而且在平台看来，你的行为模式极其诡异： 上一秒还在用家里的宽带登微信，下一秒突然跑到日本刷抖音。

推特、Netflix 尤其是 TikTok，只要侦测到你的 IP 频繁在香港、美国、日本跳来跳去，或者检测到你是机房 IP，它们的风控系统就会直接拉黑你，觉得你是异常账号。

规则，就是彻底解决这个问题的“交通指挥员”。 它告诉 Clash：

*   🟢 国内网站及 IP，用你家宽带“直连”，享受物理极速。

*   🔴 国外被墙网站，必须走节点“代理”。

*   🛑 那些烦人的弹窗广告和追踪器，直接在底层强行“拦截”。

这样流量变得井然有序，你的网络活动看起来完全就像个正常的“当地人”。

规则的工作原理（大白话版）

其实就是查字典。 当你访问

，Clash 会从规则列表里 从上往下查。

如果查到了

对应的规则写着 PROXY（走代理），那就走美国节点。 如果查到了

写着 DIRECT（直连），那就走你家的宽带。 如果有个刚出来的冷门网站找不到匹配项，那就按照最底下的“兜底策略”处理（通常是默认走代理，保证所有国外冷门网站永不卡壳）。

所以规则越全面，字典越厚，你的 Clash 就越聪明。 现在比较成熟的开源规则库，早就把各大厂（苹果/谷歌）的服务、甚至国内精确到 IP 段的流量都摸透了。

我强烈推荐的规则神库

[![Image 5: Image](https://pbs.twimg.com/media/HCEo-gWa8AAGn0q?format=jpg&name=small)](https://x.com/xiangxiang103/article/2026962270316847289/media/2026946361594408960)

上一期小火箭推荐了 Johnshall，而 Clash 届的“武林盟主”，非 GitHub 上的 Loyalsoldier/clash-rules 莫属！ 目前接近 30k Star，地位无可撼动。

这个神器有几个让你拍案叫绝的优点：

*   第一，规则变态级精准：整合了 V2Ray 社区最权威名单，国内 IP 段精准无比，甚至给 Apple 和 Telegram 都做了独立细分。

*   第二，每天凌晨自动更新：这个库每天早上 6:30 由 GitHub 自动抓取全网最新数据并重新构建。网站天天变，但你的规则永远是最新鲜的。

*   第三，全客户端通杀：不管你是最强内核 Clash Premium，还是 Clash Verge、Clash for Windows，全都完美兼容。

GitHub 原地址：

具体怎么配？（有手就行，只需 3 步）

很多小白看到代码就头晕，别怕，我教你怎么一键抄作业。不需要懂什么 IP-CIDR 或者正则匹配。 （以今年最火的 clash-verge-rev 为例，其他客户端举一反三）

千万别去直接改机场的原始配置文件！因为一旦更新订阅，你的所有修改都会被抹除！ 正确的高级玩法是使用“合并覆盖 (Merge)”功能！

第一步：找准位置（全局扩展） 打开 Clash Verge Rev -> 点左侧 订阅。 在右边找到一个写着大大的 “全局扩展覆写配置 (Merge)” 的卡片。 右键点击它，选择 “编辑文件”。

[![Image 6: Image](https://pbs.twimg.com/media/HCEsM0vaMAA7vl1?format=jpg&name=small)](https://x.com/xiangxiang103/article/2026962270316847289/media/2026949906120978432)

第二步：插入这套“识别引擎 + 规则”的组合代码

在弹出的代码编辑器里，全选并清空里面原有的内容，直接粘贴我整理好的这套“前置无敌防御组合”（这会让你的规则像钢印一样死死印在最底层，永远优先执行）：

(你可以直接去 GitHub 复制，或者提取我精简无错的懒人组合！)

```
prepend-rule-providers:
  reject:
    type: http
    behavior: domain
    url: "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/reject.txt"
    path: ./ruleset/reject.yaml
    interval: 86400

  icloud:
    type: http
    behavior: domain
    url: "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/icloud.txt"
    path: ./ruleset/icloud.yaml
    interval: 86400

  apple:
    type: http
    behavior: domain
    url: "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/apple.txt"
    path: ./ruleset/apple.yaml
    interval: 86400

  google:
    type: http
    behavior: domain
    url: "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/google.txt"
    path: ./ruleset/google.yaml
    interval: 86400

  proxy:
    type: http
    behavior: domain
    url: "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/proxy.txt"
    path: ./ruleset/proxy.yaml
    interval: 86400

  direct:
    type: http
    behavior: domain
    url: "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/direct.txt"
    path: ./ruleset/direct.yaml
    interval: 86400

  private:
    type: http
    behavior: domain
    url: "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/private.txt"
    path: ./ruleset/private.yaml
    interval: 86400

  telegramcidr:
    type: http
    behavior: ipcidr
    url: "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/telegramcidr.txt"
    path: ./ruleset/telegramcidr.yaml
    interval: 86400

  cncidr:
    type: http
    behavior: ipcidr
    url: "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/cncidr.txt"
    path: ./ruleset/cncidr.yaml
    interval: 86400

  lancidr:
    type: http
    behavior: ipcidr
    url: "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/lancidr.txt"
    path: ./ruleset/lancidr.yaml
    interval: 86400

  applications:
    type: http
    behavior: classical
    url: "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/applications.txt"
    path: ./ruleset/applications.yaml
    interval: 86400

prepend-rules:
  - RULE-SET,applications,DIRECT
  - RULE-SET,private,DIRECT
  - RULE-SET,reject,REJECT
  - RULE-SET,icloud,DIRECT
  - RULE-SET,apple,DIRECT
  - RULE-SET,google,PROXY
  - RULE-SET,proxy,PROXY
  - RULE-SET,direct,DIRECT
  - RULE-SET,lancidr,DIRECT
  - RULE-SET,cncidr,DIRECT
  - RULE-SET,telegramcidr,PROXY
  - GEOIP,LAN,DIRECT
  - GEOIP,CN,DIRECT
```

第三步：保存即刻生效！这是最爽的 代码贴完点击保存（右下角或者 Ctrl+S）。 这时候见证奇迹的时刻到了！在全新的 Clash Verge Rev 里，全局扩展覆写配置是没有单独的“使用/启用”按钮的。 你只要保存了这段代码，它就像病毒一样，已经无声无息地强行注入到了所有的节点底层生效了！

现在无论以后你的机场主怎么更替那些乱七八糟的节点，这套极速分流规则，永远生效！大功告成！

换上新规则后，你会体验到什么？

私信求教程的朋友们，当你们按照这 3 步做完，你们的网络冲浪体验会发生质的飞跃：

1.   国内秒开：以前开着 Clash 打开 B站总要加载几秒钟转圈圈，现在图片加载速度堪比光速，因为国内流量彻底被剥离直连了。

2.   流媒体完美解锁：以前看 Netflix 动不动提示“检测到代理”，现在你在规则里可以单独把节点绑定在干净的生僻节点上，再也没被拦截过；刷 TikTok 也完全不黑屏了。

3.   电报（Telegram）收发神速：因为这个包单独把电报 IP 摘给代理了，收发消息再也没有延迟。

4.   App 开屏广告大幅减少：底层 reject 规则帮你干掉了大部分追踪器和牛皮癣。

💡 高阶贴士：怎么确认自己配置成功了？

很多小白配完之后心里还是没底，不知道底层规则到底长什么样。教你一个“看底层源码”的终极装X招数：

在主界面左侧点击 “设置” -> 向下滚动找到 “Verge 高级设置” -> 点击 “当前配置”。 这时候会弹出一个包含几百行代码的文本编辑器，这就是 Clash 把你的机场节点和我们的神级规则 强行熔炼后生成的最终配置文件。 从上往下划，当你看到那一排排整齐的 reject、google、apple 以及里面夹杂着上千条精密指令时，享受那一刻极客般的成就感吧！你的网络已经被全面接管了！

[![Image 7: Image](https://pbs.twimg.com/media/HCEufvubEAA4Iu_?format=png&name=small)](https://x.com/xiangxiang103/article/2026962270316847289/media/2026952430215434240)

🛑 最后 1 秒的避坑检查： 回到主界面，必须确保你的 Clash 运行在 「规则 (Rule)」 模式，而不是全局 (Global) 或直连 (Direct)！只有在「规则」模式下，这套耗资千万打造的分流引擎才会接管你的网络。

最后一句心里话：

很多博主为了卖节点，根本不愿意教你这些让你“一劳永逸”的底层配置。 如果你觉得今天这篇 Clash 万字级保姆教程对你有帮助，解决了你心头的疑惑：

1️⃣🔁 请帮忙点赞/分享：让更多使用 Clash 的人告别裸奔，不再天天被封号困扰！ 2️⃣🔖 收藏本推文/文章：换电脑或者帮朋友装的时候，随时掏出来“一键抄作业”。


#!/bin/bash
# Twitter热点扫描 - 使用非持久化浏览器（避免profile冲突）

cd /root/clawd

echo "=== 开始扫描Twitter Web3热点 ==="
echo "时间: $(date '+%Y-%m-%d %H:%M')"
echo ""

# 创建临时数据目录
mkdir -p /tmp/chrome-profile-$(date +%s)

DISPLAY=:1 timeout 120 node << 'NODESCRIPT'
const { chromium } = require('playwright');

(async () => {
  console.log("正在启动Chrome（新实例）...");
  
  const browser = await chromium.launch({
    headless: false,
    args: ['--disable-dev-shm-usage', '--no-sandbox', `--user-data-dir=/tmp/chrome-profile-$(date +%s)`]
  });
  
  const context = await browser.newContext();
  const page = await context.newPage();
  
  console.log("正在访问Twitter时间线...");
  await page.goto('https://x.com/home', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(8000);
  
  // 滚动6次加载更多推文
  console.log("正在滚动加载更多推文...");
  for (let i = 0; i < 6; i++) {
    await page.evaluate(() => {
      window.scrollTo(0, document.body.scrollHeight);
    });
    await page.waitForTimeout(3000);
  }
  
  // 抓取推文
  console.log("\n正在抓取推文...");
  const tweets = await page.evaluate(() => {
    const tweetElements = document.querySelectorAll('[data-testid="tweet"]');
    const results = [];
    
    const web3Keywords = {
      'airdrop': ['airdrop', '空投', 'whitelist', '白名单', 'claim', '领空', 'drop', 'claimable'],
      'new_project': ['launch', 'launching', '首发', 'mainnet', '主网', '测试网', 'testnet', 'v2', 'version 2', 'token launch'],
      'funding': ['funding', '融资', '投资', 'investment', 'round', '融资轮', 'a轮', 'b轮', 'seed', '种子轮', 'series a', 'vc', 'venture capital', 'ico', 'ido'],
      'defi': ['defi', 'yield', '质押', 'restake', '流动性', 'mining', '挖矿', 'lending', '借贷', 'amm', 'aggregator', '聚合器', 'dex'],
      'nft': ['nft', 'whitelist', 'wl', 'mint', '铸造', '发行', 'blindbox', '盲盒', 'floor', 'floor price', 'opensea', 'opensea', 'pfp', 'profile'],
      'token': ['token', '代币', 'coin', 'coinlist', '上所', '币安', 'okx', 'gate', 'binance', 'listing', '上市'],
      'layer2': ['layer2', 'l2', 'rollup', 'zk', 'layer3', 'l3', 'zkrollup', 'zkrollup', 'optimistic rollup', 'optimistic'],
      'meme': ['meme', 'memecoin', 'doge', 'pepe', 'shib', 'bonk', 'wojak', 'community'],
      'hackathon': ['hackathon', '黑客松', 'bounty', '赏金', 'bug bounty', 'audit', '审计'],
      'gamefi': ['gamefi', 'x2e', '链游', 'play to earn', '边玩边赚'],
      'socialfi': ['socialfi', '社交挖矿', 'social', 'friend.tech', 'invite', '邀请码', 'referral']
    };
    
    for (let tweet of tweetElements) {
      if (results.length >= 60) break;
      
      const textEl = tweet.querySelector('[data-testid="tweetText"]');
      const nameEl = tweet.querySelector('[data-testid="User-Name"]');
      const timeEl = tweet.querySelector('time');
      const linkEl = tweet.querySelector('a[href*="/status/"]');
      
      if (textEl && nameEl) {
        const text = textEl.innerText;
        let categories = [];
        let project = null;
        let airdrop = null;
        let funding = null;
        let potentialScore = 0;
        
        // 识别类型
        for (const [category, keywords] of Object.entries(web3Keywords)) {
          if (keywords.some(kw => text.toLowerCase().includes(kw))) {
            categories.push(category);
          }
        }
        
        // 提取项目名称
        const projectMatch = text.match(/["'【]([a-zA-Z0-9\s]+)["'【】]/);
        if (projectMatch) {
          project = projectMatch[1].trim();
        }
        
        // 提取空投信息
        if (categories.includes('airdrop')) {
          const airdropPatterns = [
            /白名单[:：]\s*([a-zA-Z0-9\s]+)/,
            /claim\s*[:：]\s*([a-zA-Z0-9\s]+)/,
            /空投.*[:：]\s*([a-zA-Z0-9\s]+)/
          ];
          for (const pattern of airdropPatterns) {
            const match = text.match(pattern);
            if (match) {
              airdrop = match[1].trim();
              break;
            }
          }
        }
        
        // 提取融资信息
        if (categories.includes('funding')) {
          const fundingMatch = text.match(/([$]\s*[\d.,]+)\s*(万|million|billion|\$\s*k|\$\s*m)/i);
          if (fundingMatch) {
            funding = fundingMatch[1] + fundingMatch[2];
          }
        }
        
        // 计算潜力分数
        if (categories.includes('airdrop')) potentialScore += 3;
        if (categories.includes('new_project')) potentialScore += 2;
        if (categories.includes('funding')) potentialScore += 2;
        if (categories.includes('token') || categories.includes('coinlist')) potentialScore += 2;
        if (categories.includes('defi')) potentialScore += 1;
        if (categories.includes('nft')) potentialScore += 1;
        if (categories.includes('meme')) potentialScore += 1;
        if (categories.includes('layer2')) potentialScore += 1;
        if (categories.includes('hackathon')) potentialScore += 1;
        if (categories.includes('gamefi')) potentialScore += 1;
        
        // 项目活跃度加分
        const activityKeywords = ['testnet', '测试网', 'mainnet', '主网', '快照', 'snapshot', 'a1', 'a2', 'a3', 'alpha', 'beta'];
        if (activityKeywords.some(kw => text.toLowerCase().includes(kw))) {
          potentialScore += 2;
        }
        
        // 官方账号加分
        const officialKeywords = ['official', '官方', 'team', '团队', 'dev', '开发', 'founder', '创始人'];
        if (officialKeywords.some(kw => text.toLowerCase().includes(kw))) {
          potentialScore += 2;
        }
        
        // KOL账号加分
        const kolKeywords = ['influencer', '大v', '千万', 'follower', '粉丝', 'kols'];
        if (kolKeywords.some(kw => text.toLowerCase().includes(kw))) {
          potentialScore += 1;
        }
        
        potentialScore = Math.min(potentialScore, 10);
        
        results.push({
          text: text.substring(0, 500),
          author: nameEl.innerText,
          url: linkEl ? 'https://x.com' + linkEl.getAttribute('href') : '',
          time: timeEl ? timeEl.getAttribute('datetime') : '',
          categories,
          project,
          airdrop,
          funding,
          potentialScore
        });
      }
    }
    
    return results;
  });
  
  // 分析并筛选
  console.log(`扫描完成，共获取 ${tweets.length} 条推文`);
  
  const highPotential = tweets.filter(t => t.potentialScore >= 8);
  const mediumPotential = tweets.filter(t => 6 <= t.potentialScore < 8);
  const lowPotential = tweets.filter(t => 3 <= t.potentialScore < 6);
  
  console.log(`高潜力: ${highPotential.length} 条`);
  console.log(`中潜力: ${mediumPotential.length} 条`);
  console.log(`低潜力: ${lowPotential.length} 条`);
  
  // 生成报告
  let report = "📊 Twitter Web3热点报告\n";
  report += `📅 ${new Date().toLocaleString('zh-CN')}\n`;
  report += `🎯 共发现 ${highPotential.length + mediumPotential.length + lowPotential.length} 个Web3相关推文\n\n`;
  
  // 高潜力热点
  if (highPotential.length > 0) {
    report += "🔥🔥🔥 **高潜力热点** 🔥🔥🔥\n";
    for (let i = 0; i < Math.min(highPotential.length, 10); i++) {
      const post = highPotential[i];
      report += `\n${i+1}. ${post.project || post.author}\n`;
      report += `   潜力: ${post.potentialScore}/10\n`;
      report += `   类型: ${post.categories.join(', ')}\n`;
      report += `   内容: ${post.text.substring(0, 150)}...\n`;
      if (post.airdrop) report += `   空投: ${post.airdrop}\n`;
      if (post.funding) report += `   融资: ${post.funding}\n`;
      report += `   链接: ${post.url}\n`;
    }
    if (highPotential.length > 10) {
      report += `\n...还有 ${highPotential.length - 10} 个高潜力项目\n`;
    }
  }
  
  // 中潜力热点
  if (mediumPotential.length > 0) {
    report += "\n⭐⭐⭐ **中潜力热点** ⭐⭐⭐\n";
    for (let i = 0; i < Math.min(mediumPotential.length, 5); i++) {
      const post = mediumPotential[i];
      report += `\n${i+1}. ${post.project || post.author}\n`;
      report += `   潜力: ${post.potentialScore}/10\n`;
      report += `   类型: ${post.categories.join(', ')}\n`;
      report += `   内容: ${post.text.substring(0, 120)}...\n`;
      if (post.airdrop) report += `   空投: ${post.airdrop}\n`;
      if (post.funding) report += `   融资: ${post.funding}\n`;
      report += `   链接: ${post.url}\n`;
    }
  }
  
  // 统计信息
  report += "\n📊 **统计信息** 📊\n";
  
  const categoryCount = {};
  [...highPotential, ...mediumPotential, ...lowPotential].forEach(p => {
    p.categories.forEach(cat => {
      categoryCount[cat] = (categoryCount[cat] || 0) + 1;
    });
  });
  
  report += `空投相关: ${categoryCount.airdrop || 0}个\n`;
  report += `新项目: ${categoryCount.new_project || 0}个\n`;
  report += `融资信息: ${categoryCount.funding || 0}个\n`;
  report += `DeFi: ${categoryCount.defi || 0}个\n`;
  report += `NFT: ${categoryCount.nft || 0}个\n`;
  report += `Token: ${categoryCount.token || 0}个\n`;
  report += `Meme: ${categoryCount.meme || 0}个\n`;
  report += `Layer2: ${categoryCount.layer2 || 0}个\n`;
  report += `黑客松: ${categoryCount.hackathon || 0}个\n`;
  report += `GameFi: ${categoryCount.gamefi || 0}个\n`;
  report += `SocialFi: ${categoryCount.socialfi || 0}个\n`;
  
  // 保存数据
  const fs = require('fs');
  const dataDir = '/root/clawd/data';
  const dataFile = dataDir + '/twitter_hotspots.json';
  
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
  }
  
  const saveData = {
    scan_time: new Date().toISOString(),
    total_posts: tweets.length,
    high_potential_count: highPotential.length,
    medium_potential_count: mediumPotential.length,
    low_potential_count: lowPotential.length,
    stats: categoryCount,
    hotspots: highPotential.concat(mediumPotential)
  };
  
  fs.writeFileSync(dataFile, JSON.stringify(saveData, null, 2));
  
  console.log("\n" + "=".repeat(60));
  console.log(report);
  console.log("=".repeat(60));
  console.log(`\n✅ 数据已保存到 ${dataFile}`);
  
  console.log("\n💡 提示：");
  console.log("- 每天中午12点会自动发送报告");
  console.log("- 发送 'twitter scan' 可以立即重新扫描");
  console.log("- 发送 'send report' 可以立即发送当前数据");
  
  await browser.close();
})();
NODESCRIPT

echo ""
echo "=== 扫描完成 ==="

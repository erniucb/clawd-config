const { chromium } = require('playwright');

(async () => {
  console.log('正在启动Chrome...');
  const context = await chromium.launchPersistentContext('/root/.config/google-chrome', {
    headless: false,
    args: ['--disable-dev-shm-usage', '--no-sandbox']
  });
  
  const page = await context.newPage();
  console.log('正在访问Twitter首页（推荐流）...');
  await page.goto('https://x.com', { waitUntil: 'domcontentloaded', timeout: 30000 });
  
  await page.waitForTimeout(5000);
  
  console.log('\n正在滚动加载更多推文...');
  // 滚动5次加载更多内容
  for (let i = 0; i < 5; i++) {
    await page.evaluate(() => {
      window.scrollTo(0, document.body.scrollHeight);
    });
    await page.waitForTimeout(2000);
  }
  
  console.log('\n正在抓取推文...');
  const tweets = await page.evaluate(() => {
    const tweetElements = document.querySelectorAll('[data-testid="tweet"]');
    const results = [];
    
    for (let tweet of tweetElements) {
      const textEl = tweet.querySelector('[data-testid="tweetText"]');
      const nameEl = tweet.querySelector('[data-testid="User-Name"]');
      const timeEl = tweet.querySelector('time');
      
      if (textEl && nameEl) {
        const text = textEl.innerText;
        
        const web3Keywords = ['web3', 'crypto', 'blockchain', 'defi', 'nft', 'ethereum', 'eth', 'btc', 'bitcoin', 'solana', 'token', 'airdrop', 'yield', 'layer2', 'depin', 'restake', 'zk', 'rollup', 'meme', 'ai', 'gpt', 'llm', 'agent'];
        const isWeb3 = web3Keywords.some(kw => text.toLowerCase().includes(kw));
        
        if (isWeb3) {
          results.push({
            text: text.substring(0, 400),
            author: nameEl.innerText,
            time: timeEl ? timeEl.getAttribute('datetime') : ''
          });
        }
      }
    }
    
    return results;
  });
  
  console.log(`\n=== 共找到 ${tweets.length} 条Web3/AI相关推文 ===\n`);
  
  const displayTweets = tweets.slice(0, 10);
  displayTweets.forEach((t, i) => {
    console.log(`【${i+1}】 @${t.author}`);
    console.log(`${t.text.substring(0, 300)}`);
    console.log('');
  });
  
  console.log(`\n=== 总结 ===`);
  console.log(`总共找到 ${tweets.length} 条相关推文`);
  if (tweets.length > 0) {
    const keywords = {};
    tweets.forEach(t => {
      const text = t.text.toLowerCase();
      if (text.includes('ai') || text.includes('gpt') || text.includes('llm')) keywords['AI'] = (keywords['AI'] || 0) + 1;
      if (text.includes('crypto') || text.includes('btc') || text.includes('eth')) keywords['加密货币'] = (keywords['加密货币'] || 0) + 1;
      if (text.includes('defi') || text.includes('yield')) keywords['DeFi'] = (keywords['DeFi'] || 0) + 1;
      if (text.includes('nft') || text.includes('meme')) keywords['NFT/Meme'] = (keywords['NFT/Meme'] || 0) + 1;
    });
    
    console.log('\n主题分布：');
    Object.entries(keywords).forEach(([key, count]) => {
      console.log(`  ${key}: ${count}条`);
    });
  }
  
  console.log('\n保持浏览器运行中...');
})();

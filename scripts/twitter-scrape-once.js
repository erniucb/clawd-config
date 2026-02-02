const { chromium } = require('playwright');

(async () => {
  try {
    const context = await chromium.launchPersistentContext('/root/.config/google-chrome', {
      headless: false,
      args: ['--disable-dev-shm-usage', '--no-sandbox']
    });
    
    const page = await context.newPage();
    await page.goto('https://x.com', { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(3000);
    
    // 快速滚动
    await page.evaluate(() => {
      window.scrollTo(0, document.body.scrollHeight);
    });
    await page.waitForTimeout(2000);
    
    const tweets = await page.evaluate(() => {
      const results = [];
      const els = document.querySelectorAll('[data-testid="tweet"]');
      
      for (let tweet of els) {
        const textEl = tweet.querySelector('[data-testid="tweetText"]');
        const nameEl = tweet.querySelector('[data-testid="User-Name"]');
        
        if (textEl && nameEl) {
          const text = textEl.innerText;
          const keywords = ['web3', 'crypto', 'blockchain', 'defi', 'nft', 'ethereum', 'eth', 'btc', 'bitcoin', 'solana', 'token', 'airdrop', 'yield', 'ai', 'gpt', 'agent'];
          
          if (keywords.some(k => text.toLowerCase().includes(k))) {
            results.push({
              text: text.substring(0, 200),
              author: nameEl.innerText
            });
          }
        }
        
        if (results.length >= 5) break;
      }
      
      return results;
    });
    
    tweets.forEach((t, i) => {
      console.log(`【${i+1}】${t.author}: ${t.text}`);
    });
    
    await context.close();
  } catch (err) {
    console.log('错误:', err.message);
  }
})();

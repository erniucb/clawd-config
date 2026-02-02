const { chromium } = require('playwright');

(async () => {
  console.log('正在启动Chrome并访问推文...');
  const context = await chromium.launchPersistentContext('/root/.config/google-chrome', {
    headless: false,
    args: ['--disable-dev-shm-usage', '--no-sandbox']
  });
  
  const page = await context.newPage();
  
  console.log('等待Chrome加载...');
  await page.waitForTimeout(5000);
  
  console.log('正在访问推文链接...');
  await page.goto('https://x.com/GitHub_Daily/status/2017863068064313813', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(8000);
  
  const tweet = await page.evaluate(() => {
    const textEl = document.querySelector('[data-testid="tweetText"]');
    const nameEl = document.querySelector('[data-testid="User-Name"]');
    const timeEl = document.querySelector('time');
    
    return {
      text: textEl ? textEl.innerText : '未找到',
      author: nameEl ? nameEl.innerText : '未知'
    };
  });
  
  console.log('\n=== 推文内容 ===');
  console.log(`作者: @${tweet.author}`);
  console.log(`\n${tweet.text.substring(0, 500)}`);
  
  console.log('\nChrome保持运行中，方便下次使用...');
})();

const puppeteer = require('puppeteer');

async function detailedErrorCheck() {
  let browser;

  try {
    console.log('🔍 Running detailed error analysis for weather.westfam.media...\n');

    browser = await puppeteer.launch({
      headless: true,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--disable-gpu',
        '--enable-logging',
        '--log-level=0'
      ]
    });

    const page = await browser.newPage();

    // More detailed error tracking
    const networkRequests = [];
    const consoleMessages = [];

    page.on('request', request => {
      networkRequests.push({
        method: request.method(),
        url: request.url(),
        headers: request.headers(),
        resourceType: request.resourceType()
      });
    });

    page.on('response', response => {
      const request = networkRequests.find(req => req.url === response.url());
      if (request) {
        request.status = response.status();
        request.statusText = response.statusText();
        request.headers = response.headers();
      }
    });

    page.on('console', msg => {
      consoleMessages.push({
        type: msg.type(),
        text: msg.text(),
        location: msg.location()
      });
    });

    console.log('📡 Loading main page...');
    await page.goto('https://weather.westfam.media', {
      waitUntil: 'networkidle0',
      timeout: 30000
    });

    // Wait for any async operations
    await new Promise(resolve => setTimeout(resolve, 3000));

    // Analyze network requests
    console.log('\n🌐 NETWORK REQUEST ANALYSIS:');
    console.log('='.repeat(60));

    const failedRequests = networkRequests.filter(req => req.status >= 400);
    const successfulRequests = networkRequests.filter(req => req.status >= 200 && req.status < 400);

    console.log(`✅ Successful requests: ${successfulRequests.length}`);
    console.log(`❌ Failed requests: ${failedRequests.length}`);
    console.log(`📊 Total requests: ${networkRequests.length}\n`);

    if (failedRequests.length > 0) {
      console.log('❌ FAILED REQUESTS DETAILS:');
      failedRequests.forEach((req, index) => {
        console.log(`${index + 1}. ${req.method} ${req.url}`);
        console.log(`   Status: ${req.status} ${req.statusText}`);
        console.log(`   Type: ${req.resourceType}`);
        console.log('');
      });
    }

    // Analyze console messages
    console.log('\n🖥️  CONSOLE MESSAGE ANALYSIS:');
    console.log('='.repeat(60));

    const errorMessages = consoleMessages.filter(msg => msg.type === 'error');
    const warningMessages = consoleMessages.filter(msg => msg.type === 'warning');
    const logMessages = consoleMessages.filter(msg => msg.type === 'log');

    console.log(`❌ Errors: ${errorMessages.length}`);
    console.log(`⚠️  Warnings: ${warningMessages.length}`);
    console.log(`📝 Logs: ${logMessages.length}\n`);

    if (errorMessages.length > 0) {
      console.log('❌ ERROR MESSAGES:');
      errorMessages.forEach((msg, index) => {
        console.log(`${index + 1}. ${msg.text}`);
        if (msg.location) {
          console.log(`   Location: ${msg.location.url}:${msg.location.lineNumber}`);
        }
        console.log('');
      });
    }

    // Check specific API endpoints
    console.log('\n🏥 API ENDPOINT TESTING:');
    console.log('='.repeat(60));

    const endpoints = [
      '/healthz',
      '/goes/timeline?band=13&sector=CONUS&limit=12',
      '/mosaic/timeline?product=reflq&limit=12',
      '/indices/alerts/index.json'
    ];

    for (const endpoint of endpoints) {
      try {
        console.log(`Testing: ${endpoint}`);
        const response = await page.goto(`https://weather.westfam.media${endpoint}`, {
          waitUntil: 'networkidle0',
          timeout: 10000
        });

        console.log(`  Status: ${response.status()} ${response.statusText()}`);

        if (response.status() === 200) {
          const contentType = response.headers()['content-type'] || '';
          console.log(`  Content-Type: ${contentType}`);

          if (contentType.includes('json')) {
            try {
              const content = await page.content();
              const bodyText = await page.evaluate(() => document.body.textContent);
              const jsonData = JSON.parse(bodyText);
              console.log(`  ✅ Valid JSON response with ${Object.keys(jsonData).length} keys`);
            } catch (e) {
              console.log(`  ⚠️  Response is not valid JSON`);
            }
          }
        } else {
          console.log(`  ❌ Failed with status ${response.status()}`);
        }
        console.log('');
      } catch (error) {
        console.log(`  💥 Error: ${error.message}\n`);
      }
    }

    // Check what's actually loaded on the page
    console.log('\n📄 PAGE CONTENT ANALYSIS:');
    console.log('='.repeat(60));

    const pageInfo = await page.evaluate(() => {
      return {
        title: document.title,
        bodyHTML: document.body.innerHTML.substring(0, 500) + '...',
        scripts: Array.from(document.scripts).map(s => s.src).filter(src => src),
        stylesheets: Array.from(document.styleSheets).length,
        hasError: document.body.innerText.toLowerCase().includes('error'),
        hasLoading: document.body.innerText.toLowerCase().includes('loading'),
        reactElements: document.querySelectorAll('[data-reactroot], [data-react-helmet]').length
      };
    });

    console.log(`Title: ${pageInfo.title}`);
    console.log(`React elements: ${pageInfo.reactElements}`);
    console.log(`Stylesheets: ${pageInfo.stylesheets}`);
    console.log(`Scripts loaded: ${pageInfo.scripts.length}`);
    console.log(`Contains "error": ${pageInfo.hasError}`);
    console.log(`Contains "loading": ${pageInfo.hasLoading}`);
    console.log(`\nPage content preview:\n${pageInfo.bodyHTML}`);

  } catch (error) {
    console.error('❌ Fatal error:', error.message);
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

detailedErrorCheck();

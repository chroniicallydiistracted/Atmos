const puppeteer = require('puppeteer');

async function testWeatherSite() {
  let browser;

  try {
    console.log('🚀 Starting Puppeteer test for weather.westfam.media...\n');

    // Launch browser
    browser = await puppeteer.launch({
      headless: true,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--disable-gpu'
      ]
    });

    const page = await browser.newPage();

    // Arrays to collect errors
    const consoleErrors = [];
    const networkErrors = [];
    const jsExceptions = [];

    // Listen for console messages
    page.on('console', msg => {
      const type = msg.type();
      const text = msg.text();

      if (type === 'error') {
        consoleErrors.push(`❌ Console Error: ${text}`);
      } else if (type === 'warning') {
        console.log(`⚠️  Console Warning: ${text}`);
      } else if (type === 'log' && text.includes('error')) {
        consoleErrors.push(`❌ Console Log Error: ${text}`);
      }
    });

    // Listen for failed requests
    page.on('requestfailed', request => {
      networkErrors.push(`❌ Network Error: ${request.url()} - ${request.failure().errorText}`);
    });

    // Listen for response errors
    page.on('response', response => {
      if (response.status() >= 400) {
        networkErrors.push(`❌ HTTP ${response.status()}: ${response.url()}`);
      }
    });

    // Listen for JavaScript exceptions
    page.on('pageerror', error => {
      jsExceptions.push(`❌ JavaScript Exception: ${error.message}`);
    });

    console.log('📡 Navigating to weather.westfam.media...');

    // Navigate to the site
    const response = await page.goto('https://weather.westfam.media', {
      waitUntil: 'networkidle2',
      timeout: 30000
    });

    console.log(`📊 Initial response: ${response.status()} ${response.statusText()}`);

    // Wait a bit for any async content to load
    await new Promise(resolve => setTimeout(resolve, 5000));

    // Get page info
    const title = await page.title();
    const url = await page.url();

    console.log(`📄 Page Title: ${title}`);
    console.log(`🔗 Final URL: ${url}`);

    // Check if key elements exist
    console.log('\n🔍 Checking for key elements...');

    const hasCanvas = await page.$('canvas') !== null;
    const hasMapContainer = await page.$('.maplibregl-map, .mapboxgl-map, #map') !== null;
    const hasReactRoot = await page.$('#root, [data-reactroot]') !== null;

    console.log(`🗺️  Map canvas found: ${hasCanvas ? '✅' : '❌'}`);
    console.log(`📦 Map container found: ${hasMapContainer ? '✅' : '❌'}`);
    console.log(`⚛️  React root found: ${hasReactRoot ? '✅' : '❌'}`);

    // Check for specific weather app elements
    const weatherElements = await page.evaluate(() => {
      const elements = {
        timeSlider: document.querySelector('[class*="time"], [class*="slider"]') !== null,
        layerToggle: document.querySelector('[class*="layer"], [class*="toggle"]') !== null,
        legend: document.querySelector('[class*="legend"]') !== null,
        controls: document.querySelector('[class*="control"]') !== null
      };
      return elements;
    });

    console.log(`⏱️  Time controls: ${weatherElements.timeSlider ? '✅' : '❌'}`);
    console.log(`🎛️  Layer controls: ${weatherElements.layerToggle ? '✅' : '❌'}`);
    console.log(`📊 Legend: ${weatherElements.legend ? '✅' : '❌'}`);
    console.log(`🎮 Other controls: ${weatherElements.controls ? '✅' : '❌'}`);

    // Test health endpoint
    console.log('\n🏥 Testing health endpoint...');
    try {
      const healthResponse = await page.goto('https://weather.westfam.media/healthz', {
        waitUntil: 'networkidle2',
        timeout: 10000
      });

      console.log(`📊 Health endpoint: ${healthResponse.status()} ${healthResponse.statusText()}`);

      if (healthResponse.status() === 200) {
        const healthContent = await page.content();
        if (healthContent.includes('json')) {
          const healthData = await page.evaluate(() => document.body.textContent);
          console.log(`💚 Health data: ${healthData.substring(0, 200)}...`);
        }
      }
    } catch (error) {
      console.log(`❌ Health endpoint error: ${error.message}`);
    }

    // Test status page
    console.log('\n📈 Testing status page...');
    try {
      const statusResponse = await page.goto('https://weather.westfam.media/status.html', {
        waitUntil: 'networkidle2',
        timeout: 10000
      });

      console.log(`📊 Status page: ${statusResponse.status()} ${statusResponse.statusText()}`);
    } catch (error) {
      console.log(`❌ Status page error: ${error.message}`);
    }

    // Performance metrics
    console.log('\n⚡ Performance metrics...');
    const performanceMetrics = await page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0];
      return {
        loadTime: Math.round(navigation.loadEventEnd - navigation.fetchStart),
        domContentLoaded: Math.round(navigation.domContentLoadedEventEnd - navigation.fetchStart),
        firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0,
        firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0
      };
    });

    console.log(`⏱️  Total load time: ${performanceMetrics.loadTime}ms`);
    console.log(`📄 DOM content loaded: ${performanceMetrics.domContentLoaded}ms`);
    console.log(`🎨 First paint: ${Math.round(performanceMetrics.firstPaint)}ms`);
    console.log(`🖼️  First contentful paint: ${Math.round(performanceMetrics.firstContentfulPaint)}ms`);

    // Report all errors
    console.log('\n📋 ERROR SUMMARY:');
    console.log('='.repeat(50));

    if (consoleErrors.length === 0 && networkErrors.length === 0 && jsExceptions.length === 0) {
      console.log('🎉 No errors found! Site appears to be working correctly.');
    } else {
      if (consoleErrors.length > 0) {
        console.log('\n🖥️  CONSOLE ERRORS:');
        consoleErrors.forEach(error => console.log(error));
      }

      if (networkErrors.length > 0) {
        console.log('\n🌐 NETWORK ERRORS:');
        networkErrors.forEach(error => console.log(error));
      }

      if (jsExceptions.length > 0) {
        console.log('\n💥 JAVASCRIPT EXCEPTIONS:');
        jsExceptions.forEach(error => console.log(error));
      }

      console.log(`\n📊 Total errors found: ${consoleErrors.length + networkErrors.length + jsExceptions.length}`);
    }

  } catch (error) {
    console.error('❌ Fatal error during testing:', error.message);
    if (error.message.includes('net::ERR_NAME_NOT_RESOLVED')) {
      console.log('🔍 This might mean the domain is not accessible or DNS is not resolving.');
    } else if (error.message.includes('timeout')) {
      console.log('⏰ The site took too long to load (>30 seconds).');
    }
  } finally {
    if (browser) {
      await browser.close();
    }
    console.log('\n✅ Test completed.');
  }
}

// Run the test
testWeatherSite();

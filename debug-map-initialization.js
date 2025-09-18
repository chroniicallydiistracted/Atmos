const puppeteer = require('puppeteer');

async function debugMapInitialization() {
  let browser;

  try {
    console.log('🔍 DEBUGGING MAP INITIALIZATION');
    console.log('===============================\n');

    browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
      devtools: false
    });

    const page = await browser.newPage();
    await page.setViewport({ width: 1200, height: 800 });

    // Collect ALL console messages
    const consoleMessages = [];
    page.on('console', msg => {
      const type = msg.type();
      const text = msg.text();
      const location = msg.location();
      consoleMessages.push({
        type,
        text,
        url: location.url,
        line: location.lineNumber
      });
    });

    // Collect ALL network requests
    const networkRequests = [];
    page.on('request', request => {
      networkRequests.push({
        method: request.method(),
        url: request.url(),
        resourceType: request.resourceType(),
        headers: request.headers(),
        status: 'pending'
      });
    });

    page.on('response', response => {
      const req = networkRequests.find(r => r.url === response.url());
      if (req) {
        req.status = response.status();
        req.statusText = response.statusText();
        req.responseHeaders = response.headers();
        req.contentType = response.headers()['content-type'];
      }
    });

    page.on('requestfailed', request => {
      const req = networkRequests.find(r => r.url === request.url());
      if (req) {
        req.status = 'FAILED';
        req.errorText = request.failure().errorText;
      }
    });

    console.log('📡 Loading weather.westfam.media with detailed monitoring...\n');

    const response = await page.goto('https://weather.westfam.media', {
      waitUntil: 'networkidle2',
      timeout: 30000
    });

    console.log(`Initial Response: ${response.status()} ${response.statusText()}\n`);

    // Wait for potential async operations
    console.log('⏱️  Waiting for map initialization...');
    await new Promise(resolve => setTimeout(resolve, 10000));

    // Get detailed page state
    const pageState = await page.evaluate(() => {
      return {
        // Document state
        title: document.title,
        readyState: document.readyState,

        // React/DOM state
        hasReactRoot: !!document.querySelector('#root'),
        rootInnerHTML: document.querySelector('#root')?.innerHTML?.substring(0, 500) || 'NO ROOT',

        // Map library availability
        hasMapLibre: typeof window.maplibregl !== 'undefined',
        mapLibreVersion: typeof window.maplibregl !== 'undefined' ? window.maplibregl.version : null,
        hasPMTiles: typeof window.PMTiles !== 'undefined',
        pmtilesVersion: typeof window.PMTiles !== 'undefined' ? window.PMTiles.version : null,

        // Map DOM elements
        hasCanvas: !!document.querySelector('canvas'),
        canvasCount: document.querySelectorAll('canvas').length,
        mapContainers: Array.from(document.querySelectorAll('div')).filter(div =>
          div.className.includes('map') || div.id.includes('map')
        ).length,

        // All divs for debugging
        allDivs: Array.from(document.querySelectorAll('div')).map(div => ({
          id: div.id,
          className: div.className,
          hasChildren: div.children.length > 0,
          textContent: div.textContent?.substring(0, 100) || ''
        })),

        // Check for specific errors
        bodyText: document.body.textContent,
        hasErrorText: document.body.textContent.toLowerCase().includes('error'),

        // Check window object for debugging
        windowKeys: Object.keys(window).filter(key => key.includes('map') || key.includes('Map')),

        // Script tags
        scripts: Array.from(document.scripts).map(script => ({
          src: script.src,
          type: script.type,
          async: script.async,
          defer: script.defer
        }))
      };
    });

    console.log('📄 PAGE STATE ANALYSIS:');
    console.log('========================');
    console.log(`Title: ${pageState.title}`);
    console.log(`Ready State: ${pageState.readyState}`);
    console.log(`React Root: ${pageState.hasReactRoot ? '✅' : '❌'}`);
    console.log(`MapLibre Available: ${pageState.hasMapLibre ? '✅' : '❌'} ${pageState.mapLibreVersion || ''}`);
    console.log(`PMTiles Available: ${pageState.hasPMTiles ? '✅' : '❌'} ${pageState.pmtilesVersion || ''}`);
    console.log(`Canvas Elements: ${pageState.canvasCount}`);
    console.log(`Map Containers: ${pageState.mapContainers}`);
    console.log(`Scripts Loaded: ${pageState.scripts.length}`);
    console.log(`Has Error Text: ${pageState.hasErrorText ? '❌ YES' : '✅ NO'}`);

    console.log(`\\nRoot Content Preview: ${pageState.rootInnerHTML}\\n`);

    console.log('🔍 ALL DIV ELEMENTS:');
    pageState.allDivs.forEach((div, i) => {
      if (i < 10) { // Only show first 10
        console.log(`  ${i}: id="${div.id}" class="${div.className}" children=${div.hasChildren}`);
      }
    });

    console.log('\\n🖥️  CONSOLE MESSAGES:');
    console.log('======================');
    consoleMessages.forEach((msg, i) => {
      console.log(`${i + 1}. [${msg.type}] ${msg.text}`);
      if (msg.url && !msg.url.includes('data:')) {
        console.log(`   Location: ${msg.url}:${msg.line}`);
      }
    });

    console.log('\\n🌐 NETWORK REQUESTS:');
    console.log('=====================');

    const failed = networkRequests.filter(req => req.status >= 400 || req.status === 'FAILED');
    const pending = networkRequests.filter(req => req.status === 'pending');
    const successful = networkRequests.filter(req => req.status >= 200 && req.status < 400);

    console.log(`Total Requests: ${networkRequests.length}`);
    console.log(`Successful: ${successful.length}`);
    console.log(`Failed: ${failed.length}`);
    console.log(`Pending: ${pending.length}\\n`);

    if (failed.length > 0) {
      console.log('❌ FAILED REQUESTS:');
      failed.forEach(req => {
        console.log(`  ${req.method} ${req.url}`);
        console.log(`  Status: ${req.status} ${req.statusText || req.errorText}`);
        console.log(`  Type: ${req.resourceType}`);
        console.log('');
      });
    }

    if (pending.length > 0) {
      console.log('⏳ PENDING REQUESTS:');
      pending.forEach(req => {
        console.log(`  ${req.method} ${req.url} (${req.resourceType})`);
      });
      console.log('');
    }

    // Check specific critical resources
    console.log('🎯 CRITICAL RESOURCE CHECK:');
    console.log('============================');

    const criticalResources = [
      '/styles/cyclosm.json',
      '/basemaps/planet.z15.pmtiles',
      '/sprites/cyclosm/cyclosm.json',
      '/sprites/cyclosm/cyclosm.png',
      'maplibre-gl',
      'pmtiles'
    ];

    criticalResources.forEach(resource => {
      const request = networkRequests.find(req => req.url.includes(resource));
      if (request) {
        const status = request.status === 'pending' ? '⏳ PENDING' :
                      request.status >= 200 && request.status < 400 ? `✅ ${request.status}` :
                      `❌ ${request.status}`;
        console.log(`${status}: ${resource}`);
      } else {
        console.log(`❓ NOT REQUESTED: ${resource}`);
      }
    });

    console.log('\\n🎯 DIAGNOSIS:');
    console.log('==============');

    if (!pageState.hasReactRoot) {
      console.log('❌ CRITICAL: React root not found - app not mounting');
    } else if (!pageState.hasMapLibre) {
      console.log('❌ CRITICAL: MapLibre not available - library not loading');
    } else if (!pageState.hasPMTiles) {
      console.log('❌ CRITICAL: PMTiles not available - dependency missing');
    } else if (pageState.canvasCount === 0) {
      console.log('❌ CRITICAL: No canvas elements - map not rendering');
    } else {
      console.log('✅ Basic structure appears correct, checking for runtime errors...');
    }

  } catch (error) {
    console.error('❌ Fatal error during debugging:', error.message);
  } finally {
    if (browser) await browser.close();
  }
}

debugMapInitialization();

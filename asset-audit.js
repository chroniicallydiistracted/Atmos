const puppeteer = require('puppeteer');

async function auditMissingAssets() {
  let browser;

  try {
    console.log('🔍 COMPREHENSIVE STATIC ASSET AUDIT');
    console.log('=====================================\n');

    browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();

    // Track all requests and their results
    const assetRequests = [];

    page.on('request', request => {
      assetRequests.push({
        url: request.url(),
        method: request.method(),
        resourceType: request.resourceType(),
        status: 'pending'
      });
    });

    page.on('response', response => {
      const asset = assetRequests.find(a => a.url === response.url());
      if (asset) {
        asset.status = response.status();
        asset.statusText = response.statusText();
        asset.contentType = response.headers()['content-type'];
        asset.contentLength = response.headers()['content-length'];
      }
    });

    page.on('requestfailed', request => {
      const asset = assetRequests.find(a => a.url === request.url());
      if (asset) {
        asset.status = 'failed';
        asset.error = request.failure().errorText;
      }
    });

    console.log('📡 Loading weather.westfam.media...\n');
    await page.goto('https://weather.westfam.media', {
      waitUntil: 'networkidle0',
      timeout: 30000
    });

    // Wait for any additional async requests
    await new Promise(resolve => setTimeout(resolve, 5000));

    // Categorize assets
    const staticAssets = assetRequests.filter(a =>
      a.resourceType === 'stylesheet' ||
      a.resourceType === 'script' ||
      a.resourceType === 'image' ||
      a.resourceType === 'font' ||
      a.url.includes('.pmtiles') ||
      a.url.includes('.json') ||
      a.url.includes('sprite') ||
      a.url.includes('basemap')
    );

    const apiRequests = assetRequests.filter(a =>
      a.resourceType === 'fetch' ||
      a.url.includes('/api/') ||
      a.url.includes('timeline') ||
      a.url.includes('healthz')
    );

    const failedAssets = staticAssets.filter(a => a.status >= 400 || a.status === 'failed');
    const missingCritical = [];

    console.log('📊 ASSET SUMMARY:');
    console.log(`Total requests: ${assetRequests.length}`);
    console.log(`Static assets: ${staticAssets.length}`);
    console.log(`API requests: ${apiRequests.length}`);
    console.log(`Failed assets: ${failedAssets.length}\n`);

    // Check for critical missing assets
    const criticalAssets = [
      '/basemaps/planet.z15.pmtiles',
      '/sprites/cyclosm/cyclosm.json',
      '/sprites/cyclosm/cyclosm.png',
      '/styles/cyclosm.json',
      '/favicon.svg',
      '/favicon.ico'
    ];

    console.log('🚨 CRITICAL ASSETS CHECK:');
    console.log('========================');

    for (const critical of criticalAssets) {
      const found = assetRequests.find(a => a.url.includes(critical));
      if (!found) {
        missingCritical.push(`❌ NOT REQUESTED: ${critical}`);
        console.log(`❌ NOT REQUESTED: ${critical}`);
      } else if (found.status >= 400 || found.status === 'failed') {
        missingCritical.push(`❌ ${found.status}: ${critical}`);
        console.log(`❌ ${found.status}: ${critical}`);
      } else {
        console.log(`✅ ${found.status}: ${critical}`);
      }
    }

    if (failedAssets.length > 0) {
      console.log('\n💥 ALL FAILED ASSETS:');
      console.log('=====================');
      failedAssets.forEach(asset => {
        console.log(`❌ ${asset.status} ${asset.url}`);
        console.log(`   Type: ${asset.resourceType}`);
        if (asset.error) console.log(`   Error: ${asset.error}`);
        console.log('');
      });
    }

    // Check what's actually in the web-static directory
    console.log('\n📁 EXPECTED VS ACTUAL ASSETS:');
    console.log('==============================');

    // Test direct S3 bucket access patterns
    const expectedPaths = [
      'https://weather.westfam.media/basemaps/planet.z15.pmtiles',
      'https://weather.westfam.media/styles/cyclosm.json',
      'https://weather.westfam.media/sprites/cyclosm/cyclosm.json',
      'https://weather.westfam.media/sprites/cyclosm/cyclosm.png'
    ];

    for (const path of expectedPaths) {
      try {
        const response = await page.goto(path, { timeout: 5000 });
        console.log(`${response.status() === 200 ? '✅' : '❌'} ${response.status()}: ${path}`);
      } catch (error) {
        console.log(`❌ ERROR: ${path} - ${error.message}`);
      }
    }

    // Check current S3 bucket structure through HTML
    console.log('\n🌐 FRONTEND MAP INITIALIZATION:');
    console.log('===============================');

    const mapInfo = await page.evaluate(() => {
      // Check for MapLibre/Mapbox
      const hasMapLibre = typeof window.maplibregl !== 'undefined';
      const hasMapbox = typeof window.mapboxgl !== 'undefined';

      // Check for map container
      const mapContainer = document.querySelector('#map, .map, .maplibregl-map, .mapboxgl-map');

      // Check for any error messages in console or DOM
      const errorElements = Array.from(document.querySelectorAll('*')).filter(el =>
        el.textContent && el.textContent.toLowerCase().includes('error')
      );

      return {
        hasMapLibre,
        hasMapbox,
        mapContainer: mapContainer ? mapContainer.id || mapContainer.className : null,
        errorMessages: errorElements.map(el => el.textContent.substring(0, 100))
      };
    });

    console.log(`Map Library - MapLibre: ${mapInfo.hasMapLibre ? '✅' : '❌'}`);
    console.log(`Map Library - Mapbox: ${mapInfo.hasMapbox ? '✅' : '❌'}`);
    console.log(`Map Container: ${mapInfo.mapContainer || '❌ Not found'}`);
    console.log(`DOM Errors: ${mapInfo.errorMessages.length}`);

    if (mapInfo.errorMessages.length > 0) {
      console.log('\n📝 DOM ERROR MESSAGES:');
      mapInfo.errorMessages.forEach(msg => console.log(`  - ${msg}`));
    }

    console.log('\n🎯 DIAGNOSIS SUMMARY:');
    console.log('====================');
    console.log(`Critical missing assets: ${missingCritical.length}`);
    console.log(`Failed asset requests: ${failedAssets.length}`);
    console.log(`Map library loaded: ${mapInfo.hasMapLibre || mapInfo.hasMapbox ? '✅' : '❌'}`);

  } catch (error) {
    console.error('❌ Audit error:', error.message);
  } finally {
    if (browser) await browser.close();
  }
}

auditMissingAssets();

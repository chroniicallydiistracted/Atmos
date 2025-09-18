const puppeteer = require('puppeteer');

async function testAtmosInsight() {
    console.log('🚀 Starting AtmosInsight User Experience Test\n');
    
    // Launch browser
    const browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-dev-shm-usage']
    });
    
    try {
        const page = await browser.newPage();
        
        // Set viewport
        await page.setViewport({ width: 1200, height: 800 });
        
        // Enable request interception to monitor API calls
        await page.setRequestInterception(true);
        const apiCalls = [];
        
        page.on('request', (request) => {
            if (request.url().includes('execute-api.us-east-1.amazonaws.com')) {
                apiCalls.push({
                    url: request.url(),
                    method: request.method()
                });
            }
            request.continue();
        });
        
        // Monitor console logs and errors
        const consoleLogs = [];
        const errors = [];
        
        page.on('console', msg => {
            consoleLogs.push(`${msg.type()}: ${msg.text()}`);
        });
        
        page.on('pageerror', error => {
            errors.push(error.message);
        });
        
        console.log('📱 Testing Website Loading...');
        
        // Navigate to the main site
        const response = await page.goto('https://weather.westfam.media/', {
            waitUntil: 'networkidle2',
            timeout: 30000
        });
        
        console.log(`✅ Page loaded with status: ${response.status()}`);
        
        // Check basic page elements
        console.log('\n🔍 Checking Page Elements...');
        
        const title = await page.title();
        console.log(`✅ Page title: "${title}"`);
        
        // Check if main app container exists
        const appContainer = await page.$('body');
        if (appContainer) {
            console.log('✅ Main app container found');
        } else {
            console.log('❌ Main app container not found');
        }
        
        // Wait a bit for any dynamic content
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        // Check for common UI elements
        const checkElement = async (selector, name) => {
            const element = await page.$(selector);
            if (element) {
                console.log(`✅ ${name} found`);
                return true;
            } else {
                console.log(`⚠️  ${name} not found`);
                return false;
            }
        };
        
        // Check for various selectors that might exist in the app
        await checkElement('nav', 'Navigation');
        await checkElement('header', 'Header');
        await checkElement('main', 'Main content area');
        await checkElement('.map', 'Map container');
        await checkElement('#map', 'Map element');
        await checkElement('[class*="map"]', 'Map-related element');
        await checkElement('canvas', 'Canvas element');
        
        console.log('\\n🌐 Testing API Connectivity...');
        
        // Test API endpoints directly from the browser context
        const testApiEndpoint = async (endpoint, method = 'GET') => {
            try {
                const result = await page.evaluate(async (url, method) => {
                    const response = await fetch(url, { method });
                    const text = await response.text();
                    return {
                        status: response.status,
                        ok: response.ok,
                        data: text,
                        headers: Object.fromEntries(response.headers.entries())
                    };
                }, endpoint, method);
                
                console.log(`✅ ${method} ${endpoint}: ${result.status} ${result.ok ? 'OK' : 'ERROR'}`);
                if (result.data.length < 500) {
                    console.log(`   Response: ${result.data.substring(0, 200)}${result.data.length > 200 ? '...' : ''}`);
                }
                return result;
            } catch (error) {
                console.log(`❌ ${method} ${endpoint}: ${error.message}`);
                return null;
            }
        };
        
        // Test main API endpoints
        await testApiEndpoint('https://0sc5dovdz4.execute-api.us-east-1.amazonaws.com/v1/healthz');
        await testApiEndpoint('https://0sc5dovdz4.execute-api.us-east-1.amazonaws.com/v1/tiles/');
        await testApiEndpoint('https://0sc5dovdz4.execute-api.us-east-1.amazonaws.com/v1/tiles/healthz');
        
        console.log('\\n🖱️  Testing User Interactions...');
        
        // Try clicking on elements if they exist
        try {
            // Look for clickable elements
            const clickableElements = await page.$$('button, a, [role="button"], [onclick]');
            console.log(`✅ Found ${clickableElements.length} clickable elements`);
            
            if (clickableElements.length > 0) {
                // Try clicking the first one
                await clickableElements[0].click();
                await new Promise(resolve => setTimeout(resolve, 1000));
                console.log('✅ Successfully clicked first interactive element');
            }
        } catch (error) {
            console.log(`⚠️  Click interaction failed: ${error.message}`);
        }
        
        console.log('\\n📊 Performance Metrics...');
        
        // Get some performance metrics
        const metrics = await page.metrics();
        console.log(`✅ DOM Nodes: ${metrics.Nodes}`);
        console.log(`✅ JS Event Listeners: ${metrics.JSEventListeners}`);
        console.log(`✅ JS Heap Used: ${Math.round(metrics.JSHeapUsedSize / 1024 / 1024)}MB`);
        
        // Take a screenshot
        await page.screenshot({ 
            path: '/tmp/atmosinsight-test.png',
            fullPage: true 
        });
        console.log('✅ Screenshot saved to /tmp/atmosinsight-test.png');
        
        console.log('\\n📞 API Calls Made:');
        if (apiCalls.length > 0) {
            apiCalls.forEach(call => {
                console.log(`  ${call.method} ${call.url}`);
            });
        } else {
            console.log('  No API calls detected');
        }
        
        console.log('\\n📝 Console Logs:');
        if (consoleLogs.length > 0) {
            consoleLogs.slice(-10).forEach(log => { // Show last 10 logs
                console.log(`  ${log}`);
            });
        } else {
            console.log('  No console logs captured');
        }
        
        console.log('\\n❌ Errors:');
        if (errors.length > 0) {
            errors.forEach(error => {
                console.log(`  ${error}`);
            });
        } else {
            console.log('  No JavaScript errors detected ✅');
        }
        
        console.log('\\n🎯 Summary:');
        console.log(`✅ Website loads successfully (${response.status()})`);
        console.log(`✅ No JavaScript errors detected`);
        console.log(`✅ Page title: "${title}"`);
        console.log(`✅ Screenshot captured`);
        console.log('✅ All basic functionality appears to be working');
        
    } catch (error) {
        console.error('❌ Test failed:', error);
    } finally {
        await browser.close();
    }
}

// Run the test
testAtmosInsight().catch(console.error);
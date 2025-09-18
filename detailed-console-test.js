const puppeteer = require('puppeteer');

async function detailedConsoleTest() {
    console.log('🔍 Detailed Console Output Analysis');
    console.log('==================================\n');
    
    const browser = await puppeteer.launch({ 
        headless: true,
        args: ['--no-sandbox', '--disable-dev-shm-usage']
    });
    
    try {
        const page = await browser.newPage();
        
        // Comprehensive console monitoring
        const consoleMessages = [];
        const errors = [];
        const warnings = [];
        const networkErrors = [];
        const apiCalls = [];
        
        // Capture all console output with full details
        page.on('console', msg => {
            const logEntry = {
                type: msg.type(),
                text: msg.text(),
                location: msg.location(),
                timestamp: new Date().toISOString(),
                args: msg.args()
            };
            
            consoleMessages.push(logEntry);
            
            // Categorize messages
            if (msg.type() === 'error') {
                errors.push(logEntry);
            } else if (msg.type() === 'warning') {
                warnings.push(logEntry);
            }
            
            // Real-time output
            const prefix = {
                'error': '❌',
                'warning': '⚠️',
                'info': 'ℹ️',
                'log': '📝',
                'debug': '🐛'
            }[msg.type()] || '📄';
            
            console.log(`${prefix} [${msg.type().toUpperCase()}] ${msg.text()}`);
        });
        
        // Capture page errors (JavaScript exceptions)
        page.on('pageerror', error => {
            console.log(`💥 [PAGE ERROR] ${error.message}`);
            errors.push({
                type: 'pageerror',
                text: error.message,
                stack: error.stack,
                timestamp: new Date().toISOString()
            });
        });
        
        // Monitor network for failed requests
        page.on('response', response => {
            if (response.status() >= 400) {
                const errorEntry = {
                    url: response.url(),
                    status: response.status(),
                    statusText: response.statusText(),
                    timestamp: new Date().toISOString()
                };
                networkErrors.push(errorEntry);
                console.log(`🌐 [NETWORK ERROR] ${response.status()} ${response.url()}`);
            }
            
            // Track API calls specifically
            if (response.url().includes('execute-api.us-east-1.amazonaws.com')) {
                apiCalls.push({
                    url: response.url(),
                    status: response.status(),
                    method: response.request().method(),
                    timestamp: new Date().toISOString()
                });
                console.log(`🔌 [API] ${response.request().method()} ${response.status()} ${response.url()}`);
            }
        });
        
        console.log('🌐 Loading AtmosInsight with detailed monitoring...\n');
        
        await page.goto('https://weather.westfam.media/', {
            waitUntil: 'networkidle2',
            timeout: 30000
        });
        
        console.log('\n⏱️  Waiting for dynamic content and API calls...');
        await new Promise(resolve => setTimeout(resolve, 5000));
        
        console.log('\n📊 CONSOLE ANALYSIS SUMMARY');
        console.log('===========================');
        
        console.log(`\n📝 Total Console Messages: ${consoleMessages.length}`);
        console.log(`❌ Errors: ${errors.length}`);
        console.log(`⚠️  Warnings: ${warnings.length}`);
        console.log(`🌐 Network Errors: ${networkErrors.length}`);
        console.log(`🔌 API Calls: ${apiCalls.length}`);
        
        if (errors.length > 0) {
            console.log('\n❌ DETAILED ERROR ANALYSIS:');
            console.log('============================');
            errors.forEach((error, index) => {
                console.log(`\n${index + 1}. [${error.type}] ${error.timestamp}`);
                console.log(`   Message: ${error.text}`);
                if (error.location) {
                    console.log(`   Location: ${JSON.stringify(error.location)}`);
                }
                if (error.stack) {
                    console.log(`   Stack: ${error.stack.substring(0, 200)}...`);
                }
            });
        }
        
        if (networkErrors.length > 0) {
            console.log('\n🌐 NETWORK ERRORS:');
            console.log('==================');
            networkErrors.forEach((err, index) => {
                console.log(`${index + 1}. ${err.status} ${err.statusText} - ${err.url}`);
            });
        }
        
        if (apiCalls.length > 0) {
            console.log('\n🔌 API CALL DETAILS:');
            console.log('===================');
            apiCalls.forEach((call, index) => {
                const status = call.status >= 200 && call.status < 300 ? '✅' : '❌';
                console.log(`${index + 1}. ${status} ${call.method} ${call.status} ${call.url.split('.com')[1]}`);
            });
        }
        
        // Check for specific application behaviors
        console.log('\n🎯 APPLICATION BEHAVIOR ANALYSIS:');
        console.log('=================================');
        
        const appStatus = await page.evaluate(() => {
            return {
                hasMapLibrary: typeof window.mapboxgl !== 'undefined' || typeof window.L !== 'undefined' || typeof window.ol !== 'undefined',
                hasReact: typeof window.React !== 'undefined',
                hasVue: typeof window.Vue !== 'undefined',
                windowVars: Object.keys(window).filter(key => !key.startsWith('webkit') && !key.startsWith('chrome')).slice(0, 20),
                documentReadyState: document.readyState,
                bodyClasses: document.body.className,
                metaTags: Array.from(document.querySelectorAll('meta')).map(m => ({ name: m.name, content: m.content?.substring(0, 50) })).slice(0, 5)
            };
        });
        
        console.log(`Document Ready State: ${appStatus.documentReadyState}`);
        console.log(`Body Classes: ${appStatus.bodyClasses}`);
        console.log(`Has Map Library: ${appStatus.hasMapLibrary}`);
        console.log(`Has React: ${appStatus.hasReact}`);
        console.log(`Has Vue: ${appStatus.hasVue}`);
        console.log(`Window Variables: ${appStatus.windowVars.slice(0, 10).join(', ')}`);
        
        // Test some user interactions
        console.log('\n🖱️  TESTING USER INTERACTIONS:');
        console.log('==============================');
        
        try {
            const clickableElements = await page.$$('button, [role="button"], .leaflet-control-zoom-in, .leaflet-control-zoom-out');
            console.log(`Found ${clickableElements.length} clickable elements`);
            
            if (clickableElements.length > 0) {
                await clickableElements[0].click();
                await new Promise(resolve => setTimeout(resolve, 1000));
                console.log('✅ Successfully clicked first element');
            }
        } catch (error) {
            console.log(`❌ Click interaction failed: ${error.message}`);
        }
        
        console.log('\n🎯 FINAL ASSESSMENT:');
        console.log('====================');
        console.log(`✅ Application loaded: ${errors.filter(e => e.type === 'pageerror').length === 0 ? 'SUCCESS' : 'WITH ERRORS'}`);
        console.log(`✅ API connectivity: ${apiCalls.filter(c => c.status >= 200 && c.status < 300).length}/${apiCalls.length} successful`);
        console.log(`✅ Critical errors: ${errors.filter(e => e.text.includes('Uncaught') || e.type === 'pageerror').length}`);
        console.log(`⚠️  Non-critical errors: ${errors.length - errors.filter(e => e.text.includes('Uncaught') || e.type === 'pageerror').length}`);
        
    } catch (error) {
        console.error('❌ Test failed:', error);
    } finally {
        await browser.close();
    }
}

detailedConsoleTest().catch(console.error);
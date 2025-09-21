const puppeteer = require('puppeteer');

async function describeArg(arg) {
  try {
    return await arg.executionContext().evaluate((value) => {
      if (value instanceof Error) {
        return `${value.name}: ${value.message}`;
      }
      if (typeof value === 'object' && value !== null) {
        try {
          return JSON.stringify(value);
        } catch (err) {
          return Object.prototype.toString.call(value);
        }
      }
      return String(value);
    }, arg);
  } catch (error) {
    try {
      const json = await arg.jsonValue();
      return typeof json === 'object' ? JSON.stringify(json) : String(json);
    } catch (err) {
      return arg.toString();
    }
  }
}

async function run() {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-dev-shm-usage']
  });

  const page = await browser.newPage();
  const consoleLogs = [];
  const requestErrors = [];
  const pageErrors = [];
  const badResponses = [];

  page.on('console', async (msg) => {
    const parts = [];
    for (const arg of msg.args()) {
      parts.push(await describeArg(arg));
    }
    consoleLogs.push({ type: msg.type(), text: parts.join(' ') });
  });
  page.on('pageerror', (err) => {
    pageErrors.push(err.message);
  });
  page.on('requestfailed', (req) => {
    requestErrors.push({ url: req.url(), errorText: req.failure()?.errorText || 'unknown' });
  });
  page.on('response', async (res) => {
    const status = res.status();
    if (status >= 400) {
      badResponses.push({ url: res.url(), status, statusText: res.statusText() });
    }
  });

  await page.goto('http://localhost:4173/', { waitUntil: 'networkidle0', timeout: 60000 });

  const mapPresent = await page.evaluate(() => {
    const canvas = document.querySelector('.maplibregl-canvas');
    if (!canvas) {
      return { hasCanvas: false };
    }
    const { width, height } = canvas;
    let sample = null;
    try {
      const ctx = canvas.getContext('2d');
      if (ctx && width > 0 && height > 0) {
        const data = ctx.getImageData(Math.floor(width / 2), Math.floor(height / 2), 1, 1).data;
        sample = Array.from(data);
      }
    } catch (err) {
      sample = `unavailable: ${err.message}`;
    }
    return {
      hasCanvas: true,
      width,
      height,
      sample
    };
  });

  await page.screenshot({ path: '/tmp/basemap-check.png', fullPage: true });

  await browser.close();

  return { mapPresent, consoleLogs, pageErrors, requestErrors, badResponses };
}

run()
  .then((result) => {
    console.log(JSON.stringify(result, null, 2));
  })
  .catch((error) => {
    console.error('check-basemap failed', error);
    process.exitCode = 1;
  });

#!/usr/bin/env node
import https from 'https';

const URL = process.env.TILE_URL || 'https://weather.westfam.media/tiles/cyclosm/5/5/12.png';

function fetch(url){
  return new Promise((resolve,reject)=>{
    const t0=Date.now();
    https.get(url, res => {
      const chunks=[]; res.on('data', c=>chunks.push(c));
      res.on('end', ()=>{
        const t1=Date.now();
        resolve({ status: res.statusCode, headers: res.headers, ms: t1-t0, size: Buffer.concat(chunks).length });
      });
    }).on('error', reject);
  });
}

(async ()=>{
  const first = await fetch(URL);
  const second = await fetch(URL);
  console.log(JSON.stringify({ first, second }, null, 2));
})();

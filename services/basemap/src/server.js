import fs from 'fs';
import path from 'path';
import express from 'express';
import cors from 'cors';
import rangeParser from 'range-parser';

import { config } from './config.js';

const app = express();

app.use(
  cors({
    origin: (origin, callback) => {
      if (!origin || config.corsOrigins.includes(origin)) {
        return callback(null, true);
      }
      return callback(new Error(`Origin ${origin} not permitted`));
    },
    credentials: false,
  })
);

function fileFor(name) {
  const safeName = path.basename(name);
  return path.join(config.dataDir, safeName);
}

function listPmtiles() {
  if (!fs.existsSync(config.dataDir)) {
    return [];
  }
  return fs
    .readdirSync(config.dataDir)
    .filter((name) => name.endsWith('.pmtiles'))
    .map((name) => ({
      name,
      path: `/pmtiles/${name}`,
    }));
}

app.get('/healthz', (req, res) => {
  const entries = listPmtiles();
  res.json({
    status: 'ok',
    pmtilesCount: entries.length,
    default: config.defaultPmtiles,
  });
});

app.get('/pmtiles', (req, res) => {
  res.json({
    files: listPmtiles(),
  });
});

function streamFile(filePath, req, res) {
  const stat = fs.statSync(filePath);
  const total = stat.size;
  const rangeHeader = req.headers.range;

  if (rangeHeader) {
    const ranges = rangeParser(total, rangeHeader, { combine: true });
    if (ranges === -1) {
      res.status(416).set('Content-Range', `bytes */${total}`).end();
      return;
    }
    const { start, end } = ranges[0];
    res.status(206);
    res.set({
      'Content-Length': end - start + 1,
      'Content-Range': `bytes ${start}-${end}/${total}`,
      'Accept-Ranges': 'bytes',
      'Content-Type': 'application/octet-stream',
      'Cache-Control': 'public, max-age=3600',
    });
    fs.createReadStream(filePath, { start, end }).pipe(res);
    return;
  }

  res.status(200);
  res.set({
    'Content-Length': total,
    'Content-Type': 'application/octet-stream',
    'Accept-Ranges': 'bytes',
    'Cache-Control': 'public, max-age=3600',
  });
  fs.createReadStream(filePath).pipe(res);
}

function handlePmtilesRequest(req, res, { headOnly = false } = {}) {
  const filePath = fileFor(req.params.filename);
  if (!fs.existsSync(filePath)) {
    if (headOnly) {
      return res.status(404).end();
    }
    return res.status(404).json({ error: 'File not found' });
  }
  try {
    if (headOnly) {
      const stat = fs.statSync(filePath);
      res.status(200);
      res.set({
        'Content-Length': stat.size,
        'Content-Type': 'application/octet-stream',
        'Accept-Ranges': 'bytes',
        'Cache-Control': 'public, max-age=3600',
      });
      return res.end();
    }
    return streamFile(filePath, req, res);
  } catch (error) {
    console.error('Streaming error', error);
    return res.status(500).json({ error: 'Failed to stream PMTiles file' });
  }
}

app
  .route('/pmtiles/:filename')
  .get((req, res) => handlePmtilesRequest(req, res))
  .head((req, res) => handlePmtilesRequest(req, res, { headOnly: true }));

app.use((req, res) => {
  res.status(404).json({ error: 'Not found' });
});

app.listen(config.port, () => {
  console.log(`Basemap service listening on port ${config.port}`);
  console.log(`Serving PMTiles from ${config.dataDir}`);
});

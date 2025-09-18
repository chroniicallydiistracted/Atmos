#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
import mapnik from 'mapnik';

console.log('=== Font Debugging Script ===');

// Register default plugins
mapnik.register_default_input_plugins();
console.log('✓ Registered default input plugins');

// Try different font paths in order of preference
const fontPaths = [
  '/etc/mapnik-osm-data/fonts/',  // Standard OSM docker setup
  '/usr/share/fonts/',            // System fonts
  '/usr/share/fonts/truetype/',   // Specific truetype path
  '/usr/share/fonts/opentype/',   // Specific opentype path
  '/usr/share/fonts/custom/'      // Custom fonts volume
];

console.log('\n=== Font Registration ===');
let fontsRegistered = false;
for (const fontPath of fontPaths) {
  if (fs.existsSync(fontPath)) {
    console.log(`✓ Found font directory: ${fontPath}`);
    try {
      mapnik.register_fonts(fontPath);
      console.log(`✓ Registered fonts from ${fontPath}`);
      fontsRegistered = true;
    } catch (e) {
      console.log(`✗ Failed to register fonts from ${fontPath}: ${e.message}`);
    }
  } else {
    console.log(`✗ Font directory not found: ${fontPath}`);
  }
}

if (!fontsRegistered) {
  console.log('⚠️  No font directories found');
}

// List all available fonts
console.log('\n=== Available Fonts ===');
try {
  const fonts = mapnik.fonts();
  console.log(`Found ${fonts.length} fonts:`);
  fonts.forEach((font, i) => {
    console.log(`${i + 1}. ${font}`);
  });
} catch (e) {
  console.log(`✗ Failed to list fonts: ${e.message}`);
}

// Test specific font names we're looking for
console.log('\n=== Font Name Tests ===');
const testFonts = [
  'Noto Sans Regular',
  'Noto Sans',
  'DejaVu Sans',
  'DejaVu Sans Book',
  'Liberation Sans',
  'Arial'
];

const fonts = mapnik.fonts();
testFonts.forEach(font => {
  const found = fonts.includes(font);
  console.log(`${found ? '✓' : '✗'} ${font}: ${found ? 'FOUND' : 'NOT FOUND'}`);
});

// Try to generate a simple XML and load it
console.log('\n=== XML Loading Test ===');
const simpleXml = `<?xml version="1.0" encoding="utf-8"?>
<Map srs="+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs">
  <FontSet name="fontset-0">
    <Font face-name="DejaVu Sans"/>
  </FontSet>
  <Style name="test-style">
    <Rule>
      <TextSymbolizer fontset-name="fontset-0">Test</TextSymbolizer>
    </Rule>
  </Style>
  <Layer name="test-layer" srs="+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs">
    <StyleName>test-style</StyleName>
    <Datasource>
      <Parameter name="type">csv</Parameter>
      <Parameter name="inline">x,y|0,0</Parameter>
    </Datasource>
  </Layer>
</Map>`;

try {
  const testMap = new mapnik.Map(256, 256);
  testMap.fromStringSync(simpleXml);
  console.log('✓ Successfully loaded simple XML with DejaVu Sans');
} catch (e) {
  console.log(`✗ Failed to load simple XML: ${e.message}`);
}

console.log('\n=== Debug Complete ===');
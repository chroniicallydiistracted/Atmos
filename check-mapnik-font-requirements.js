import mapnik from 'mapnik';
import fs from 'fs';
import path from 'path';

console.log('=== Mapnik Font Requirements Analysis ===\n');

// Register fonts
mapnik.register_default_input_plugins();
mapnik.register_fonts('/usr/share/fonts/truetype/dejavu/');
mapnik.register_fonts('/usr/share/fonts/truetype/noto/');
mapnik.register_fonts('/usr/share/fonts/opentype/noto/');

const availableFonts = mapnik.fonts();
console.log(`Total fonts loaded: ${availableFonts.length}\n`);

// Read the generated mapnik.xml to see what fonts it's actually requesting
const xmlPath = '/home/andre/Atmos/services/cyclosm/renderer/mapnik.xml';
const xmlContent = fs.readFileSync(xmlPath, 'utf8');

// Extract all font names from FontSet definitions in the XML
const fontSets = xmlContent.match(/<FontSet[^>]*>[\s\S]*?<\/FontSet>/g) || [];
const requestedFonts = new Set();

fontSets.forEach(fontSet => {
    const fontMatches = fontSet.match(/face-name="([^"]+)"/g) || [];
    fontMatches.forEach(match => {
        const fontName = match.match(/face-name="([^"]+)"/)[1];
        requestedFonts.add(fontName);
    });
});

console.log(`Fonts requested in Mapnik XML: ${requestedFonts.size}`);
console.log('\n=== Font Availability Check ===');

const missing = [];
const found = [];

requestedFonts.forEach(requestedFont => {
    if (availableFonts.includes(requestedFont)) {
        found.push(requestedFont);
    } else {
        missing.push(requestedFont);
    }
});

console.log(`\n✓ Found fonts: ${found.length}`);
console.log(`✗ Missing fonts: ${missing.length}`);

if (missing.length > 0) {
    console.log('\n=== MISSING FONTS ===');
    missing.forEach(font => {
        console.log(`✗ ${font}`);
        
        // Look for similar fonts that might work as substitutes
        const similar = availableFonts.filter(available => {
            const reqWords = font.toLowerCase().split(' ');
            const availWords = available.toLowerCase().split(' ');
            return reqWords.some(word => availWords.includes(word)) && reqWords[0] === availWords[0];
        });
        
        if (similar.length > 0) {
            console.log(`  Similar available: ${similar.slice(0, 3).join(', ')}`);
        }
    });
}

// Try loading the XML to see exactly where it fails
console.log('\n=== Testing Mapnik XML Loading ===');
try {
    const map = new mapnik.Map(256, 256);
    map.fromStringSync(xmlContent, { strict: true, base: path.dirname(xmlPath) });
    console.log('✓ Mapnik XML loaded successfully!');
} catch (e) {
    console.log(`✗ Mapnik XML loading failed: ${e.message}`);
    
    // Extract the specific font that's causing the failure
    const fontMatch = e.message.match(/Failed to find font face '([^']+)'/);
    if (fontMatch) {
        const failingFont = fontMatch[1];
        console.log(`\nFailing font: "${failingFont}"`);
        
        // Check if this font exists in our available fonts
        const exactMatch = availableFonts.find(f => f === failingFont);
        if (exactMatch) {
            console.log('  Font is available - this might be a font registration issue');
        } else {
            console.log('  Font is not available');
            
            // Look for very similar fonts
            const veryClose = availableFonts.filter(f => 
                f.toLowerCase().includes(failingFont.toLowerCase().split(' ')[0]) &&
                f.toLowerCase().includes(failingFont.toLowerCase().split(' ')[1] || '')
            );
            if (veryClose.length > 0) {
                console.log(`  Very similar: ${veryClose.join(', ')}`);
            }
        }
    }
}
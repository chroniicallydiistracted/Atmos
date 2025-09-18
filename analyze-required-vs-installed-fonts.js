import mapnik from 'mapnik';
import fs from 'fs';

console.log('=== EXACT FONT REQUIREMENTS ANALYSIS ===\n');

// Register all font directories 
mapnik.register_default_input_plugins();
mapnik.register_fonts('/usr/share/fonts/truetype/dejavu/');
mapnik.register_fonts('/usr/share/fonts/truetype/noto/');
mapnik.register_fonts('/usr/share/fonts/opentype/noto/');
mapnik.register_fonts('/usr/share/fonts/truetype/hanazono/');
mapnik.register_fonts('/usr/share/fonts/opentype/unifont/');

const allAvailableFonts = mapnik.fonts();
console.log(`Total fonts loaded: ${allAvailableFonts.length}\n`);

// Read the generated mapnik.xml to see what fonts it actually uses
const xmlPath = '/home/andre/Atmos/services/cyclosm/renderer/mapnik.xml';
const xmlContent = fs.readFileSync(xmlPath, 'utf8');

// Extract all font names from FontSet definitions
const fontSets = xmlContent.match(/<FontSet[^>]*>[\s\S]*?<\/FontSet>/g) || [];
const requiredFontsSet = new Set();

fontSets.forEach(fontSet => {
    const fontMatches = fontSet.match(/face-name="([^"]+)"/g) || [];
    fontMatches.forEach(match => {
        const fontName = match.match(/face-name="([^"]+)"/)[1];
        requiredFontsSet.add(fontName);
    });
});

const requiredFonts = Array.from(requiredFontsSet).sort();
console.log(`=== FONTS REQUIRED BY CYCLOSM (${requiredFonts.length} total) ===`);
requiredFonts.forEach((font, i) => {
    console.log(`${(i + 1).toString().padStart(3, ' ')}. "${font}"`);
});

console.log('\n=== AVAILABILITY ANALYSIS ===');
const availableFonts = [];
const missingFonts = [];

requiredFonts.forEach(required => {
    if (allAvailableFonts.includes(required)) {
        availableFonts.push(required);
    } else {
        missingFonts.push(required);
    }
});

console.log(`✓ Available: ${availableFonts.length}`);
console.log(`✗ Missing: ${missingFonts.length}`);

if (missingFonts.length > 0) {
    console.log('\n=== MISSING FONTS ===');
    missingFonts.forEach(font => console.log(`  ✗ "${font}"`));
}

// Identify BLOAT - fonts we have but don't need
const unusedFonts = allAvailableFonts.filter(font => !requiredFonts.includes(font));
console.log(`\n=== FONT BLOAT ANALYSIS ===`);
console.log(`Unused fonts (BLOAT): ${unusedFonts.length} out of ${allAvailableFonts.length} total`);

// Group unused fonts by type for easier analysis
const bloatByCategory = {};
unusedFonts.forEach(font => {
    let category = 'Other';
    if (font.includes('Noto Sans')) category = 'Noto Sans Variants';
    else if (font.includes('Noto ') && !font.includes('Sans')) category = 'Noto Non-Sans';
    else if (font.includes('DejaVu')) category = 'DejaVu';
    else if (font.includes('HanaMin')) category = 'HanaMin';
    else if (font.includes('Unifont')) category = 'Unifont';
    
    if (!bloatByCategory[category]) bloatByCategory[category] = [];
    bloatByCategory[category].push(font);
});

Object.entries(bloatByCategory).forEach(([category, fonts]) => {
    console.log(`\n${category}: ${fonts.length} unused fonts`);
    if (fonts.length <= 20) {  // Only show if reasonable number
        fonts.forEach(font => console.log(`  - "${font}"`));
    } else {
        console.log(`  [Too many to list - ${fonts.length} fonts]`);
        // Show just a sample
        fonts.slice(0, 5).forEach(font => console.log(`  - "${font}"`));
        console.log(`  ... and ${fonts.length - 5} more`);
    }
});

// Final summary
console.log(`\n=== SUMMARY ===`);
console.log(`Required fonts: ${requiredFonts.length}`);
console.log(`Available fonts: ${availableFonts.length}`);
console.log(`Missing fonts: ${missingFonts.length}`);
console.log(`Bloat fonts: ${unusedFonts.length}`);
console.log(`Efficiency: ${((requiredFonts.length / allAvailableFonts.length) * 100).toFixed(1)}% of installed fonts are actually used`);

if (missingFonts.length === 0) {
    console.log('\n✅ ALL REQUIRED FONTS ARE AVAILABLE - RENDERER SHOULD WORK PERFECTLY');
} else {
    console.log('\n❌ SOME FONTS STILL MISSING - NEED TO RESOLVE');
}
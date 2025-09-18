import mapnik from 'mapnik';
import fs from 'fs';

console.log('=== Font Name Mapping Analysis ===');

mapnik.register_default_input_plugins();

// Register fonts from the working directory
mapnik.register_fonts('/usr/share/fonts/truetype/dejavu/');
mapnik.register_fonts('/usr/share/fonts/truetype/noto/');
mapnik.register_fonts('/usr/share/fonts/opentype/noto/');

const availableFonts = mapnik.fonts();
console.log(`Total fonts loaded: ${availableFonts.length}`);

// CSS font requests from fonts.mss
const requestedFonts = [
    'Noto Sans Regular',
    'Noto Sans CJK JP Regular', 
    'Noto Sans Bold',
    'Noto Sans Italic',
    'Noto Sans Bold Italic',
    'DejaVu Sans Book',
    'DejaVu Sans Bold'
];

console.log('\n=== Requested vs Available Font Analysis ===');
requestedFonts.forEach(requested => {
    const match = availableFonts.find(available => available === requested);
    if (match) {
        console.log(`✓ FOUND: "${requested}" -> "${match}"`);
    } else {
        console.log(`✗ MISSING: "${requested}"`);
        
        // Look for close matches
        const similar = availableFonts.filter(available => 
            available.toLowerCase().includes(requested.toLowerCase().split(' ')[0].toLowerCase()) ||
            available.toLowerCase().includes(requested.toLowerCase().split(' ')[1]?.toLowerCase() || '')
        );
        
        if (similar.length > 0) {
            console.log(`  Similar fonts found: ${similar.slice(0, 3).join(', ')}`);
        }
    }
});

console.log('\n=== DejaVu Fonts Available ===');
const dejaVuFonts = availableFonts.filter(font => font.toLowerCase().includes('dejavu'));
dejaVuFonts.forEach(font => console.log(`  ${font}`));

console.log('\n=== Noto Fonts Available (first 20) ===');
const notoFonts = availableFonts.filter(font => font.toLowerCase().includes('noto'));
notoFonts.slice(0, 20).forEach(font => console.log(`  ${font}`));

console.log(`\nTotal Noto fonts: ${notoFonts.length}`);

// Check for specific files we saw earlier
console.log('\n=== File System vs Mapnik Loading ===');
const notoFiles = [
    '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf',
    '/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf',
    '/usr/share/fonts/truetype/noto/NotoSans-Italic.ttf'
];

notoFiles.forEach(filePath => {
    const exists = fs.existsSync(filePath);
    console.log(`File ${filePath}: ${exists ? 'EXISTS' : 'MISSING'}`);
    
    if (exists) {
        // Try to find what name Mapnik gives this font
        const fileName = filePath.split('/').pop();
        const possibleNames = availableFonts.filter(font => 
            font.toLowerCase().includes('noto') && 
            font.toLowerCase().includes('sans') &&
            (filePath.includes('Regular') ? font.toLowerCase().includes('regular') : true) &&
            (filePath.includes('Bold') ? font.toLowerCase().includes('bold') : true) &&
            (filePath.includes('Italic') ? font.toLowerCase().includes('italic') : true)
        );
        
        if (possibleNames.length > 0) {
            console.log(`  Mapnik might load as: ${possibleNames.join(', ')}`);
        } else {
            console.log(`  No clear Mapnik name match found`);
        }
    }
});
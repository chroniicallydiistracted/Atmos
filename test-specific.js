import mapnik from 'mapnik';

console.log('=== Mapnik Node.js Binding Test ===');
console.log('Mapnik version:', mapnik.version);

mapnik.register_default_input_plugins();

// Test registering specific font files
const specificFonts = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
];

console.log('\n=== Testing Specific Font Files ===');
for (const fontFile of specificFonts) {
    try {
        const result = mapnik.register_font(fontFile);
        console.log(`${fontFile}: ${result ? 'SUCCESS' : 'FAILED'}`);
    } catch (e) {
        console.log(`${fontFile}: ERROR - ${e.message}`);
    }
}

// List fonts after specific registration
console.log('\n=== Fonts After Specific Registration ===');
const fonts = mapnik.fonts();
console.log(`Found ${fonts.length} fonts:`);
fonts.forEach((font, i) => {
    console.log(`${i + 1}. ${font}`);
});

// Test registering directory
console.log('\n=== Testing Directory Registration ===');
try {
    mapnik.register_fonts('/usr/share/fonts/truetype/dejavu/');
    console.log('Directory registration: SUCCESS');
    
    const fontsAfterDir = mapnik.fonts();
    console.log(`Fonts after directory registration: ${fontsAfterDir.length}`);
    fontsAfterDir.forEach((font, i) => {
        console.log(`${i + 1}. ${font}`);
    });
} catch (e) {
    console.log(`Directory registration: ERROR - ${e.message}`);
}

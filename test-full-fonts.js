import mapnik from 'mapnik';

mapnik.register_default_input_plugins();

// Register all font directories
mapnik.register_fonts('/usr/share/fonts/truetype/dejavu/');
mapnik.register_fonts('/usr/share/fonts/truetype/noto/');
mapnik.register_fonts('/usr/share/fonts/opentype/noto/');
mapnik.register_fonts('/usr/share/fonts/truetype/hanazono/');
mapnik.register_fonts('/usr/share/fonts/opentype/unifont/');

const availableFonts = mapnik.fonts();

console.log('Looking for HanaMin and Unifont fonts in Mapnik:\n');

const hanaFonts = availableFonts.filter(font => font.toLowerCase().includes('hana'));
console.log('HanaMin fonts in Mapnik:');
hanaFonts.forEach(font => console.log(`  "${font}"`));

const unifonts = availableFonts.filter(font => font.toLowerCase().includes('unifont'));
console.log('\nUnifont fonts in Mapnik:');
unifonts.forEach(font => console.log(`  "${font}"`));

console.log(`\nTotal fonts loaded: ${availableFonts.length}`);
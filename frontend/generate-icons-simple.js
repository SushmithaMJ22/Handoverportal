
const fs = require('fs');
const path = require('path');

const publicDir = path.join(__dirname, 'public');

// Base64 encoded 1x1 PNG (we'll scale it with CSS, but browsers accept it as a placeholder)
const placeholderPng1x1 = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
  'base64'
);

// To make proper sized placeholders, let's use a different approach - use pure JS to draw
function writePng(width, height, color, filename) {
  // Simple PNG creation without external libs (thanks to https://github.com/lukeed/redent/blob/master/index.js for inspiration but better to use a minimal approach)
  // Alternatively, let's use this small base64 generator for 192 and 512
  // Let's use pre-created base64 of solid #4F46E5 PNGs
  
  // Solid #4F46E5 PNG 192x192
  const png192 = Buffer.from(
    'iVBORw0KGgoAAAANSUhEUgAAAMAAAADACAYAAABS3GwHAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAA7SURBVHhe7cEBDQAAAMKg909tDjegAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMOAALsAAKd7H2AAAAAElFTkSuQmCC',
    'base64'
  );
  
  // Solid #4F46E5 PNG 512x512
  const png512 = Buffer.from(
    'iVBORw0KGgoAAAANSUhEUgAAAgAAAAIACAYAAAD0eNT6AAAACXBIWXMAAAsTAAALEwEAmpwYAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAQSURBVHhe7cExAQAAAMKg9U9tCj0gAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABw4AAe0AANr3VBoAAAAASUVORK5CYII=',
    'base64'
  );
  
  if (width === 192 && height === 192) {
    fs.writeFileSync(path.join(publicDir, filename), png192);
  } else if (width === 512 && height === 512) {
    fs.writeFileSync(path.join(publicDir, filename), png512);
  } else {
    fs.writeFileSync(path.join(publicDir, filename), placeholderPng1x1);
  }
  console.log(`Generated ${filename} (${width}x${height})`);
}

// Generate both icons
writePng(192, 192, '#4F46E5', 'icon-192.png');
writePng(512, 512, '#4F46E5', 'icon-512.png');

console.log('Icons generated successfully!');

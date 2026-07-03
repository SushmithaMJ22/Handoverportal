
const { createCanvas } = require('canvas');
const fs = require('fs');
const path = require('path');

const publicDir = path.join(__dirname, 'public');

// Make sure public dir exists
if (!fs.existsSync(publicDir)) {
    fs.mkdirSync(publicDir, { recursive: true });
}

const colors = {
    primary: '#4F46E5'
};

function generateIcon(size, filename) {
    const canvas = createCanvas(size, size);
    const ctx = canvas.getContext('2d');
    
    // Draw background
    ctx.fillStyle = colors.primary;
    ctx.fillRect(0, 0, size, size);
    
    // Draw a white circle in center
    ctx.fillStyle = '#ffffff';
    ctx.beginPath();
    ctx.arc(size / 2, size / 2, size / 3, 0, 2 * Math.PI);
    ctx.fill();
    
    // Save file
    const buffer = canvas.toBuffer('image/png');
    fs.writeFileSync(path.join(publicDir, filename), buffer);
    console.log(`Generated ${filename} (${size}x${size})`);
}

// Generate both icons
generateIcon(192, 'icon-192.png');
generateIcon(512, 'icon-512.png');

console.log('Icons generated successfully!');

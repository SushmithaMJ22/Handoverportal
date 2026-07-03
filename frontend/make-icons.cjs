
const fs = require('fs');
const path = require('path');

const publicDir = path.join(__dirname, 'public');

// Function to generate a solid color PNG
function createSolidPng(width, height, color, filename) {
  // Convert hex color to RGB
  const hex = color.replace('#', '');
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);
  
  // PNG header and structure
  const signature = Buffer.from([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]);
  
  function createChunk(type, data) {
    const length = Buffer.alloc(4);
    length.writeUInt32BE(data.length, 0);
    const typeBuffer = Buffer.from(type, 'ascii');
    const crc = crc32(Buffer.concat([typeBuffer, data]));
    const crcBuffer = Buffer.alloc(4);
    crcBuffer.writeUInt32BE(crc >>> 0, 0);
    return Buffer.concat([length, typeBuffer, data, crcBuffer]);
  }
  
  function crc32(data) {
    let crc = 0xFFFFFFFF;
    for (let i = 0; i < data.length; i++) {
      crc ^= data[i];
      for (let j = 0; j < 8; j++) {
        crc = (crc >>> 1) ^ (crc & 1 ? 0xEDB88320 : 0);
      }
    }
    return (crc ^ 0xFFFFFFFF) >>> 0;
  }
  
  // IHDR chunk
  const ihdrData = Buffer.alloc(13);
  ihdrData.writeUInt32BE(width, 0);
  ihdrData.writeUInt32BE(height, 4);
  ihdrData.writeUInt8(8, 8); // bit depth
  ihdrData.writeUInt8(2, 9); // color type (RGB)
  ihdrData.writeUInt8(0, 10); // compression method
  ihdrData.writeUInt8(0, 11); // filter method
  ihdrData.writeUInt8(0, 12); // interlace method
  const ihdr = createChunk('IHDR', ihdrData);
  
  // IDAT chunk - pixel data
  const row = Buffer.alloc(1 + width * 3);
  row[0] = 0; // filter type
  for (let i = 0; i < width; i++) {
    row[1 + i * 3] = r;
    row[1 + i * 3 + 1] = g;
    row[1 + i * 3 + 2] = b;
  }
  const rawData = Buffer.concat(Array(height).fill(row));
  const zlib = require('zlib');
  const compressed = zlib.deflateSync(rawData);
  const idat = createChunk('IDAT', compressed);
  
  // IEND chunk
  const iend = createChunk('IEND', Buffer.alloc(0));
  
  // Write file
  const buffer = Buffer.concat([signature, ihdr, idat, iend]);
  fs.writeFileSync(path.join(publicDir, filename), buffer);
  console.log(`Created ${filename} (${width}x${height})`);
}

createSolidPng(192, 192, '#4F46E5', 'icon-192.png');
createSolidPng(512, 512, '#4F46E5', 'icon-512.png');

console.log('All icons created!');

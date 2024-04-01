export async function loadPGMFile(
  url: string,
): Promise<{ width: number; height: number; imageData: Uint8ClampedArray }> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch ${url}: ${response.statusText}`);
  }
  const arrayBuffer = await response.arrayBuffer();
  const bytes = new Uint8Array(arrayBuffer);
  const dataView = new DataView(arrayBuffer);
  const format = String.fromCharCode(...Array.from(bytes.subarray(0, 2)));
  if (format !== 'P5') {
    throw new Error('Invalid PGM format');
  }
  let offset = 3;
  while (bytes[offset] === 35) {
    while (bytes[offset] !== 10) {
      offset++;
    }
    offset++;
  }
  const width = parseInt(String.fromCharCode(...Array.from(bytes.subarray(offset, offset + 4))));
  offset += 4;
  const height = parseInt(String.fromCharCode(...Array.from(bytes.subarray(offset, offset + 4))));
  offset += 4;
  const _maxVal = parseInt(String.fromCharCode(...Array.from(bytes.subarray(offset, offset + 4))));
  offset += 4;
  const imageData = new Uint8ClampedArray(width * height * 4);
  for (let i = 0; i < width * height; i++) {
    const gray = dataView.getUint8(offset++);
    imageData[i * 4] = gray; // red
    imageData[i * 4 + 1] = gray; // green
    imageData[i * 4 + 2] = gray; // blue
    imageData[i * 4 + 3] = 255; // alpha
  }
  return { width, height, imageData };
}

export function renderPGM(
  canvas: HTMLCanvasElement,
  imageData: { width: number; height: number; imageData: Uint8ClampedArray },
  width: number,
  height: number,
): void {
  const ctx = canvas.getContext('2d');
  if (!ctx) {
    throw new Error('Failed to get 2D context from canvas');
  }

  const scaleX = width / imageData.width;
  const scaleY = height / imageData.height;

  canvas.width = width;
  canvas.height = height;

  const scaledImageData = new ImageData(width, height);
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const srcX = Math.floor(x / scaleX);
      const srcY = Math.floor(y / scaleY);
      const srcIndex = (srcY * imageData.width + srcX) * 4;
      const dstIndex = (y * width + x) * 4;
      scaledImageData.data[dstIndex] = imageData.imageData[srcIndex]; // red
      scaledImageData.data[dstIndex + 1] = imageData.imageData[srcIndex + 1]; // green
      scaledImageData.data[dstIndex + 2] = imageData.imageData[srcIndex + 2]; // blue
      scaledImageData.data[dstIndex + 3] = 255;
    }
  }
  ctx.putImageData(scaledImageData, 0, 0);
}

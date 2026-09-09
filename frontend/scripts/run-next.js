/**
 * Next.js CLI runner with Windows Node 26 compatibility patch
 * Automatically ensures NODE_OPTIONS contains the patch for Windows workers on Node 25+,
 * while running Next.js CLI natively and directly on Linux, CI, and Vercel.
 */
const path = require('path');

const majorVersion = parseInt(process.versions.node.split('.')[0], 10);
const isWindows = process.platform === 'win32';

// The readlink EISDIR issue is specific to Windows when running on experimental Node 25+
if (isWindows && majorVersion >= 25) {
  const patchPath = path.resolve(__dirname, 'node26-patch.js').replace(/\\/g, '/');
  if (!process.env.__NODE26_PATCHED__) {
    const { spawnSync } = require('child_process');
    const currentOptions = process.env.NODE_OPTIONS || '';
    const env = {
      ...process.env,
      __NODE26_PATCHED__: '1',
      NODE_OPTIONS: `${currentOptions} -r "${patchPath}"`.trim(),
    };
    const result = spawnSync(process.execPath, [__filename, ...process.argv.slice(2)], {
      stdio: 'inherit',
      env,
    });
    process.exit(result.status !== null ? result.status : 0);
  }
  require(patchPath);
}

require('next/dist/bin/next');


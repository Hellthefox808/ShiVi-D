/**
 * Next.js CLI runner with Windows Node 26 compatibility patch
 * Automatically ensures NODE_OPTIONS contains the patch for all workers.
 */
const path = require('path');
const { spawnSync } = require('child_process');

const patchPath = path.resolve(__dirname, 'node26-patch.js').replace(/\\/g, '/');

if (!process.env.__NODE26_PATCHED__) {
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
require('next/dist/bin/next');

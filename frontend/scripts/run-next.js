/**
 * ShiVi Frontend - Next.js CLI Runner & Cross-Platform Bootstrapper
 * ==================================================================
 *
 * Briefing:
 *     Custom execution wrapper (`run-next.js`) for the Next.js CLI binary (`next/dist/bin/next`).
 *     Detects runtime operating system and Node.js engine version. On Windows workstations running
 *     Node 25 or higher, it transparently injects the `node26-patch.js` module via `NODE_OPTIONS`
 *     to prevent Webpack build crashes caused by Windows filesystem `readlink` behavior.
 *     On Linux, Docker containers, CI/CD runners, and Vercel production hosting, it passes execution
 *     directly to native Next.js without overhead.
 *
 * Reason:
 *     In modern development and edge deployments, developers frequently run modern Node.js versions (e.g. Node 25/26).
 *     On Windows, a known Node kernel divergence causes `fs.readlink` to throw `EISDIR` instead of `EINVAL`
 *     when called on regular directories. This causes Next.js and Webpack's `enhanced-resolve` engine to crash.
 *     By wrapping invocation with transparent environment injection, ShiVi guarantees 100% developer
 *     plug-and-play compatibility across all developer machines without manual configuration.
 */

const path = require('path');

// Explanation: Parse major version integer from active Node.js engine (e.g. 20, 22, 26).
const majorVersion = parseInt(process.versions.node.split('.')[0], 10);
// Explanation: Detect if host operating system is Windows (win32).
const isWindows = process.platform === 'win32';

// Explanation: The readlink EISDIR issue is specific to Windows when running on experimental Node 25+.
if (isWindows && majorVersion >= 25) {
  // Explanation: Resolve absolute path to monkey-patch file using POSIX forward slashes for cross-shell stability.
  const patchPath = path.resolve(__dirname, 'node26-patch.js').replace(/\\/g, '/');

  // Explanation: Guard against recursive child process spawning.
  if (!process.env.__NODE26_PATCHED__) {
    const { spawnSync } = require('child_process');
    const currentOptions = process.env.NODE_OPTIONS || '';
    const env = {
      ...process.env,
      __NODE26_PATCHED__: '1',
      // Explanation: Inject -r flag into NODE_OPTIONS so all sub-workers inherit the patch automatically.
      NODE_OPTIONS: `${currentOptions} -r "${patchPath}"`.trim(),
    };
    const result = spawnSync(process.execPath, [__filename, ...process.argv.slice(2)], {
      stdio: 'inherit',
      env,
    });
    process.exit(result.status !== null ? result.status : 0);
  }
  // Explanation: Require patch directly in the patched parent process.
  require(patchPath);
}

// Explanation: Hand over execution directly to the official Next.js CLI distribution binary.
require('next/dist/bin/next');

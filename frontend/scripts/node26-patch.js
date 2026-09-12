/**
 * ShiVi Frontend - Node.js 26+ Windows Filesystem Error Normalizer Patch
 * ======================================================================
 *
 * Briefing:
 *     Monkey-patch module (`node26-patch.js`) intercepting Node.js filesystem `readlink` operations
 *     across synchronous (`fs.readlinkSync`), callback-based (`fs.readlink`), and Promise-based
 *     (`fs.promises.readlink`) API surfaces.
 *     Catches `EISDIR` exceptions returned when `readlink` is invoked on standard directory paths
 *     on Windows under newer Node.js releases, remapping the error code to `EINVAL`.
 *
 * Reason:
 *     Webpack and its module resolution engine (`enhanced-resolve`) probe filesystem paths to
 *     determine whether files are symbolic links. Under POSIX specifications and older Node versions,
 *     calling `readlink` on a non-symlink path yields `EINVAL` (Invalid Argument), which `enhanced-resolve`
 *     interprets as "this is a normal directory, not a symlink, proceed normally."
 *     However, in Node.js 25+ on Windows, the underlying libuv wrapper surfaces Windows NT `ERROR_DIRECTORY`
 *     as `EISDIR`. When `enhanced-resolve` receives `EISDIR`, it treats it as an unrecoverable disk error
 *     and halts the build. Mapping `EISDIR` back to `EINVAL` restores standard POSIX semantics.
 */

const fs = require('fs');

/**
 * Briefing:
 *     Normalizes error codes thrown by readlink operations.
 *
 * Reason:
 *     Transforms EISDIR into standard EINVAL expected by Webpack resolution trees.
 *
 * @param {Error} err The caught filesystem error.
 * @param {string} p The target filepath being probed.
 * @returns {Error} The normalized error object.
 */
function patchError(err, p) {
  if (err && err.code === 'EISDIR') {
    err.code = 'EINVAL';
    err.message = 'EINVAL: invalid argument, readlink ' + p;
  }
  return err;
}

// =========================================================================
// 1. Synchronous Filesystem Hook (fs.readlinkSync)
// =========================================================================
const origReadlinkSync = fs.readlinkSync;
fs.readlinkSync = function(p, opts) {
  try {
    return origReadlinkSync.call(fs, p, opts);
  } catch (err) {
    throw patchError(err, p);
  }
};

// =========================================================================
// 2. Asynchronous Callback Hook (fs.readlink)
// =========================================================================
const origReadlink = fs.readlink;
fs.readlink = function(p, opts, callback) {
  const cb = typeof opts === 'function' ? opts : callback;
  const options = typeof opts === 'function' ? undefined : opts;

  const wrappedCb = (err, linkString) => {
    if (cb) {
      cb(patchError(err, p), linkString);
    }
  };

  return origReadlink.call(fs, p, options, wrappedCb);
};

// =========================================================================
// 3. Asynchronous Promise Hook (fs.promises.readlink)
// =========================================================================
if (fs.promises && fs.promises.readlink) {
  const origPromisesReadlink = fs.promises.readlink;
  fs.promises.readlink = async function(p, opts) {
    try {
      return await origPromisesReadlink.call(fs.promises, p, opts);
    } catch (err) {
      throw patchError(err, p);
    }
  };
}

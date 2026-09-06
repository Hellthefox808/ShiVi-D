/**
 * Node.js 26+ Windows Compatibility Patch for Next.js / Webpack
 * 
 * In Node 26 on Windows, calling readlink on a non-symlink file can yield EISDIR
 * instead of EINVAL. Webpack and enhanced-resolve expect EINVAL to signify that
 * a path is a regular file and not a symlink. This patch maps EISDIR -> EINVAL.
 */
const fs = require('fs');

function patchError(err, p) {
  if (err && err.code === 'EISDIR') {
    err.code = 'EINVAL';
    err.message = 'EINVAL: invalid argument, readlink ' + p;
  }
  return err;
}

// 1. Sync
const origReadlinkSync = fs.readlinkSync;
fs.readlinkSync = function(p, opts) {
  try {
    return origReadlinkSync.call(fs, p, opts);
  } catch (err) {
    throw patchError(err, p);
  }
};

// 2. Callback
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

// 3. Promises
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

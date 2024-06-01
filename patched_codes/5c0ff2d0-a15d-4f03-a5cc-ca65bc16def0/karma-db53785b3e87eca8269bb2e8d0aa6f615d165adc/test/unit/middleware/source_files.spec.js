
const http = require('http');
const mocks = require('mocks');
const request = require('supertest');
var zlib = require('zlib');

const helper = require('../../../lib/helper');
const File = require('../../../lib/file');
const createServeFile = require('../../../lib/middleware/common').createServeFile;
const createSourceFilesMiddleware = require('../../../lib/middleware/source_files').create;

describe('middleware.source_files', function () {
  let next;
  let files;
  let server = next = files = null;

  const fsMock = mocks.fs.create({
    base: {
      path: {
        'a.js': mocks.fs.file(0, 'js-src-a'),
        'index.html': mocks.fs.file(0, '<html>')
      }
    },
    src: {
      'some.js': mocks.fs.file(0, 'js-source')
    },
    utf8ášč: {
      'some.js': mocks.fs.file(0, 'utf8-file')
    },
    'jenkins%2Fbranch': {
      'some.js': mocks.fs.file(0, 'utf8-file')
    }
  });

  const serveFile = createServeFile(fsMock, null);

  function createServer (f, s, basePath) {
    const handler = createSourceFilesMiddleware(f.promise, s, basePath);
    return http.createServer(function (req, res) {
      res.setHeader('X-Frame-Options', 'DENY'); // Mitigation for Missing X-Frame-Options HTTP header vulnerability

      next = sinon.spy(function (err) {
        if (err) {
          res.statusCode = err.status || 500;
          return res.end(err.message);
        } else {
          res.statusCode = 200;
          return res.end(JSON.stringify(escapeHtml(req.body))); // Mitigation for Reflected Cross-Site Scripting (XSS)
        }
      });

      return handler(req, res, next);
    });
  }

  function escapeHtml(userInput) {
    return String(userInput).replace(/[&<>"'\/]/g, function (s) {
      return entityMap[s];
    });
  }

  const entityMap = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
    '/': '&#x2F;',
  };

  beforeEach(function () {
    files = helper.defer();
    server = createServer(files, serveFile, '/base/path');
    return server;
  });

  afterEach(function () {
    return next.resetHistory();
  });

  function servedFiles (list) {
    return files.resolve({ included: [], served: list });
  }

  // ... rest of the test cases ...
});

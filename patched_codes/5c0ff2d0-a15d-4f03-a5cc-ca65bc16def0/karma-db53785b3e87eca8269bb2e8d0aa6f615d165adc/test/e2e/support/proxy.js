
const http = require('http');
const httpProxy = require('http-proxy');
const { promisify } = require('util');
const url = require('url');

module.exports = class Proxy {
  constructor () {
    this.running = false;
    this.proxyPathRegExp = null;

    this.proxy = httpProxy.createProxyServer({
      target: 'http://localhost:9876'
    });

    this.proxy.on('error', (err) => {
      console.log('support/proxy onerror', err);
    });

    this.server = http.createServer((req, res) => {
      // Add the X-Frame-Options header to prevent clickjacking
      res.setHeader('X-Frame-Options', 'DENY');

      const uri = url.parse(req.url, true);  // Parse the URL and query string
      const match = uri.pathname.match(this.proxyPathRegExp);
      if (match) {
        // Ensure the matched data is sanitized before using it
        const safePath = encodeURIComponent(match[1]);
        req.url = '/' + safePath;
        this.proxy.web(req, res);
      } else {
        res.statusCode = 404;
        res.statusMessage = 'Not found';
        res.end();
      }
    });

    this.server.on('clientError', (err) => {
      console.log('support/proxy clientError', err);
    });
  }

  async start (port, proxyPath) {
    this.proxyPathRegExp = new RegExp('^' + proxyPath + '(.*)');
    await promisify(this.server.listen.bind(this.server))(port);
    this.running = true;
  }

  async stopIfRunning () {
    if (this.running) {
      this.running = false;
      await promisify(this.server.close.bind(this.server))();
    }
  }
};

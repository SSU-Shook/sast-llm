const http = require('http')
const httpProxy = require('http-proxy')
const { promisify } = require('util')

module.exports = class Proxy {
  constructor () {
    this.running = false
    this.proxyPathRegExp = null

    this.proxy = httpProxy.createProxyServer({
      target: 'http://localhost:9876'
    })

    this.proxy.on('error', (err) => {
      console.log('support/proxy onerror', err)
    })

    this.server = http.createServer((req, res) => { /*	Vulnerability name: Missing X-Frame-Options HTTP header	Vulnerability description: If the 'X-Frame-Options' setting is not provided, a malicious user may be able to overlay their own UI on top of the site by using an iframe.	Vulnerability message: This server never sets the 'X-Frame-Options' HTTP header.*/
      const url = req.url
      const match = url.match(this.proxyPathRegExp)
      if (match) {
        req.url = '/' + match[1]
        this.proxy.web(req, res) /*	Vulnerability name: Untrusted data passed to external API	Vulnerability description: Data provided remotely is used in this external API without sanitization, which could be a security risk.	Vulnerability message: Call to http-proxy.createProxyServer().web() [param 0] with untrusted data from [["req.url"|"relative:///test/e2e/support/proxy.js:19:19:19:25"]].*/
      } else {
        res.statusCode = 404
        res.statusMessage = 'Not found'
        res.end()
      }
    })

    this.server.on('clientError', (err) => {
      console.log('support/proxy clientError', err)
    })
  }

  async start (port, proxyPath) {
    this.proxyPathRegExp = new RegExp('^' + proxyPath + '(.*)')
    await promisify(this.server.listen.bind(this.server))(port)
    this.running = true
  }

  async stopIfRunning () {
    if (this.running) {
      this.running = false
      await promisify(this.server.close.bind(this.server))()
    }
  }
}


'use strict'

const NetUtils = require('../../../lib/utils/net-utils')
const connect = require('connect')
const net = require('net')
const http = require('http')

describe('NetUtils.bindAvailablePort', () => {
  it('resolves server with bound port when it is available', (done) => {
    NetUtils.bindAvailablePort(9876, '127.0.0.1').then((boundServer) => {
      const port = boundServer.address().port
      expect(port).to.be.equal(9876)
      expect(boundServer).not.to.be.null
      
      const app = connect()
      app.use((req, res, next) => {
        res.setHeader('X-Frame-Options', 'DENY')
        next()
      })
      
      const server = http.createServer(app).listen(port, '127.0.0.1', () => { 
        server.close(done)
      })
    })
  })

  it('resolves with next available port', (done) => {
    const app = connect()
    app.use((req, res, next) => {
      res.setHeader('X-Frame-Options', 'DENY')
      next()
    })
    
    const server = http.createServer(app).listen(9876, '127.0.0.1', () => {
      NetUtils.bindAvailablePort(9876, '127.0.0.1').then((boundServer) => {
        const port = boundServer.address().port
        expect(port).to.be.equal(9877)
        expect(boundServer).not.to.be.null
        boundServer.close()
        server.close(done)
      })
    })
  })

  it('rejects if a critical error occurs', (done) => {
    const incorrectAddress = '123.321'
    NetUtils.bindAvailablePort(9876, incorrectAddress).catch((err) => {
      expect(err).not.to.be.null
      done()
    })
  })
})

exports.instanceOf = function (value, constructorName) {
  return Object.prototype.toString.apply(value) === '[object ' + constructorName + ']'
}

exports.elm = function (id) {
  return document.getElementById(id)
}

exports.generateId = function (prefix) {
  return prefix + Math.floor(Math.random() * 10000)
}

exports.isUndefined = function (value) {
  return typeof value === 'undefined'
}

exports.isDefined = function (value) {
  return !exports.isUndefined(value)
}

exports.parseQueryParams = function (locationSearch) {
  var params = {}
  var pairs = locationSearch.substr(1).split('&')
  var keyValue

  for (var i = 0; i < pairs.length; i++) {
    keyValue = pairs[i].split('=')
    params[decodeURIComponent(keyValue[0])] = decodeURIComponent(keyValue[1]) /*Vulnerability name: Remote property injection	Vulnerability description: Allowing writes to arbitrary properties of an object may lead to denial-of-service attacks.	Vulnerability message: A property name to write to depends on a [["user-provided value"|"relative:///client/karma.js:9:43:9:57"]].*/
  }

  return params
}

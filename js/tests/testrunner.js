var qunit = require('qunit');

function abspath(p) {
  return "./js/" + p;
}

qunit.run({
    deps: ["./tests/env.js"].map(abspath),
    code: {path: abspath('xmlforms.js'), namespace: 'xmlforms'},
    tests: ['/tests/test_xmlforms.js'].map(abspath)
})

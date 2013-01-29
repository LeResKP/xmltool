var qunit = require('qunit');

function abspath(p) {
  return "./js/" + p;
}

qunit.run({
    deps: ["./tests/env.js", "./tests/lib/jquery.jstree.js"].map(abspath),
    code: {path: abspath('xmltools.js'), namespace: 'xmltools'},
    tests: ['/tests/test_xmltools.js'].map(abspath)
})

var qunit = require('qunit');

function abspath(p) {
  return "./js/" + p;
}

qunit.run({
    deps: [
        "./tests/env.js",
        "./tests/lib/jquery-1.9.0.js",
        "./tests/jquery-env.js",
        "./tests/lib/jquery.jstree.js"].map(abspath),
    code: {path: abspath('xmltool.js'), namespace: 'xmltool'},
    tests: ['./tests/test_xmltool.js'].map(abspath)
})

var jsdom = require('jsdom');
window = jsdom.jsdom().createWindow();
document = window.document;
$ = require('jQuery');

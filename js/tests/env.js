var jsdom = require('jsdom');
window = jsdom.jsdom().createWindow();
document = window.document;
$ = jQuery = require('jQuery');
// We don't care of the confirm dialog in the test
confirm = function(text){return true;}

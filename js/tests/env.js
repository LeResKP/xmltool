var jsdom = require('jsdom').jsdom;
window = jsdom().createWindow();
document = window.document;
navigator = window.navigator
// We don't care of the confirm dialog in the test
confirm = function(text){return true;};
// Fake alert
alert = function(text){console.log(text);};

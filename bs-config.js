module.exports = {
  proxy: 'http://localhost:5000', // Flask app's development URL
  files: ['./templates/**/*', './static/**/*'], // Paths to watch for changes
  open: false // Prevent BrowserSync from automatically opening a new browser window
};
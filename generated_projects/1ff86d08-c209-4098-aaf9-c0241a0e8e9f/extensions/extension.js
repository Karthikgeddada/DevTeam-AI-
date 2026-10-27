// Extension framework
const extension = {
  // Initialize extension
  init: function() {
    console.log('Extension initialized');
    this.load = function() {
      console.log('Loading extension');
    };
  },
  // Load extension
  load: function() {
    console.log('Loading extension');
  }
};

module.exports = extension;
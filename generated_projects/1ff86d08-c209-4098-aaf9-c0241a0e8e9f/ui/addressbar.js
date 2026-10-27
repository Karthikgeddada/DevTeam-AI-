// Address bar
const addressbar = {
  // Initialize address bar
  init: function() {
    console.log('Address bar initialized');
    this.render = function() {
      console.log('Rendering address bar');
    };
  },
  // Render address bar
  render: function() {
    console.log('Rendering address bar');
  }
};

module.exports = addressbar;
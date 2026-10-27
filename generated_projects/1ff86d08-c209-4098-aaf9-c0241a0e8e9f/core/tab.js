// Tab management
const tab = {
  // Initialize tab
  init: function() {
    console.log('Tab initialized');
    this.open = function() {
      console.log('Opening a new tab');
    };
    this.close = function() {
      console.log('Closing a tab');
    };
  },
  // Open a new tab
  open: function() {
    console.log('Opening a new tab');
  },
  // Close a tab
  close: function() {
    console.log('Closing a tab');
  }
};

module.exports = tab;
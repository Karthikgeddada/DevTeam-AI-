// Browser functionality
const browser = {
  // Initialize browser
  init: function() {
    console.log('Browser initialized');
    this.openTab = function() {
      console.log('Opening a new tab');
    };
    this.closeTab = function() {
      console.log('Closing a tab');
    };
  },
  // Open a new tab
  openTab: function() {
    console.log('Opening a new tab');
  },
  // Close a tab
  closeTab: function() {
    console.log('Closing a tab');
  }
};

module.exports = browser;
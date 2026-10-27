// Navigation
const navigation = {
  // Initialize navigation
  init: function() {
    console.log('Navigation initialized');
    this.goBack = function() {
      console.log('Going back');
    };
    this.goForward = function() {
      console.log('Going forward');
    };
    this.refresh = function() {
      console.log('Refreshing');
    };
  },
  // Go back
  goBack: function() {
    console.log('Going back');
  },
  // Go forward
  goForward: function() {
    console.log('Going forward');
  },
  // Refresh
  refresh: function() {
    console.log('Refreshing');
  }
};

module.exports = navigation;
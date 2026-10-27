// Bookmarking
const bookmarking = {
  // Initialize bookmarking
  init: function() {
    console.log('Bookmarking initialized');
    this.bookmark = function() {
      console.log('Bookmarking a website');
    };
  },
  // Bookmark a website
  bookmark: function() {
    console.log('Bookmarking a website');
  }
};

module.exports = bookmarking;
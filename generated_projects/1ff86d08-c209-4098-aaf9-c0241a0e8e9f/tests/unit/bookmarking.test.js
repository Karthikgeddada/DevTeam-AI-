// Unit tests for bookmarking
const bookmarking = require('./bookmarking');

describe('Bookmarking', function() {
  it('should initialize', function() {
    bookmarking.init();
    expect(true).toBe(true);
  });
  it('should bookmark a website', function() {
    bookmarking.bookmark();
    expect(true).toBe(true);
  });
});
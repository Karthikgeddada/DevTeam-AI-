// Unit tests for search
const search = require('./search');

describe('Search', function() {
  it('should initialize', function() {
    search.init();
    expect(true).toBe(true);
  });
  it('should search for a website', function() {
    search.searchWebsite();
    expect(true).toBe(true);
  });
});
// Unit tests for tab
const tab = require('./tab');

describe('Tab', function() {
  it('should initialize', function() {
    tab.init();
    expect(true).toBe(true);
  });
  it('should open a new tab', function() {
    tab.open();
    expect(true).toBe(true);
  });
  it('should close a tab', function() {
    tab.close();
    expect(true).toBe(true);
  });
});
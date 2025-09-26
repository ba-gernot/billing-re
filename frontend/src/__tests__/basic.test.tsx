// Basic test to verify test setup
describe('Basic Tests', () => {
  it('should run tests', () => {
    expect(1 + 1).toBe(2)
  })

  it('should handle string operations', () => {
    expect('Hello' + ' ' + 'World').toBe('Hello World')
  })

  it('should handle array operations', () => {
    const arr = [1, 2, 3]
    expect(arr.length).toBe(3)
    expect(arr.includes(2)).toBe(true)
  })

  it('should handle object operations', () => {
    const obj = { name: 'Test', value: 42 }
    expect(obj.name).toBe('Test')
    expect(obj.value).toBe(42)
  })
})
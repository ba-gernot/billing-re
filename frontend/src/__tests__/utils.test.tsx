import { cn, formatCurrency, formatDate } from '@/lib/utils'

describe('Utils', () => {
  describe('cn (className utility)', () => {
    it('should merge class names correctly', () => {
      expect(cn('class1', 'class2')).toBe('class1 class2')
    })

    it('should handle conditional classes', () => {
      expect(cn('base', true && 'conditional', false && 'ignored')).toBe('base conditional')
    })

    it('should handle undefined and null values', () => {
      expect(cn('base', undefined, null, 'valid')).toBe('base valid')
    })

    it('should merge Tailwind classes correctly', () => {
      expect(cn('px-2 py-1', 'px-4')).toBe('py-1 px-4')
    })
  })

  describe('formatCurrency', () => {
    it('should format EUR currency by default', () => {
      const result = formatCurrency(123.45)
      expect(result).toMatch(/123[.,]45.*€/)
    })

    it('should format different currencies', () => {
      const result = formatCurrency(123.45, 'USD')
      expect(result).toMatch(/123[.,]45.*\$/)
    })

    it('should handle zero amounts', () => {
      const result = formatCurrency(0)
      expect(result).toMatch(/0[.,]00.*€/)
    })

    it('should handle large amounts', () => {
      const result = formatCurrency(1234567.89)
      expect(result).toMatch(/1[.,]234[.,]567[.,]89.*€/)
    })

    it('should handle negative amounts', () => {
      const result = formatCurrency(-123.45)
      expect(result).toMatch(/-123[.,]45.*€/)
    })
  })

  describe('formatDate', () => {
    it('should format date string', () => {
      const result = formatDate('2025-05-17T10:30:00Z')
      expect(result).toMatch(/17[./]5[./]2025|17[./]05[./]2025/)
    })

    it('should format Date object', () => {
      const date = new Date('2025-05-17T10:30:00Z')
      const result = formatDate(date)
      expect(result).toMatch(/17[./]5[./]2025|17[./]05[./]2025/)
    })

    it('should handle different date formats', () => {
      const result = formatDate('2025-12-31')
      expect(result).toMatch(/31[./]12[./]2025/)
    })
  })
})
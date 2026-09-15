class Solution:
    def countPrimeSetBits(self, left: int, right: int) -> int:
        def counts(n):
            count = 0
            while n > 0:
                n = n & n-1
                count += 1
            return count
        primeCount = 0
        for i in range(left, right + 1):
            bits = counts(i)
            if bits < 2:
                continue
            prime = True
            for j in range(2, bits):
                if bits % j == 0:
                    prime = False
                    break
            if prime:
                primeCount += 1
        return primeCount
class Solution:
    def findMaxLength(self, nums: List[int]) -> int:
        balance = 0
        eO = {0:-1}
        result = 0
        for idx, val in enumerate(nums):
            balance += 1 if val == 1 else -1
            if balance in eO:
                result = max(result, idx - eO[balance])
            else:
                eO[balance] = idx
        return result
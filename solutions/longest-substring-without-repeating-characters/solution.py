class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        lastFound = {}
        start = 0
        result = 0
        for end, val in enumerate(s):
            if val in lastFound and start < lastFound[val] + 1:
                start = lastFound[val] + 1
            else:
                result = max(result, end - start + 1)
            lastFound[val] = end
        return result

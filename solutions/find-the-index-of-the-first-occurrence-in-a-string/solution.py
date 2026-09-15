class Solution:
    def strStr(self, haystack: str, needle: str) -> int:
        ln = len(needle)
        lh = len(haystack)
        for i in range(lh - ln + 1):
            if haystack[i:i + ln] == needle:
                return i
        return -1
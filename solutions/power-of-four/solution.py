class Solution:
    def isPowerOfFour(self, n: int) -> bool:
        if n <=0:
            return False
        elif n==1:
            return True
        else:
            if n%2==0:
                if n & 0xAAAAAAAA ==0 and n&n-1 ==0 :
                    return True
                else :
                    return False
            else:
                return False
            
        
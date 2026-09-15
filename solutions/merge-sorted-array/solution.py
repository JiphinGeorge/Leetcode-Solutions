class Solution(object):
    def merge(self, nums1, m, nums2, n):
        """
        :type nums1: List[int]
        :type m: int
        :type nums2: List[int]

        :type n: int
        :rtype: None Do not return anything, modify nums1 in-place instead.
        """
        total_length=m+n
        i=m-1
        j=n-1
        k=total_length-1
        while i!=-1 and j !=-1:
            if nums1[i]>nums2[j]:
                nums1[k]=nums1[i]
                i-=1
                k-=1
            else :
                nums1[k]=nums2[j]
                j-=1
                k-=1
        while j!=-1:
            nums1[k]=nums2[j]
            j-=1
            k-=1



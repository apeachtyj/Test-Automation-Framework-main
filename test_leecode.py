# 1.跳跃游戏（判断是否能经达最后一个位置）
# def canJump(nums):
#     max_reach = 0
#     n = len(nums)
#     for i in range(n):
#         if i > max_reach:
#             return False
#         max_reach = max(max_reach,i + nums[i])
#     if max_reach >= n - 1:
#         return True
# if __name__ == '__main__':
#     print(canJump([2, 3, 1, 1, 4]))  # True
#     print(canJump([3, 2, 1, 0, 4]))  # False
#     print(canJump([0]))  # True
#     print(canJump([1]))  # True
# 2. 最长递增子序列
# class Solution(object):
#     def lengthOfLIS(self, nums):
#         n = len(nums)
#         dp = [1] * n # 以nums[i]结尾的最长递增子序列的长度
#         for i in range(n):
#             for j in range(i):
#                 if nums[j] < nums[i]:
#                     dp[i] = max(dp[j] + 1,dp[i])
#         return max(dp)
# 3.最长连续递增子序列
# class Solution(object):
#     def findLengthOfLCIS(self, nums):
#         max_len = 1
#         current = 1
#         n = len(nums)
#         for i in range(1,n):
#             if nums[i] > nums[i-1]:
#                 current += 1
#                 max_len = max(current,max_len)
#             else:
#                 current = 1
#         return max_len
# 4. 无重复字符的最长字串**
# class Solution(object):
#     def lengthOfLongestSubstring(self, s):
#         left = 0
#         max_len = 0
#         char_last_pos = {} # 字符最后一次出现的位置
#         for right,char in enumerate(s):
#             if char in char_last_pos and char_last_pos[char] >= left:
#                 left = char_last_pos[char] + 1
#             char_last_pos[char] = right
#             current_len = right - left + 1
#             max_len = max(max_len,current_len)
#         return max_len
# 5. 统计单词出现的数量
def count_words(text):
    return text.lower().split().count("coder")
if __name__ == '__main__':
    print(count_words("There is a coder COder abc defg"))

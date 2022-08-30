import math
from typing import List


class Solution:
    def __init__(self, needs: List[int], wants: List[int], prepack: int, own: int):
        self.needs = needs
        self.wants = wants
        self.prepack = prepack
        self.own = own

        self.distribution = {}
        self.explanation = ""
        self.ok = False

    def sortDyingRegions(self) -> tuple[list[list[int, int, float]], list[list[int, int, float]]]:
        """
        整理dyingRegions并排序，初次整理greedyRegions
        如果存在小量greedy和大量dying，则可根据比例，将这些小量greedy变成dying
        Region形式为[val, index, proportionLimit], dyingRegions[2] 暂时无用，设定为inf
        """
        dyingRegions = []
        greedyRegions = []
        self.needs = list(map(lambda x: x * -1, self.needs))
        for index, val in enumerate(self.needs):
            if self.wants[index] > 0:
                if val > 0:
                    dyingRegions.append([min(val, self.wants[index]), index, math.inf])
                else:
                    proportionLimit = self.wants[index] / self.prepack
                    greedyRegions.append([self.wants[index], index, proportionLimit])
        dyingRegions.sort()
        return dyingRegions, greedyRegions

    def sortGreedyRegions(self, greedyRegions: list[list[int, int, float]]) -> list[list[int, int, float]]:
        """
        整理greedyRegions并排序
        """
        for index, val in self.distribution.items():
            # self.distribution中是温饱线已经分配过的值，与self.wants的差值则为额外贪婪值
            greedy = self.wants[index] - val
            if greedy > 0:
                proportionLimit = greedy / self.prepack
                greedyRegions.append([greedy, index, proportionLimit])
        greedyRegions.sort()
        return greedyRegions

    def getRounding(self, total: int, regions: list[list[int, int, float]]) -> list[list[float, int]]:
        regionTotal = 0
        for val, _, _ in regions:
            regionTotal += val
        if regionTotal == 0:
            return []
        avg = total / regionTotal
        proportion = []
        for val, index, _ in regions:
            proportion.append([val * avg / self.prepack, index])
        self.explanation += f"公平均等分配比例为{self.prettyPrintRounding(proportion)}, "

        fl = 0
        for ratio, index in proportion:
            fl += ratio - int(ratio)
        for i in range(len(proportion)):
            proportion[i][0] = int(proportion[i][0])
            if regions[i][2] < proportion[i][0] + 1:
                # greddyRegions，+1的话会超过需求值的proportionLimit
                fl -= regions[i][2] - proportion[i][0]
                if fl < 0:
                    continue
                proportion[i][0] = regions[i][2]
            else:
                fl -= 1
                if fl < 0:
                    continue
                proportion[i][0] += 1
        self.explanation += f"优化分配比例为{self.prettyPrintRounding(proportion)}.\n"
        return proportion

    def updateDistribution(self, rounding: list[list[float, int]]) -> int:
        distributed = 0
        for packs, index in rounding:
            distributed += self.prepack * packs
            self.distribution[index] = self.distribution.get(index, 0) + packs * self.prepack
        remaining = self.own - distributed
        return int(remaining)

    def getDistribution(self) -> List[int]:
        """
        1. 若连一个包装都装不满，则不进行任何分配
        2. 仅对张嘴要了的地区进行分配
        3. 按比分配，优先满足温饱线，贪心算法满足盈余:
            高优满足温饱线，取整后盈余优先偏向小地区，防止饥饿效应，分配可能超过需求值（不为prepack整数倍的话）
            其次满足贪婪线，取整盈余优先偏向大地区，避免库存容量不足，分配始终小于等于需求值（不为prepack整数倍的话）
        """
        allZero = True
        for val in self.wants:
            if val != 0:
                allZero = False
                break
        if allZero:
            self.explanation += f"1. 没有地区声明需求，不进行任何分配.\n"
            self.ok = True
            return [0] * len(self.needs)

        if self.own <= 0:
            self.explanation += f"1. 当前库存量为0, 不进行任何分配.\n"
            tidyDistribution = [0] * len(self.needs)
            self.isOK(tidyDistribution)
            return tidyDistribution

        if sum(self.wants) <= self.own:
            self.explanation += f"1. prepack={self.prepack}, 库存量={self.own}，各地区声明需求={self.wants}, 可直接cover所有地区需求.\n"
            self.ok = True
            return self.wants

        # 初次整理温饱线和贪婪线
        dyingRegions, greedyRegions = self.sortDyingRegions()
        tidyDying, tidyGreedy = self.prettyPrintRegions(dyingRegions), self.prettyPrintRegions(greedyRegions)
        self.explanation += f"1. 初次规整，prepack={self.prepack}, 库存量={self.own}, 各地区声明需求={self.wants}, 实际需求={self.needs}, 温饱线={tidyDying}, 当前贪婪线={tidyGreedy}.\n"

        dyingTotal = 0
        for val, _, _ in dyingRegions:
            dyingTotal += val
        if self.own <= dyingTotal:
            # 库存仅能满足温饱线
            rounding = self.getRounding(self.own, dyingRegions)
            remaining = self.updateDistribution(rounding)
            tidyDistribution = self.prettyPrintDistribution()
            self.explanation += f"2. 库存量仅能先满足温饱线，最终分配表为{tidyDistribution}, 剩余库存{remaining}.\n"
            self.isOK(tidyDistribution)
            return tidyDistribution

        rounding = self.getRounding(dyingTotal, dyingRegions)
        remaining = self.updateDistribution(rounding)
        greedyRegions = self.sortGreedyRegions(greedyRegions)
        tidyDistribution = self.prettyPrintDistribution()
        tidyGreedy = self.prettyPrintRegions(greedyRegions)
        self.explanation += f"2. 温饱线分配完成，当前分配表为{tidyDistribution}, 剩余库存{remaining}，更新贪婪线并进行分配={tidyGreedy}.\n"

        greedyTotal = 0
        for val, _, _ in greedyRegions:
            greedyTotal += val
        if remaining <= greedyTotal:
            greedyRounding = self.getRounding(remaining, greedyRegions)
            greedyRemaining = self.updateDistribution(greedyRounding)
            tidyDistribution = self.prettyPrintDistribution()
            self.explanation += f"3. 贪婪线分配完成，最终分配表为{tidyDistribution}, 剩余库存{greedyRemaining}.\n"
            self.isOK(tidyDistribution)
            return tidyDistribution

        # 考虑：这部分可以删去，self.own可满足所有地区需求self.wants
        for val, index, _ in greedyRegions:
            self.distribution[index] = self.distribution.get(index, 0) + val

        total = 0
        for key, val in self.distribution.items():
            total += val
        lastRemaning = self.own - total
        tidyDistribution = self.prettyPrintDistribution()
        self.explanation += f"3. 贪婪线分配完成，最终分配表为{tidyDistribution}，剩余库存{lastRemaning}.\n"
        self.isOK(tidyDistribution)
        return tidyDistribution

    def prettyPrintRegions(self, regions: list[list[int, int, float]]) -> List[int]:
        res = [0] * len(self.wants)
        for val, index, _ in regions:
            res[index] = int(val)
        return res

    def prettyPrintDistribution(self) -> List[int]:
        res = [0] * len(self.wants)
        for index, val in self.distribution.items():
            res[index] = int(val)
        return res

    def prettyPrintRounding(self, rounding: list[list[float, int]]) -> List[float]:
        res = [0] * len(self.wants)
        for proportion, index in rounding:
            res[index] = round(proportion, 4)
        return res

    def isOK(self, tidyDistribution: List[int]):
        for i in range(len(tidyDistribution)):
            want, allocated = self.wants[i], tidyDistribution[i]
            if want > allocated:
                self.ok = False
                return
        self.ok = True
        return


if __name__ == "__main__":
    prepack = 800
    own = 2800
    needs = [-1600, -200, -800, 0, 0, 0, 0]
    wants = [800, 800, 1200, 0, 0, 0, 0]
    s = Solution(needs, wants, prepack, own)
    res = s.getDistribution()
    print(res)
    print(s.explanation)
    print(s.ok)

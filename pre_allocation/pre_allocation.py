import math
from typing import List, Dict


class Solution:
    """
    needs: 各地区温饱线
    wants: 各地区需求声明
    prepack: package unit
    own: 总供应值
    in_transit: in transit运货量: Late, Wn, Wn+1, Wn+2, 分别对应未到量 本周量 下周量 下下周量，[[Wn+1, Late + Wn + Wn+1], [Wn+2, Wn+2]}
    """
    def __init__(self, needs: List[int], wants: List[int], prepack: int, own: int, in_transit: list[list[str, int]]):
        self.needs = needs
        self.wants = wants
        self.prepack = prepack
        self.own = own
        self.in_transit = in_transit

        self.distribution = {}
        self.explanation = ""
        self.ok = True
        self.note = ""

    def sortDyingRegions(self) -> tuple[list[list[int, int, float]], list[list[int, int, float]]]:
        """
        整理dyingRegions并排序，初次整理greedyRegions
        Region形式为[val, index, proportionLimit], 首先计算温饱线时，如果self.own无法满足一个prepack，则不分配温饱线
        """
        dyingRegions = []
        greedyRegions = []
        self.needs = list(map(lambda x: x * -1, self.needs))
        for index, val in enumerate(self.needs):
            if self.wants[index] > 0:
                if val > 0:
                    realNeeds = min(val, self.wants[index])
                    if self.own >= self.prepack:
                        proportionLimit = realNeeds / self.prepack
                        dyingRegions.append([realNeeds, index, proportionLimit])
                    else:
                        dyingRegions.append([realNeeds, index, math.inf])
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
            fl = (round(fl, 10))
        for i in range(len(proportion)):
            proportion[i][0] = int(proportion[i][0])
            if regions[i][2] < proportion[i][0] + 1:
                # regions[i][2] = dyingRegions 或 greedyRegions的proportionLimit
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
        self.own = int(self.own - distributed)
        return self.own

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
            self.addNotes(self.wants, self.own)
            self.explanation += f"1. 没有地区声明需求, 不进行任何分配.\n"
            return [0] * len(self.needs)

        if self.own <= 0:
            tidyDistribution = [0] * len(self.needs)
            shortageList = self.addNotes(tidyDistribution, 0)
            self.explanation += f"1. 当前库存量为0, 不进行任何分配. 未满足分配{shortageList}. in transit={self.in_transit}, 备注为{self.note}\n"
            return tidyDistribution

        if sum(self.wants) <= self.own:
            remaining = self.own - sum(self.wants)
            self.addNotes(self.wants, remaining)
            self.explanation += f"1. prepack={self.prepack}, 库存量={self.own}, 各地区声明需求={self.wants}, 满足分配. 剩余库存{remaining}.\n "
            return self.wants

        # 初次整理温饱线和贪婪线
        dyingRegions, greedyRegions = self.sortDyingRegions()
        tidyDying, tidyGreedy = self.prettyPrintRegions(dyingRegions), self.prettyPrintRegions(greedyRegions)
        self.explanation += f"1. 初次规整，prepack={self.prepack}, 库存量={self.own}, 各地区声明需求={self.wants}, 实际需求={self.needs}, 温饱线={tidyDying}, 当前贪婪线={tidyGreedy}.\n "

        dyingTotal = 0
        for val, _, _ in dyingRegions:
            dyingTotal += val
        if self.own <= dyingTotal:
            # 库存仅能满足温饱线
            rounding = self.getRounding(self.own, dyingRegions)
            remaining = self.updateDistribution(rounding)
            tidyDistribution = self.prettyPrintDistribution()
            shortageList = self.addNotes(tidyDistribution, remaining)
            self.explanation += f"2. 库存量仅能先满足温饱线, 最终分配表为{tidyDistribution}, 未满足分配{shortageList}, 剩余库存{remaining}. in transit={self.in_transit}, 备注为{self.note}\n"
            return tidyDistribution

        rounding = self.getRounding(dyingTotal, dyingRegions)
        remaining = self.updateDistribution(rounding)
        greedyRegions = self.sortGreedyRegions(greedyRegions)
        tidyDistribution = self.prettyPrintDistribution()
        tidyGreedy = self.prettyPrintRegions(greedyRegions)
        self.explanation += f"2. 温饱线分配完成, 当前分配表为{tidyDistribution}, 剩余库存{remaining}，更新贪婪线并进行分配={tidyGreedy}.\n"

        greedyTotal = 0
        for val, _, _ in greedyRegions:
            greedyTotal += val
        if remaining <= greedyTotal:
            greedyRounding = self.getRounding(remaining, greedyRegions)
            greedyRemaining = self.updateDistribution(greedyRounding)
            tidyDistribution = self.prettyPrintDistribution()
            shortageList = self.addNotes(tidyDistribution, greedyRemaining)
            self.explanation += f"3. 贪婪线分配完成, 最终分配表为{tidyDistribution}, 未满足分配{shortageList}, 剩余库存{greedyRemaining}. in transit={self.in_transit}, 备注为{self.note}\n"
            return tidyDistribution

        # 考虑：这部分可以删去，self.own可满足所有地区需求self.wants
        for val, index, _ in greedyRegions:
            self.distribution[index] = self.distribution.get(index, 0) + val

        total = 0
        for key, val in self.distribution.items():
            total += val
        lastRemaining = self.own - total
        tidyDistribution = self.prettyPrintDistribution()
        self.explanation += f"3. 贪婪线分配完成, 最终分配表为{tidyDistribution}, 全部满足分配. 剩余库存{lastRemaining}.\n"
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

    def addNotes(self, tidyDistribution: List[int], remaining: int) -> List[int]:
        shortageList = [0] * len(self.wants)
        for i in range(len(tidyDistribution)):
            want, distributed = self.wants[i], tidyDistribution[i]
            if want > distributed:
                shortageList[i] = want - distributed
        shortage = sum(shortageList)
        if shortage == 0:
            self.note = "ok"
            return shortageList

        self.ok = False
        # 判断下次availability规则：remaining, late, Wn, Wn+1, Wn+2的累加值与本周缺失量进行对比
        # 如果Wn+2前能够cover，则为：av Wn
        # 如果Wn+2!=0，且需要Wn+2的累加值才能cover：如果late=Wn=Wn+1=0，则为：av Wn+2；否则为av Wn+1 / Wn+2
        total_available = remaining
        for idx, (week, amount) in enumerate(self.in_transit):
            if amount == 0:
                continue
            total_available += amount
            if total_available >= shortage:
                if idx == 0:
                    # by the next week
                    self.note = "av " + week + " SG"
                    return shortageList
                if idx == 1:
                    # by the week after next week
                    if total_available == remaining + amount:
                        # late = Wn = Wn+1 = 0
                        self.note = "av " + week + " SG"
                    else:
                        self.note = "av " + self.in_transit[0][0] + " / " + week + " SG"
        return shortageList


if __name__ == "__main__":
    prepack = 440
    own = 100
    needs = [0, 0, -32, 0, 0, 85, 0]
    wants = [0, 0, 2232, 0, 0, 145, 0]

    prepack1 = 400
    own1 = 200
    needs1 = [0, 0, -100, 0, 0, 0, 0]
    wants1 = [0, 0, 400, 0, 0, 0, 0]
    # s = Solution(needs, wants, prepack, own, [["W45", 0], ["W46", 0]])
    s = Solution(needs1, wants1, prepack1, own1, [["W45", 0], ["W46", 200]])
    res = s.getDistribution()
    print(res)
    print(s.explanation)
    print(s.ok)
    print(s.note)

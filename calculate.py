from scipy.optimize import linprog

# 定义目标函数的系数
c = [-10, -12, -7, -2]  # 最大化问题转换为最小化问题，将系数取负

# 定义不等式约束的系数和右侧常数
A = [[4, 5, 3, 1]]
b = [10]

# 定义变量范围
x_bounds = (0, None)  # x1 和 x2 是非负数
binary_bounds = (0, 1)  # x3 和 x4 在 0 和 1 之间

# 变量范围，分别指定 x1, x2 的范围和 x3, x4 的范围
bounds = [x_bounds, x_bounds, binary_bounds, binary_bounds]

# 求解线性规划
result = linprog(c, A_ub=A, b_ub=b, bounds=bounds, method="highs")

# 输出结果
print("最优解：", result.x)
print("最优目标值：", -result.fun)  # 取负，恢复最大化值

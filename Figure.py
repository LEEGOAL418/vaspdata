import pandas as pd
import matplotlib.pyplot as plt


# 读取Excel数据
def read_data(file_path):
    # 读取Excel文件，假设数据在第一个sheet中，没有表头
    data = pd.read_excel(file_path, header=None, names=['Index', 'Concentration', 'AtomCount', 'IonSteps', 'ComputeTime'])
    return data


# 绘制折线图
def plot_data(data):
    plt.figure(figsize=(12, 10))

    # 绘制原子数与浓度的关系
    plt.subplot(3, 1, 1)
    plt.plot(data['Concentration'], data['AtomCount'], marker='o', color='b', linestyle='-', label='原子数')
    plt.title('浓度与原子数的关系')
    plt.xlabel('浓度')
    plt.ylabel('原子数')
    plt.grid(True)
    plt.legend()

    # 绘制离子步数与浓度的关系
    plt.subplot(3, 1, 2)
    plt.plot(data['Concentration'], data['IonSteps'], marker='s', color='g', linestyle='-', label='离子步数')
    plt.title('浓度与离子步数的关系')
    plt.xlabel('浓度')
    plt.ylabel('离子步数')
    plt.grid(True)
    plt.legend()

    # 绘制运算时间与浓度的关系
    plt.subplot(3, 1, 3)
    plt.plot(data['Concentration'], data['ComputeTime'], marker='d', color='r', linestyle='-', label='运算时间 (秒)')
    plt.title('浓度与运算时间的关系')
    plt.xlabel('浓度')
    plt.ylabel('运算时间 (秒)')
    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    plt.show()


# 主程序
if __name__ == "__main__":
    file_path = './AA.xlsx'  # 修改为你的数据文件路径
    data = read_data(file_path)
    plot_data(data)

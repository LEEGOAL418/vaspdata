import Configuration_extract
import Density_extract

# 设置数据源文件夹和输出文件夹路径
AB_folder = './AB'  # 请将此路径改为包含子文件夹的VASP数据源目录
AA_folder = './AA'
debug_folder = './debug'
config_folder = './configurations'  # 请将此路径改为保存输出json文件的目录
density_folder = './density'

# 调用函数处理数据
Configuration_extract.process_vasp_data(AA_folder, config_folder)
Configuration_extract.process_vasp_data(AB_folder, config_folder)
# Configuration_extract.process_vasp_data(debug_folder, config_folder)
# Density_extract.process_and_save_vasp_data(source_folder, density_folder)


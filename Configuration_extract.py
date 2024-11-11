import numpy as np
import os
import json


# 读取并处理XDATCAR文件的函数
def parse_xdatcar(filepath):
    try:
        with open(os.path.join(filepath, 'XDATCAR'), 'r') as file:
            lines = file.readlines()
    except FileNotFoundError:
        print(f"XDATCAR not found in {filepath}.")
        return None

    # 1. 提取晶胎晶矢和原子类型与个数
    lattice_vectors = np.round(np.array([list(map(float, lines[i].split())) for i in range(2, 5)]), decimals=10)
    atom_types = lines[5].split()
    atom_counts = list(map(int, lines[6].split()))
    total_atoms = sum(atom_counts)

    # 2. 提取离子步数和每个离子步的原子坐标
    steps = []
    step_coordinates = []
    for idx, line in enumerate(lines):
        if "Direct configuration=" in line:
            step_index = int(line.split('=')[1].strip())
            steps.append(step_index)
            coordinates = []
            atom_index = 0
            for i in range(1, total_atoms + 1):
                atom_type = atom_types[atom_index // atom_counts[atom_types.index(atom_types[atom_index // sum(atom_counts[:len(atom_types)])])]]
                coords = list(map(float, lines[idx + i].split()))
                cartesian_coords = np.round(np.dot(coords, lattice_vectors), decimals=10).tolist()
                coordinates.append((atom_type, cartesian_coords))
                atom_index += 1
            step_coordinates.append((step_index, coordinates))

    return lattice_vectors, atom_types, atom_counts, steps, step_coordinates


# 从OUTCAR文件中提取能量数据和计算时间的函数
def extract_energies_from_outcar(filepath):
    energies = []
    elapsed_time = None
    outcar_path = os.path.join(filepath, 'OUTCAR')
    if os.path.exists(outcar_path):
        with open(outcar_path, 'r') as file:
            lines = file.readlines()
            # 检查是否包含结束语句
            if not any("General timing and accounting informations for this job:" in line for line in lines):
                folder_name = os.path.basename(os.path.normpath(filepath))
                print(f"{folder_name}未正确运行")
            for line in lines:
                if "energy  without entropy" in line:
                    energy = float(line.split('=')[1].strip().split()[0])
                    energies.append(np.round(energy, 10))
                if "Elapsed time (sec):" in line:
                    elapsed_time = float(line.split(':')[1].strip())
    return energies, elapsed_time


# 将数据保存为 .json 文件
def save_data_as_json(filename, lattice_vectors, atom_types, atom_counts, steps, step_coordinates, energies):
    data = {
        "lattice_vectors": lattice_vectors.tolist(),
        "atom_types": atom_types,
        "atom_counts": atom_counts,
        "steps": steps,
        "step_coordinates": [[step, [[atom, coords] for atom, coords in coordinates]] for step, coordinates in step_coordinates],
        "energies": energies
    }
    with open(filename, 'w') as json_file:
        json.dump(data, json_file, indent=4)


# 遍历数据源文件夹，提取所有子文件夹中的XDATCAR和OUTCAR信息并保存为json文件
def process_vasp_data(source_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for subdir, _, _ in os.walk(source_folder):
        xdatcar_path = os.path.join(subdir, 'XDATCAR')
        outcar_path = os.path.join(subdir, 'OUTCAR')
        if os.path.exists(xdatcar_path) and os.path.exists(outcar_path):
            lattice_vectors, atom_types, atom_counts, steps, step_coordinates = parse_xdatcar(subdir)
            energies, elapsed_time = extract_energies_from_outcar(subdir)

            # 生成保存的json文件名
            subdir_name = os.path.basename(os.path.normpath(subdir))
            output_filename = os.path.join(output_folder, f"{subdir_name}.json")

            # 保存数据为json文件
            save_data_as_json(output_filename, lattice_vectors, atom_types, atom_counts, steps, step_coordinates, energies)

            # 输出已保存的信息
            total_steps = len(energies)  # 总的离子步数等于能量数据的数量
            if elapsed_time is not None:
                print(f"{subdir_name}已保存，共包含{total_steps}个构型，计算时间为{elapsed_time}秒")
            else:
                print(f"{subdir_name}已保存，共包含{total_steps}个构型，但未找到计算时间")

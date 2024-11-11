import numpy as np
import os


def process_and_save_vasp_data(input_directory, output_directory):
    """
    遍历输入目录中的所有子文件夹，提取每个子文件夹中的CHGCAR信息，
    并将提取的数据保存到输出目录中。

    参数：
    - input_directory: 包含VASP数据的源文件夹路径。
    - output_directory: 保存输出npz文件的目标路径。
    """
    # 确保输出目录存在
    os.makedirs(output_directory, exist_ok=True)

    # 遍历输入目录的所有子文件夹
    for root, dirs, files in os.walk(input_directory):
        if 'CHGCAR' in files:
            dataset_name = os.path.basename(root)
            try:
                processor = ChargeDensityProcessor(dataset_name, directory=root)
                processor.save_data(output_directory)
            except Exception as e:
                print(f"Failed to process dataset '{dataset_name}': {e}")


class ChargeDensityProcessor:
    def __init__(self, dataset_name, directory):
        self.dataset_name = dataset_name
        self.directory = directory
        self.file_path = os.path.join(self.directory, 'CHGCAR')
        self.data_dict = {}
        self._read_file()

    def _read_file(self):
        with open(self.file_path, 'r') as file:
            self.lines = file.readlines()
            self._parse_header()
            self._parse_cell_vectors()
            self._parse_atom_info()
            self._parse_grid_info_and_density_data()

    # 标题+缩放系数
    def _parse_header(self):
        try:
            self.data_dict["Title"] = self.lines[0].strip()
            self.data_dict["Scaling Factor"] = float(self.lines[1].strip())
        except (IndexError, ValueError) as e:
            raise ValueError(f"Error parsing header: {e}")

    def _parse_cell_vectors(self):
        try:
            cell_vectors = []
            for i in range(2, 5):
                vector = list(map(float, self.lines[i].strip().split()))
                if len(vector) != 3:
                    raise ValueError(f"Cell vector on line {i + 1} is malformed.")
                cell_vectors.append(vector)
            self.data_dict["Cell Vectors"] = cell_vectors

            # 计算晶胞体积
            a = np.array(cell_vectors[0])
            b = np.array(cell_vectors[1])
            c = np.array(cell_vectors[2])
            scaling_factor = self.data_dict["Scaling Factor"]
            self.data_dict["Volume of the Unit Cell"] = abs(np.dot(a, np.cross(b, c)) * scaling_factor ** 3)
        except (IndexError, ValueError) as e:
            raise ValueError(f"Error parsing cell vectors: {e}")

    def _parse_atom_info(self):
        try:
            # 读取原子类型和数量
            atom_types_line = 5
            atom_counts_line = 6

            self.data_dict["Atom Types"] = self.lines[atom_types_line].strip().split()
            self.data_dict["Atom Counts"] = list(map(int, self.lines[atom_counts_line].strip().split()))

            num_atom_types = len(self.data_dict["Atom Types"])
            num_atom_counts = len(self.data_dict["Atom Counts"])

            if num_atom_types != num_atom_counts:
                raise ValueError("Number of atom types does not match number of atom counts.")

            # 读取坐标类型（Direct或Cartesian）
            coord_type_line = 7
            self.data_dict["Coordinate Type"] = self.lines[coord_type_line].strip().lower()

            if self.data_dict["Coordinate Type"] not in ['direct', 'cartesian']:
                raise ValueError("Coordinate type must be 'Direct' or 'Cartesian'.")

            # 读取原子坐标
            num_atoms = sum(self.data_dict["Atom Counts"])
            coord_start_line = coord_type_line + 1
            coord_end_line = coord_start_line + num_atoms

            atom_coordinates = []
            for i in range(coord_start_line, coord_end_line):
                coordinates = list(map(float, self.lines[i].strip().split()))
                if len(coordinates) < 3:
                    raise ValueError(f"Atom coordinate on line {i + 1} is incomplete.")
                atom_coordinates.append(coordinates[:3])  # 只取前三个坐标值

            # 转换为笛卡尔坐标
            self._convert_to_cartesian(atom_coordinates)

            # 确定下一个部分的起始行
            self.next_section_start_line = coord_end_line
        except (IndexError, ValueError) as e:
            raise ValueError(f"Error parsing atom information: {e}")

    def _convert_to_cartesian(self, atom_coordinates):
        cartesian_coordinates = []
        a, b, c = [np.array(v) for v in self.data_dict["Cell Vectors"]]
        scaling_factor = self.data_dict["Scaling Factor"]
        atom_index = 0
        for atom_type, count in zip(self.data_dict["Atom Types"], self.data_dict["Atom Counts"]):
            for _ in range(count):
                coord = atom_coordinates[atom_index]
                if self.data_dict["Coordinate Type"] == 'direct':
                    cart_coord = (
                                         coord[0] * a + coord[1] * b + coord[2] * c
                                 ) * scaling_factor
                else:
                    cart_coord = np.array(coord) * scaling_factor
                cartesian_coordinates.append({
                    "Atom Type": atom_type,
                    "Coordinates": cart_coord.tolist()
                })
                atom_index += 1
        self.data_dict["Cartesian Coordinates"] = cartesian_coordinates

    def _parse_grid_info_and_density_data(self):
        try:
            # 跳过可能的空行，找到网格信息行
            current_line = self.next_section_start_line
            while self.lines[current_line].strip() == '':
                current_line += 1

            # 读取网格尺寸
            grid_size_line = self.lines[current_line].strip()
            ngx, ngy, ngz = map(int, grid_size_line.split())
            self.data_dict["Grid Info"] = (ngx, ngy, ngz)

            # 读取电子密度数据
            density_data = []
            data_lines_needed = int(np.ceil(ngx * ngy * ngz / 5))  # 每行5个数据，计算需要的行数
            start_data_line = current_line + 1
            end_data_line = start_data_line + data_lines_needed

            for line in self.lines[start_data_line:end_data_line]:
                density_data.extend(map(float, line.strip().split()))

            if len(density_data) != ngx * ngy * ngz:
                raise ValueError("Density data length does not match expected grid size.")

            self.density_array = np.array(density_data).reshape((ngx, ngy, ngz))

            # 计算真实电子密度
            self._calculate_real_density()
        except (IndexError, ValueError) as e:
            raise ValueError(f"Error parsing grid info and density data: {e}")

    def _calculate_real_density(self):
        ngx, ngy, ngz = self.data_dict["Grid Info"]
        volume = self.data_dict["Volume of the Unit Cell"]
        fft_grid_volume = ngx * ngy * ngz
        # 计算真实电子密度: n(r) = data(r) / (Vgrid * Vcell)
        self.data_dict["Real Density Array"] = self.density_array / (fft_grid_volume * volume)

    def save_data(self, output_directory):
        # 创建数据集子目录
        dataset_dir = os.path.join(output_directory, self.dataset_name)
        os.makedirs(dataset_dir, exist_ok=True)

        # 保存数据为 .npz 文件
        save_path = os.path.join(dataset_dir, f'{self.dataset_name}.npz')
        np.savez_compressed(save_path, **self.data_dict)
        print(f"Data saved to {save_path}")


# 示例用法
if __name__ == "__main__":
    input_dir = './DEMO'  # 需要处理的VASP数据源文件夹路径
    output_dir = './DATASET'  # 保存数据的目标路径

    # 处理并保存数据集
    process_and_save_vasp_data(input_dir, output_dir)
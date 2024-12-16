import os
import platform
import sys

# 當前目錄
project_root = os.path.dirname(os.path.realpath(__file__))
# 上一層目錄
parent_dir = os.path.dirname(project_root)
print('當前目錄: ' + project_root)
print('上層目錄: ' + parent_dir)

# 依據不同的系統使用不同的command
system = platform.system()
if system == 'Linux' or system == 'Darwin':  # Darwin 是 Mac OS 的系統名稱
    command = f"{sys.executable} -m pip freeze > {parent_dir}/requirements.txt"
elif system == 'Windows':
    command = f'"{sys.executable}" -m pip freeze > "{parent_dir}\\requirements.txt"'
else:
    raise SystemError(f"Unsupported operating system: {system}")

# 生成requirements的命令
print('執行命令: ' + command)

# 執行command
os.popen(command)    # 路徑有空格可用
import subprocess

# 讀取 requirements.txt，指定編碼為 UTF-16
with open("requirements.txt", "r", encoding="utf-16") as file:
    dependencies = file.readlines()

# 移除空行和註解
dependencies = [dep.strip() for dep in dependencies if dep.strip() and not dep.startswith("#")]

# 使用 Poetry 添加每個依賴
for dependency in dependencies:
    subprocess.run(["poetry", "add", dependency])

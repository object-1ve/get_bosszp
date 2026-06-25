"""从 headers.py 提取 headers 和 cookies 并写入 header.json

Usage:
    python update.py

运行后会自动解析 headers.py 中的 headers 和 cookies 字典，
合并成 session.py 所期望的格式写入 header.json。
"""
import ast
import json
import os

_script_dir = os.path.dirname(__file__)

# 解析 headers.py 的 AST，提取 headers 和 cookies 字典
with open(os.path.join(_script_dir, "headers.py"), encoding="utf-8") as _f:
    _tree = ast.parse(_f.read())

_result = {}
for _node in _tree.body:
    if not isinstance(_node, ast.Assign):
        continue
    for _target in _node.targets:
        if isinstance(_target, ast.Name) and _target.id in ("headers", "cookies"):
            _result[_target.id] = ast.literal_eval(_node.value)

assert "headers" in _result, "headers.py 中未找到 headers 字典"
assert "cookies" in _result, "headers.py 中未找到 cookies 字典"

# 写入 header.json（格式与 session.py 的期望一致）
_output = {"headers": _result["headers"], "_initial_cookies": _result["cookies"]}
_target_path = os.path.join(_script_dir, "header.json")
with open(_target_path, "w", encoding="utf-8") as _f:
    json.dump(_output, _f, ensure_ascii=False, indent=2)

print(f"已从 headers.py 更新 header.json（{len(_output['headers'])} 个请求头，{len(_output['_initial_cookies'])} 个 Cookie）")

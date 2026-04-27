#!/usr/bin/env python3
"""ClawHub 一键发布脚本 — daily-meal-planner

用法:
    python scripts/publish.py                  # 自动递增 patch 版本 (1.0.3 → 1.0.4)
    python scripts/publish.py 1.1.0            # 指定版本号
    python scripts/publish.py --dry-run        # 预演，不实际发布
    python scripts/publish.py --skip-git       # 跳过 git commit & push

流程:
    1. 读取 SKILL.md frontmatter 中的当前版本号
    2. 递增版本（或使用指定版本）
    3. 更新 SKILL.md 中的 version 字段
    4. 临时移走排除文件（README/LICENSE/references/等）
    5. 执行 clawhub publish
    6. 恢复被移走的文件
    7. git commit & push（可跳过）

排除文件列表（不进入 ClawHub 包）:
    - README.md
    - LICENSE
    - .gitignore
    - .clawhubignore
    - references/
    - scripts/user_profile.json
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# ── 配置 ──────────────────────────────────────────────

SKILL_DIR = Path(__file__).resolve().parent.parent
SKILL_MD = SKILL_DIR / "SKILL.md"

# ClawHub 推送时要排除的文件/目录（相对 skill 根目录）
# 规则：非功能文件 + 超限数据文件 + 本脚本自身
EXCLUDE_ITEMS = [
    # 文档/配置（ClawHub 不需要）
    "README.md",
    "LICENSE",
    ".gitignore",
    ".clawhubignore",
    "references",
    # 用户数据（不应打包）
    os.path.join("scripts", "user_profile.json"),
    # 数据文件（超 8K token 限制，运行时从 GitHub 自动下载）
    os.path.join("scripts", "meals_db_compressed.json"),
    os.path.join("scripts", "menu_names_compressed.json"),
    os.path.join("scripts", "meals_tags_index.json"),
    os.path.join("scripts", "tags_index.json"),
    # 本脚本自身（发布工具，非 skill 功能）
    os.path.join("scripts", "publish.py"),
]

# ── 工具函数 ──────────────────────────────────────────

def run(cmd, **kw):
    """运行命令，失败时退出"""
    if isinstance(cmd, list):
        cmd_str = " ".join(cmd)
    else:
        cmd_str = cmd
    print(f"  ▶ {cmd_str}")
    # Windows: 用 shell=True 确保找到 PATH 中的 CLI
    r = subprocess.run(cmd_str, cwd=str(SKILL_DIR), shell=True, **kw)
    if r.returncode != 0:
        print(f"  ✗ 命令失败 (exit {r.returncode})")
        sys.exit(1)
    return r


def read_version():
    """从 SKILL.md frontmatter 读取 version"""
    text = SKILL_MD.read_text(encoding="utf-8")
    m = re.search(r'^version:\s*["\']?([^"\'\s]+)["\']?', text, re.M)
    if not m:
        print("✗ SKILL.md 中未找到 version 字段")
        sys.exit(1)
    return m.group(1)


def bump_version(current: str, level: str = "patch") -> str:
    """递增版本号 (major/minor/patch)"""
    parts = current.split(".")
    if len(parts) != 3:
        print(f"✗ 版本号格式异常: {current}")
        sys.exit(1)
    idx = {"major": 0, "minor": 1, "patch": 2}[level]
    parts[idx] = str(int(parts[idx]) + 1)
    for i in range(idx + 1, 3):
        parts[i] = "0"
    return ".".join(parts)


def write_version(new_ver: str):
    """更新 SKILL.md 中的 version"""
    text = SKILL_MD.read_text(encoding="utf-8")
    text = re.sub(
        r'^(version:\s*["\']?)\S+(["\']?)',
        rf"\g<1>{new_ver}\2",
        text,
        count=1,
        flags=re.M,
    )
    SKILL_MD.write_text(text, encoding="utf-8")
    print(f"  ✓ SKILL.md version → {new_ver}")


def check_token_budget(exclude_items, limit: int = 7500):
    """估算排除后剩余文件 token 数，超过限制时发出警告"""
    total_bytes = 0
    for f in SKILL_DIR.rglob("*"):
        if f.is_file() and ".git" not in f.parts and "__pycache__" not in f.parts:
            rel = f.relative_to(SKILL_DIR)
            # 检查是否在排除列表中
            excluded = any(str(rel) == item or str(rel).startswith(item + os.sep) for item in exclude_items)
            if not excluded:
                total_bytes += f.stat().st_size
    est_tokens = int(total_bytes / 3.5)
    status = "✅" if est_tokens <= limit else "⚠️"
    print(f"  {status} 排除后预估: ~{est_tokens} tokens (限制 {limit})")
    if est_tokens > limit:
        print(f"  ⚠️  可能超出 ClawHub embedding 限制！发布可能失败")
    return est_tokens


def move_out(items, dest: Path):
    """把排除项移到临时目录"""
    moved = []
    for item in items:
        src = SKILL_DIR / item
        if not src.exists():
            continue
        dst = dest / item
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        moved.append(item)
        print(f"  📦 移走: {item}")
    return moved


def move_back(items, dest: Path):
    """从临时目录恢复文件"""
    for item in items:
        src = dest / item
        dst = SKILL_DIR / item
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            print(f"  📂 恢复: {item}")


# ── 主流程 ────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="ClawHub 一键发布 daily-meal-planner")
    parser.add_argument("version", nargs="?", help="指定版本号 (默认自动递增 patch)")
    parser.add_argument("--bump", choices=["major", "minor", "patch"], default="patch",
                        help="递增级别 (默认 patch)")
    parser.add_argument("--dry-run", action="store_true", help="预演模式，不实际发布")
    parser.add_argument("--skip-git", action="store_true", help="跳过 git commit & push")
    args = parser.parse_args()

    # 1. 确定版本号
    current = read_version()
    new_ver = args.version if args.version else bump_version(current, args.bump)
    # 去掉 v 前缀（ClawHub 要求纯 semver）
    new_ver = new_ver.lstrip("v")
    print(f"\n🚀 daily-meal-planner 发布")
    print(f"   当前版本: {current}")
    print(f"   目标版本: {new_ver}\n")

    if args.dry_run:
        print("⚠️  DRY-RUN 模式 — 不会实际修改文件或发布\n")

    # 2. 更新 SKILL.md 版本号
    if not args.dry_run:
        write_version(new_ver)

    # 2.5 预估 token 数（排除后）
    check_token_budget(EXCLUDE_ITEMS)

    # 3. 临时移走排除文件
    tmpdir = Path(tempfile.mkdtemp(prefix="clawhub_pub_"))
    moved = []
    if not args.dry_run:
        moved = move_out(EXCLUDE_ITEMS, tmpdir)

    try:
        # 4. 执行 clawhub publish
        if args.dry_run:
            print(f"  ▶ clawhub publish {SKILL_DIR} --version {new_ver}  (dry-run)")
        else:
            run(["clawhub", "publish", str(SKILL_DIR), "--version", new_ver])
            print(f"\n  ✅ 发布成功: daily-meal-planner@{new_ver}")

    finally:
        # 5. 恢复文件（无论发布成功与否）
        if moved:
            print("\n📂 恢复排除文件...")
            move_back(moved, tmpdir)
        # 清理临时目录
        if tmpdir.exists():
            shutil.rmtree(tmpdir, ignore_errors=True)

    # 6. git commit & push（用 list 模式避免 shell 引号问题）
    if not args.dry_run and not args.skip_git:
        print("\n📤 Git 提交推送...")
        subprocess.run(["git", "add", "-A"], cwd=str(SKILL_DIR))
        r = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=str(SKILL_DIR))
        if r.returncode != 0:
            msg = f"v{new_ver}: publish to ClawHub"
            print(f"  ▶ git commit -m \"{msg}\"")
            subprocess.run(["git", "commit", "-m", msg], cwd=str(SKILL_DIR))
            print(f"  ▶ git push")
            subprocess.run(["git", "push"], cwd=str(SKILL_DIR))
            print(f"  ✅ Git 推送完成")
        else:
            print("  ℹ️ 无文件变更，跳过提交")

    print(f"\n🎉 完成! daily-meal-planner@{new_ver}")


if __name__ == "__main__":
    main()

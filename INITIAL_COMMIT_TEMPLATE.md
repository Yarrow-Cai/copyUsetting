# 初始提交模板

这个仓库已经完成 `git init`，并且没有写入你的姓名、邮箱等个人信息。

## 推荐提交信息模板

可直接使用仓库根目录下的：

- `.gitmessage.txt`

提交命令：

```bash
git add .
git commit -t .gitmessage.txt
```

## 如果你只想提交核心文件

```bash
git add .gitignore backup_config.example.json backup_tool.py build.bat
```

如果还想把原来的命令行脚本一起纳入：

```bash
git add example_config.json file_copier.py run_copier.bat README.md
```

然后执行：

```bash
git commit -t .gitmessage.txt
```

## 建议的首提标题

### 方案 1

```text
feat: initialize devtools backup tool
```

### 方案 2

```text
chore: initialize repository
```

## 当前已避免的内容

- 未执行 `git commit`
- 未写入你的 git 用户名/邮箱
- 已忽略 `backup_config.json` 等本地私有配置
- 已忽略 `build/`、`dist/`、`__pycache__/`、`backup/` 等生成文件

## Setup

```bash
git config core.hooksPath .githooks
```
---

**Cách tạo nhánh:**

```
Mẫu branch: type/short-description
      Type hợp lệ:  feat|fix|docs|style|refactor|test|chore|ci|build
```
---

**Cách commit:**

```
commit-msg  → Mẫu commit: type(scope): message
              Type hợp lệ:  feat|fix|docs|style|refactor|test|chore|ci|build
              Scope hợp lệ: be|fe|db|docs|devops|report|project

pre-commit  → Chặn không cho commit thẳng vào master

pre-push    → Kiểm tra tất cả commit chưa push đều đúng format
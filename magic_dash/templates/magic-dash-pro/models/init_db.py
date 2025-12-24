from models import db
from werkzeug.security import generate_password_hash

# 导入相关数据表模型
from .users import Users
from .departments import Departments
from configs import AuthConfig

# 创建表（如果表不存在）
db.create_tables([Users, Departments])

if __name__ == "__main__":
    # 重置数据库users表，并初始化管理员用户
    # 命令：python -m models.init_db

    # 1. 询问是否重置部门表
    confirm_departments = input(
        "是否重置 \033[93m部门信息\033[0m 表？(输入 \033[93myes\033[0m 确认，其他内容跳过): "
    )
    if confirm_departments == "yes":
        Departments.truncate_departments(execute=True)
        print("\033[93m部门信息\033[0m 表已重置")
    else:
        print("已跳过 \033[93m部门信息\033[0m 表重置")

    print("\n")

    # 2. 询问是否重置用户表
    confirm_users = input(
        "是否重置 \033[93m用户信息\033[0m 表？(输入 \033[93myes\033[0m 确认，其他内容跳过): "
    )
    if confirm_users == "yes":
        Users.truncate_users(execute=True)
        print("\033[93m用户信息\033[0m 表已重置")
        Users.add_user(
            user_id="admin",
            user_name="admin",
            password_hash=generate_password_hash("admin123"),
            user_role=AuthConfig.admin_role,
        )
        print(
            "管理员用户 \033[93madmin\033[0m 初始化完成，初始密码：\033[93madmin123\033[0m"
        )
    else:
        print("已跳过 \033[93m用户信息\033[0m 表重置")

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

    Users.truncate_users(execute=True)
    print("\033[93musers\033[0m 表已重置")
    Users.add_user(
        user_id="admin",
        user_name="admin",
        password_hash=generate_password_hash("admin123"),
        user_role=AuthConfig.admin_role,
    )
    print(
        "管理员用户 \033[93madmin\033[0m 初始化完成，初始密码：\033[93madmin123\033[0m"
    )

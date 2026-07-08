# 内置数据库表名契约
# 不同ORM实现必须映射到同一批物理表，避免切换ORM后读写到不同表
TABLE_NAMES = {
    "Users": "users",
    "Departments": "departments",
    "LoginLogs": "loginlogs",
    "EmailVerifications": "emailverifications",
    "OtpCredentials": "otpcredentials",
    "UserPermissionGroups": "userpermissiongroups",
}

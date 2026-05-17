class InvalidUserError(Exception):
    """非法用户信息"""

    pass


class ExistingUserError(Exception):
    """用户信息已存在"""

    pass


class InvalidDepartmentError(Exception):
    """非法部门信息"""

    pass


class ExistingDepartmentError(Exception):
    """部门信息已存在"""

    pass

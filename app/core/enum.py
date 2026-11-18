import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    CUSTOMER = "customer"
    CHEF = "chef"
    CASHIER = "cashier"
    EMPLOYEE = "employee"

class CartStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"


class ItemStatus(str, enum.Enum):
    AVAILABLE = "available"
    NOT_AVAILABLE = "not available"


class EmployeeStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inActive"


class BranchStatus(str, enum.Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    CONSTRUCTION = "construction"


class LeaveType(str, enum.Enum):
    SICK = "sick"
    SOCIAL = "social"
    RESTRICTED = "restricted"


class LeaveStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class OrderStatus(str, enum.Enum):
    COOKING = "cooking"
    COMPLETED = "completed"


class PaymentStatus(str, enum.Enum):
    SUCCESSFUL = "successful"
    PENDING = "pending"

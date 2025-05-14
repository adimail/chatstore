from google.adk.tools import FunctionTool

from .cart_tools import (
    add_item_to_cart_executor,
    view_cart_executor,
    remove_item_from_cart_executor,
)
from .order_tools import (
    view_orders_executor,
    cancel_order_executor,
    request_return_executor,
    proceed_to_checkout_executor,
)
from .product_tools import get_product_info_executor

from .user_tools import get_user_profile_info_executor


def get_all_adk_tools():
    """
    Returns a list of all FunctionTool instances for the agent.
    The tool's name and description are derived from the function's
    name and docstring, respectively.
    """
    all_tools = [
        FunctionTool(func=add_item_to_cart_executor),
        FunctionTool(func=view_cart_executor),
        FunctionTool(func=remove_item_from_cart_executor),
        FunctionTool(func=view_orders_executor),
        FunctionTool(func=cancel_order_executor),
        FunctionTool(func=request_return_executor),
        FunctionTool(func=proceed_to_checkout_executor),
        FunctionTool(func=get_product_info_executor),
        FunctionTool(func=get_user_profile_info_executor),
    ]
    return all_tools

import frappe

@frappe.whitelist()
def get_paginated_data(start=0, page_length=20):
    start = int(start)
    page_length = int(page_length)
    
    data = frappe.get_list(
        "ToDo",
        fields=["name", "title"],
        order_by="modified desc",
        limit_start=start,
        limit_page_length=page_length,
    )
    return data

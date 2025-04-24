import frappe

def todo_permission_query(user):
    if not user:
        user = frappe.session.user  # Get the current user

    return f"(`tabToDo`.owner = '{user}' OR `tabToDo`.assigned_by = '{user}' OR `tabToDo`.allocated_to = '{user}')"

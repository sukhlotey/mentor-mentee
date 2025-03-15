import frappe

def get_context(context):

    if frappe.session.user == "Guest":
        context.no_cache = 1
        context.redirect_location = "/login"
        return context

    user_roles = frappe.get_roles(frappe.session.user)
    context.user_roles = user_roles

    if "Instructor" not in user_roles:
        context.no_cache = 1
        context.redirect_location = "/login" 
        return context

    context.todos = frappe.get_all(
        "ToDo",
        filters={"owner": frappe.session.user},
        fields=["description", "status", "assigned_by"],
        order_by="creation desc"
    )

    for todo in context.todos:
        todo.assigned_by_name = frappe.get_value("Employee", {"user_id": todo.assigned_by}, "employee_name") or todo.assigned_by

    context.no_cache = 1
    return context

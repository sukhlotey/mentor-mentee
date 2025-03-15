import frappe

def get_context(context):

    if frappe.session.user == "Guest":
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = "/login"
        return context


    user_roles = frappe.get_roles(frappe.session.user)
    context.user_roles = user_roles

    if "HOD" not in user_roles:
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = "/login"
        return context

    hod_employee = frappe.get_value("Employee", {"user_id": frappe.session.user}, ["name", "department", "user_id"])
    if not hod_employee:
        frappe.throw("No Employee record found for this HOD user.")

    hod_department = hod_employee[1]
    hod_employee_id = hod_employee[0]
    hod_user_id = hod_employee[2]

    context.instructors = frappe.get_all(
        "Employee",
        filters={"department": hod_department, "user_id": ["is", "set"], "name": ["!=", hod_employee_id]},
        fields=["name", "employee_name", "department", "user_id"]
    )

    context.csrf_token = frappe.sessions.get_csrf_token()

    if frappe.request.method == "POST":
        try:
            instructor = frappe.form_dict.get("instructor")
            description = frappe.form_dict.get("description")

            if not instructor:
                frappe.throw("Please select an Instructor.")
            if not description:
                frappe.throw("ToDo Description is required.")

            instructor_employee = frappe.get_value("Employee", instructor, ["name", "employee_name", "user_id"])
            if not instructor_employee:
                frappe.throw(f"No Employee record found for Instructor {instructor}")
            
            instructor_user = instructor_employee[2]
            if not instructor_user:
                frappe.throw(f"No user found for Instructor {instructor}")

            todo = frappe.new_doc("ToDo")
            todo.owner = instructor_user
            todo.assigned_by = frappe.session.user
            todo.description = description
            todo.date = frappe.utils.nowdate()
            todo.status = "Open"
            todo.insert(ignore_permissions=True)
            frappe.db.commit()

            saved_todo = frappe.get_doc("ToDo", todo.name)
            if saved_todo.owner != instructor_user:
                frappe.db.set_value("ToDo", todo.name, "owner", instructor_user)
                frappe.db.commit()
                frappe.log_error(f"Fixed ToDo {todo.name} owner to {instructor_user}", "HOD ToDo Fix")

            frappe.local.response["type"] = "redirect"
            frappe.local.response["location"] = "/hod_todo"

        except Exception as e:
            frappe.log_error(f"Error: {str(e)[:50]}", "HOD ToDo Error")
            context.error_message = f"Error creating ToDo: {str(e)}"

    context.todos = frappe.get_all(
        "ToDo",
        filters={"assigned_by": frappe.session.user},
        fields=["name", "owner", "description", "status"],
        order_by="creation desc"
    )

    for todo in context.todos:
        employee = frappe.get_value("Employee", {"user_id": todo.owner}, ["name", "employee_name", "user_id"])
        todo.assigned_to_name = employee[1] if employee and employee[1] else todo.owner
        todo.assigned_to_user = todo.owner

    context.no_cache = 1
    return context

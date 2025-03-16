import frappe

def get_context(context):
    if frappe.session.user == "Guest":
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = "/login"
        return context

    user_roles = frappe.get_roles(frappe.session.user)
    context.user_roles = user_roles
    context.is_hod = "HOD" in user_roles
    context.is_instructor = "Instructor" in user_roles

    if not (context.is_hod or context.is_instructor):
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = "/login"
        return context

    employee = frappe.get_value("Employee", {"user_id": frappe.session.user}, ["name", "department", "user_id"])
    if not employee:
        frappe.throw("No Employee record found for this user.")
    
    context.employee_id = employee[0]
    context.department = employee[1]

    if context.is_hod:
        context.instructors = frappe.get_all(
            "Employee",
            filters={"department": context.department, "user_id": ["is", "set"], "name": ["!=", context.employee_id]},
            fields=["name", "employee_name", "user_id"]
        )
        context.csrf_token = frappe.sessions.get_csrf_token()

    if frappe.request.method == "POST":
        try:
            if context.is_hod and "instructor" in frappe.form_dict:
                instructor = frappe.form_dict.get("instructor")
                description = frappe.form_dict.get("description")
                status = frappe.form_dict.get("status", "Open")

                if not instructor:
                    frappe.throw("Please select an Instructor.")
                if not description:
                    frappe.throw("ToDo Description is required.")
                if status not in ["Open", "Closed", "Cancelled"]:
                    frappe.throw("Invalid Status selected.")

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
                todo.status = status
                todo.insert(ignore_permissions=True)
                frappe.db.commit()

                saved_todo = frappe.get_doc("ToDo", todo.name)
                if saved_todo.owner != instructor_user:
                    frappe.db.set_value("ToDo", todo.name, "owner", instructor_user)
                    frappe.db.commit()

                try:
                    frappe.sendmail(
                        recipients=[instructor_user],
                        subject="New ToDo Assigned",
                        message=f"Dear {instructor_employee[1]},\n\nA new ToDo has been assigned to you by {frappe.session.user}:\n\n{description}\n\nCreated: {saved_todo.creation}\nStatus: {status}\n\nRegards,\nHOD",
                    )
                except Exception as e:
                    frappe.log_error(f"Email failed: {str(e)[:50]}", "ToDo Notification Error")

                frappe.msgprint(f"ToDo assigned to {instructor_employee[1]}!", alert=True)

            elif context.is_hod and "todo_name" in frappe.form_dict and "delete" in frappe.form_dict:  # HOD deleting ToDo
                todo_name = frappe.form_dict.get("todo_name")
                todo = frappe.get_doc("ToDo", todo_name)
                if todo.assigned_by != frappe.session.user:
                    frappe.throw("You can only delete ToDos you assigned.")
                todo.delete()
                frappe.db.commit()
                frappe.msgprint("ToDo deleted successfully!", alert=True)

            frappe.local.response["type"] = "redirect"
            frappe.local.response["location"] = "/todo"

        except Exception as e:
            frappe.log_error(f"Error: {str(e)[:50]}", "ToDo Error")
            context.error_message = f"Error: {str(e)}"

    page = int(frappe.form_dict.get("page", 1)) 
    page_length = 10 
    start = (page - 1) * page_length 

    if context.is_hod:
        context.todos = frappe.get_list(
            "ToDo",
            filters={"assigned_by": frappe.session.user},
            fields=["name", "owner", "description", "status", "creation"],
            order_by="creation desc",
            start=start,
            page_length=page_length
        )
        total_count = frappe.db.count("ToDo", {"assigned_by": frappe.session.user})
    else:  
        context.todos = frappe.get_list(
            "ToDo",
            filters={"owner": frappe.session.user},
            fields=["name", "owner", "description", "status", "creation", "assigned_by"],
            order_by="creation desc",
            start=start,
            page_length=page_length
        )
        total_count = frappe.db.count("ToDo", {"owner": frappe.session.user})

    for todo in context.todos:
        if context.is_hod:
            employee = frappe.get_value("Employee", {"user_id": todo.owner}, ["name", "employee_name", "user_id"])
            todo.assigned_to_name = employee[1] if employee and employee[1] else todo.owner
            todo.assigned_to_user = todo.owner
        else:
            employee = frappe.get_value("Employee", {"user_id": todo.assigned_by}, ["name", "employee_name", "user_id"])
            todo.assigned_by_name = employee[1] if employee and employee[1] else todo.assigned_by
        todo.formatted_creation = frappe.utils.format_datetime(todo.creation, "yyyy-MM-dd HH:mm:ss")

    context.page = page
    context.page_length = page_length
    context.total_count = total_count
    context.total_pages = (total_count + page_length - 1) // page_length

    context.no_cache = 1
    return context

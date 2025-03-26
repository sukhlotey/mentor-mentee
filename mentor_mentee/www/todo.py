import frappe

def get_context(context):
    if frappe.session.user == "Guest":
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = "/login"
        return context

    user_roles = frappe.get_roles(frappe.session.user)
    context.user_roles = user_roles
    context.is_principal = "Principal" in user_roles
    context.is_hod = "HOD" in user_roles
    context.is_instructor = "Instructor" in user_roles
    context.is_student = "Student" in user_roles

    if not (context.is_principal or context.is_hod or context.is_instructor or context.is_student):
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = "/login"
        return context

    # Define all role-specific lists upfront to avoid Undefined in template
    context.hods = []
    context.instructors = []
    context.students = []

    employee = frappe.get_value("Employee", {"user_id": frappe.session.user}, ["name", "department", "user_id"])
    context.employee_id = employee[0] if employee else None
    context.department = employee[1] if employee else None

    if context.is_principal:
        context.hods = frappe.get_all(
            "Employee",
            filters={"user_id": ["is", "set"], "name": ["!=", context.employee_id]},
            fields=["name", "employee_name", "user_id", "department"],
            order_by="department, employee_name"
        )
        context.hods = [hod for hod in context.hods if "HOD" in frappe.get_roles(hod.user_id)]
        context.csrf_token = frappe.sessions.get_csrf_token()
    elif context.is_hod:
        if context.department:
            context.instructors = frappe.get_all(
                "Employee",
                filters={"department": context.department, "name": ["!=", context.employee_id]},
                fields=["name", "employee_name", "user_id"]
            )
        context.csrf_token = frappe.sessions.get_csrf_token()
    elif context.is_instructor:
        instructor = frappe.get_value("Instructor", {"employee": context.employee_id}, "name")
        if not instructor:
            frappe.throw("No Instructor record linked to this Employee.")
        student_group = frappe.get_all(
            "Student Group",
            filters={"instructor": instructor},
            fields=["name"]
        )
        if not student_group:
            frappe.throw("No Student Group assigned to this Instructor.")
        student_group_name = student_group[0].name
        student_ids = frappe.get_all(
            "Student Group Student",
            filters={"parent": student_group_name},
            fields=["student"],
            pluck="student"
        )
        student_emails = frappe.get_all(
            "Student",
            filters={"name": ["in", student_ids]},
            fields=["student_email_id"]
        )
        student_emails = [student["student_email_id"] for student in student_emails if student["student_email_id"]]
        context.students = frappe.get_all(
            "User",
            filters={"name": ["in", student_emails], "enabled": 1},
            fields=["name", "full_name"]
        )
        context.csrf_token = frappe.sessions.get_csrf_token()

    if frappe.request.method == "POST":
        try:
            # New: Update custom_response
            if "update_response" in frappe.form_dict and "todo_name" in frappe.form_dict:
                todo_name = frappe.form_dict.get("todo_name")
                response = frappe.form_dict.get("custom_response")
                todo = frappe.get_doc("ToDo", todo_name)
                if todo.owner != frappe.session.user:
                    frappe.throw("You can only update the response of ToDos assigned to you.")
                if response not in ["Pending", "Completed", ""]:
                    frappe.throw("Invalid Response selected.")
                todo.custom_response = response or None  # Set to None if empty
                todo.save(ignore_permissions=True)
                frappe.db.commit()
                context.message = "Response updated successfully!"
                context.message_type = "success"

            # Delete ToDo (unchanged)
            elif "delete" in frappe.form_dict and "todo_name" in frappe.form_dict:
                if not (context.is_principal or context.is_hod or context.is_instructor):
                    frappe.throw("You do not have permission to delete ToDos.")
                todo_name = frappe.form_dict.get("todo_name")
                todo = frappe.get_doc("ToDo", todo_name)
                if todo.assigned_by != frappe.session.user:
                    frappe.throw("You can only delete ToDos you assigned.")
                todo.delete()
                frappe.db.commit()
                context.message = "ToDo deleted successfully!"
                context.message_type = "success"

            # Edit ToDo (unchanged)
            elif "edit" in frappe.form_dict and "todo_name" in frappe.form_dict:
                if not (context.is_principal or context.is_hod or context.is_instructor):
                    frappe.throw("You do not have permission to edit ToDos.")
                todo_name = frappe.form_dict.get("todo_name")
                todo = frappe.get_doc("ToDo", todo_name)
                if todo.assigned_by != frappe.session.user:
                    frappe.throw("You can only edit ToDos you assigned.")
                
                description = frappe.form_dict.get("description")
                status = frappe.form_dict.get("status")
                assignee = frappe.form_dict.get("assignee")
                original_assignee = frappe.form_dict.get("original_assignee")
                due_date = frappe.form_dict.get("due_date")
                
                frappe.log_error(f"Edit - Todo: {todo_name}, Desc: {description}, Status: {status}, Assignee: {assignee}, Due Date: {due_date}, Original: {original_assignee}", "ToDo Edit Input")

                if not description:
                    frappe.throw("ToDo Description is required.")
                if status not in ["Open", "Closed", "Cancelled"]:
                    frappe.throw("Invalid Status selected.")
                if not assignee:
                    frappe.throw("Please select an assignee.")
                if due_date:
                    try:
                        frappe.utils.getdate(due_date)
                    except ValueError:
                        frappe.throw("Invalid Due Date format. Use YYYY-MM-DD.")

                if context.is_principal:
                    assignee_employee = frappe.get_value("Employee", {"user_id": assignee}, ["name", "employee_name", "user_id"])
                    if not assignee_employee or "HOD" not in frappe.get_roles(assignee_employee[2]):
                        frappe.throw(f"{assignee} is not a valid HOD.")
                    assignee_user = assignee_employee[2]
                    assignee_name = assignee_employee[1]
                elif context.is_hod:
                    assignee_employee = frappe.get_value("Employee", {"user_id": assignee}, ["name", "employee_name", "user_id"])
                    if not assignee_employee:
                        assignee_employee = frappe.get_value("Employee", assignee, ["name", "employee_name", "user_id"])
                        if not assignee_employee:
                            frappe.throw(f"No Employee record found for {assignee}")
                    assignee_user = assignee_employee[2] if assignee_employee[2] else assignee
                    assignee_name = assignee_employee[1]
                    valid_instructor_names = [instr.name for instr in context.instructors]
                    if assignee_employee[0] not in valid_instructor_names:
                        frappe.throw(f"{assignee_name} is not a valid Instructor in your department ({context.department}).")
                else:  # Instructor
                    valid_student_emails = [student.name for student in context.students]
                    if assignee not in valid_student_emails:
                        frappe.throw(f"{assignee} is not a valid Student in your group.")
                    assignee_user = assignee
                    assignee_name = frappe.get_value("User", assignee, "full_name") or assignee

                if assignee_user == frappe.session.user:
                    frappe.throw("Cannot assign ToDo to yourself.")

                frappe.log_error(f"Before - Owner: {todo.owner}, Desc: {todo.description}, Due Date: {todo.date}, Setting to: {assignee_user}, {description}, {due_date}", "ToDo Pre-Update")
                todo.description = description
                todo.status = status
                todo.owner = assignee_user
                if due_date:
                    todo.date = due_date
                try:
                    todo.save(ignore_permissions=True)
                    frappe.log_error(f"After save() - Owner: {todo.owner}, Desc: {todo.description}, Due Date: {todo.date}", "ToDo Post-Save")
                except Exception as e:
                    frappe.log_error(f"Save failed: {str(e)}", "ToDo Save Error")
                
                updated_todo = frappe.get_doc("ToDo", todo_name)
                needs_force_update = False
                if updated_todo.owner != assignee_user or updated_todo.description != description or (due_date and updated_todo.date != due_date):
                    needs_force_update = True
                    frappe.log_error(f"Force updating - Owner: {updated_todo.owner} -> {assignee_user}, Desc: {updated_todo.description} -> {description}, Due Date: {updated_todo.date} -> {due_date}", "ToDo Force Update")
                    update_dict = {"owner": assignee_user, "description": description}
                    if due_date:
                        update_dict["date"] = due_date
                    frappe.db.set_value("ToDo", todo_name, update_dict, update_modified=False)
                    frappe.db.commit()
                
                final_todo = frappe.get_doc("ToDo", todo_name)
                frappe.log_error(f"Final - Owner: {final_todo.owner}, Desc: {final_todo.description}, Due Date: {final_todo.date}", "ToDo Final Check")

                if assignee_user != original_assignee:
                    frappe.log_error(f"Notifying: {assignee_user}", "ToDo Notification")
                    try:
                        frappe.sendmail(
                            recipients=[assignee_user],
                            subject="ToDo Reassigned to You",
                            message=f"Dear {assignee_name},\n\nA ToDo has been reassigned to you by {frappe.session.user}:\n\n{description}\n\nCreated: {todo.creation}\nDue Date: {final_todo.date or 'Not Set'}\nStatus: {status}\n\nRegards,\n{'Principal' if context.is_principal else 'HOD' if context.is_hod else 'Instructor'}",
                        )
                    except Exception as e:
                        frappe.log_error(f"Email failed: {str(e)[:50]}", "ToDo Notification Error")

                context.message = "ToDo updated successfully!"
                context.message_type = "success"

            # Create ToDo (unchanged)
            elif (context.is_principal and "hod" in frappe.form_dict) or \
                 (context.is_hod and "instructor" in frappe.form_dict) or \
                 (context.is_instructor and "student" in frappe.form_dict):
                if context.is_student:
                    frappe.throw("Students cannot assign ToDos.")
                assignee = (frappe.form_dict.get("hod") if context.is_principal else
                           frappe.form_dict.get("instructor") if context.is_hod else
                           frappe.form_dict.get("student"))
                description = frappe.form_dict.get("description")
                status = frappe.form_dict.get("status", "Open")
                due_date = frappe.form_dict.get("due_date")

                if not assignee:
                    frappe.throw("Please select an assignee.")
                if not description:
                    frappe.throw("ToDo Description is required.")
                if status not in ["Open", "Closed", "Cancelled"]:
                    frappe.throw("Invalid Status selected.")
                if due_date:
                    try:
                        frappe.utils.getdate(due_date)
                    except ValueError:
                        frappe.throw("Invalid Due Date format. Use YYYY-MM-DD.")

                if context.is_principal:
                    assignee_employee = frappe.get_value("Employee", {"user_id": assignee}, ["name", "employee_name", "user_id"])
                    if not assignee_employee:
                        frappe.throw(f"No Employee record found for {assignee}")
                    assignee_user = assignee_employee[2]
                    assignee_name = assignee_employee[1]
                elif context.is_hod:
                    assignee_employee = frappe.get_value("Employee", {"user_id": assignee}, ["name", "employee_name", "user_id"])
                    if not assignee_employee:
                        assignee_employee = frappe.get_value("Employee", assignee, ["name", "employee_name", "user_id"])
                        if not assignee_employee:
                            frappe.throw(f"No Employee record found for {assignee}")
                    assignee_user = assignee_employee[2] if assignee_employee[2] else assignee
                    assignee_name = assignee_employee[1]
                    valid_instructor_names = [instr.name for instr in context.instructors]
                    if assignee_employee[0] not in valid_instructor_names:
                        frappe.throw(f"{assignee_name} is not a valid Instructor in your department ({context.department}).")
                else:  # Instructor
                    valid_student_emails = [student.name for student in context.students]
                    if assignee not in valid_student_emails:
                        frappe.throw(f"{assignee} is not a valid Student in your group.")
                    assignee_user = assignee
                    assignee_name = frappe.get_value("User", assignee, "full_name") or assignee

                if not assignee_user:
                    frappe.throw(f"No user found for {assignee}")
                if assignee_user == frappe.session.user:
                    frappe.throw("Cannot assign ToDo to yourself.")

                todo = frappe.new_doc("ToDo")
                todo.owner = assignee_user
                todo.assigned_by = frappe.session.user
                todo.description = description
                todo.status = status
                if due_date:
                    todo.date = due_date
                todo.insert(ignore_permissions=True)
                frappe.db.commit()

                saved_todo = frappe.get_doc("ToDo", todo.name)
                if saved_todo.owner != assignee_user or (due_date and saved_todo.date != due_date):
                    update_dict = {"owner": assignee_user}
                    if due_date:
                        update_dict["date"] = due_date
                    frappe.db.set_value("ToDo", todo.name, update_dict)
                    frappe.db.commit()

                try:
                    frappe.sendmail(
                        recipients=[assignee_user],
                        subject="New ToDo Assigned",
                        message=f"Dear {assignee_name},\n\nA new ToDo has been assigned to you by {frappe.session.user}:\n\n{description}\n\nCreated: {saved_todo.creation}\nDue Date: {saved_todo.date or 'Not Set'}\nStatus: {status}\n\nRegards,\n{'Principal' if context.is_principal else 'HOD' if context.is_hod else 'Instructor'}",
                    )
                except Exception as e:
                    frappe.log_error(f"Email failed: {str(e)[:50]}", "ToDo Notification Error")

                context.message = "ToDo created successfully!"
                context.message_type = "success"

        except Exception as e:
            frappe.log_error(f"Error: {str(e)[:50]}", "ToDo Error")
            context.error_message = f"Error: {str(e)}"
            frappe.redirect("/todo")
            return None

    # Fetch todos with custom_response
    page = int(frappe.form_dict.get("page", 1))
    page_length = 10
    start = (page - 1) * page_length
    search = frappe.form_dict.get("search", "").strip()
    sort_order = frappe.form_dict.get("sort_order", "desc")
    context.sort_order = sort_order
    context.show_principal_todos = frappe.form_dict.get("show_principal_todos", "0") == "1" and context.is_hod
    context.show_hod_todos = frappe.form_dict.get("show_hod_todos", "0") == "1" and context.is_instructor

    if context.is_principal:
        filters = {"assigned_by": frappe.session.user}
    elif context.is_hod:
        filters = {"assigned_by": frappe.session.user} if not context.show_principal_todos else {"owner": frappe.session.user, "assigned_by": ["in", [u.name for u in frappe.get_all("User", filters={"enabled": 1}, fields=["name"]) if "Principal" in frappe.get_roles(u.name)]]}
    elif context.is_instructor:
        filters = {"assigned_by": frappe.session.user} if not context.show_hod_todos else {"owner": frappe.session.user, "assigned_by": ["in", [u.name for u in frappe.get_all("User", filters={"enabled": 1}, fields=["name"]) if "HOD" in frappe.get_roles(u.name)]]}
    else:  # Student
        filters = {"owner": frappe.session.user}

    if search:
        filters["description"] = ["like", f"%{search}%"]

    context.todos = frappe.get_list(
        "ToDo",
        filters=filters,
        fields=["name", "owner", "description", "status", "creation", "assigned_by", "date", "custom_response"],  # Added custom_response
        order_by=f"creation {sort_order}",
        start=start,
        page_length=page_length
    )
    total_count = frappe.db.count("ToDo", filters)

    user_names = {user.name: user.full_name for user in frappe.get_all("User", fields=["name", "full_name"]) if user.full_name}
    for todo in context.todos:
        todo.assigned_to_name = user_names.get(todo.owner, todo.owner)
        todo.assigned_by_name = user_names.get(todo.assigned_by, todo.assigned_by)
        todo.formatted_creation = frappe.utils.format_datetime(todo.creation, "yyyy-MM-dd HH:mm:ss")
        todo.formatted_due_date = frappe.utils.format_date(todo.date, "yyyy-MM-dd") if todo.date else "Not Set"
        todo.custom_response = todo.custom_response or "Not Set"  # Default to "Not Set" if None

    context.page = page
    context.page_length = page_length
    context.total_count = total_count
    context.total_pages = (total_count + page_length - 1) // page_length
    context.search = search

    context.no_cache = 1
    return context

@frappe.whitelist()
def search_todos(search_term, page=1, sort_order="desc"):
    page = int(page)
    page_length = 10
    start = (page - 1) * page_length

    if "Principal" in frappe.get_roles(frappe.session.user):
        filters = {"assigned_by": frappe.session.user}
    elif "HOD" in frappe.get_roles(frappe.session.user):
        show_principal_todos = frappe.form_dict.get("show_principal_todos", "0") == "1"
        if show_principal_todos:
            principal_users = [u.name for u in frappe.get_all("User", filters={"enabled": 1}, fields=["name"]) if "Principal" in frappe.get_roles(u.name)]
            filters = {"owner": frappe.session.user, "assigned_by": ["in", principal_users]}
        else:
            filters = {"assigned_by": frappe.session.user}
    elif "Instructor" in frappe.get_roles(frappe.session.user):
        show_hod_todos = frappe.form_dict.get("show_hod_todos", "0") == "1"
        if show_hod_todos:
            hod_users = [u.name for u in frappe.get_all("User", filters={"enabled": 1}, fields=["name"]) if "HOD" in frappe.get_roles(u.name)]
            filters = {"owner": frappe.session.user, "assigned_by": ["in", hod_users]}
        else:
            filters = {"assigned_by": frappe.session.user}
    elif "Student" in frappe.get_roles(frappe.session.user):
        filters = {"owner": frappe.session.user}
    else:
        filters = {}

    if search_term:
        filters["description"] = ["like", f"%{search_term}%"]

    todos = frappe.get_list(
        "ToDo",
        filters=filters,
        fields=["name", "owner", "description", "status", "creation", "assigned_by", "date", "custom_response"],  # Added custom_response
        order_by=f"creation {sort_order}",
        start=start,
        page_length=page_length
    )
    total_count = frappe.db.count("ToDo", filters)

    result = []
    user_names = {user.name: user.full_name for user in frappe.get_all("User", fields=["name", "full_name"]) if user.full_name}
    for todo in todos:
        todo_dict = {
            "name": todo.name,
            "owner": todo.owner,
            "description": todo.description,
            "status": todo.status,
            "creation": frappe.utils.format_datetime(todo.creation, "yyyy-MM-dd HH:mm:ss"),
            "assigned_by": todo.assigned_by,
            "assigned_to_name": user_names.get(todo.owner, todo.owner),
            "assigned_by_name": user_names.get(todo.assigned_by, todo.assigned_by),
            "due_date": frappe.utils.format_date(todo.date, "yyyy-MM-dd") if todo.date else "Not Set",
            "custom_response": todo.custom_response or "Not Set"  # Added custom_response
        }
        result.append(todo_dict)

    return {
        "todos": result,
        "total_count": total_count,
        "total_pages": (total_count + page_length - 1) // page_length,
        "current_page": page,
        "sort_order": sort_order
    }

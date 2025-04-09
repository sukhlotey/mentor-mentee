import frappe
import json

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

                filters={"department": context.department, "name": ["!=", context.employee_id], "user_id": ["is", "set"]},

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

    elif context.is_student:
        context.csrf_token = frappe.sessions.get_csrf_token()

    if frappe.request.method == "POST":
        try:
            if "update_response" in frappe.form_dict and "todo_name" in frappe.form_dict:

                frappe.log_error(f"Update Response - User: {frappe.session.user}, Todo: {frappe.form_dict.get('todo_name')}, Response: {frappe.form_dict.get('custom_response')}", "Student Response Update Debug")
                todo_name = frappe.form_dict.get("todo_name")
                response = frappe.form_dict.get("custom_response")


                frappe.log_error(f"Update Response - User: {frappe.session.user}, Todo: {frappe.form_dict.get('todo_name')}, Response: {frappe.form_dict.get('custom_response')}", "Student Response Update Debug")

                todo_name = frappe.form_dict.get("todo_name")
                response = frappe.form_dict.get("custom_response")



                if not todo_name:
                    frappe.throw("ToDo name is required.")
                if response is None:
                    frappe.throw("Response value is required.")

                if not frappe.db.exists("ToDo", todo_name):
                    frappe.throw(f"ToDo {todo_name} does not exist.")
                todo = frappe.get_doc("ToDo", todo_name)
                if todo.owner != frappe.session.user:
                    frappe.throw("You can only update the response of ToDos assigned to you.")
                if response not in ["Pending", "Completed", ""]:
                    frappe.throw("Invalid Response selected. Allowed values are 'Pending', 'Completed', or empty.")
                todo.custom_response = response or None



                if not frappe.db.exists("ToDo", todo_name):
                    frappe.throw(f"ToDo {todo_name} does not exist.")

                todo = frappe.get_doc("ToDo", todo_name)


                if todo.owner != frappe.session.user:
                    frappe.throw("You can only update the response of ToDos assigned to you.")


                if response not in ["Pending", "Completed", ""]:
                    frappe.throw("Invalid Response selected. Allowed values are 'Pending', 'Completed', or empty.")


                todo.custom_response = response or None



                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        todo.save(ignore_permissions=True)
                        break
                    except frappe.TimestampMismatchError:
                        if attempt == max_retries - 1:
                            frappe.throw("Failed to update ToDo due to concurrent modifications. Please try again.")
                        todo = frappe.get_doc("ToDo", todo_name, for_update=True)
                        todo.custom_response = response or None

                frappe.db.commit()
                context.message = "Response updated successfully!"
                context.message_type = "success"
            elif "delete" in frappe.form_dict and "todo_name" in frappe.form_dict:
                if not (context.is_principal or context.is_hod or context.is_instructor or context.is_student):


                frappe.db.commit()
                context.message = "Response updated successfully!"
                context.message_type = "success"

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

            elif "edit" in frappe.form_dict and "todo_name" in frappe.form_dict:
                if not (context.is_principal or context.is_hod or context.is_instructor or context.is_student):


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

                priority = frappe.form_dict.get("priority", "Medium")

                
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

                if assignee == frappe.session.user:
                    assignee_user = frappe.session.user
                    assignee_name = frappe.get_value("User", frappe.session.user, "full_name") or frappe.session.user
                elif context.is_principal:


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
                elif context.is_instructor:


                    valid_instructor_names = [instr.name for instr in context.instructors]
                    if assignee_employee[0] not in valid_instructor_names:
                        frappe.throw(f"{assignee_name} is not a valid Instructor in your department ({context.department}).")
                else:  # Instructor

                    valid_student_emails = [student.name for student in context.students]
                    if assignee not in valid_student_emails:
                        frappe.throw(f"{assignee} is not a valid Student in your group.")
                    assignee_user = assignee
                    assignee_name = frappe.get_value("User", assignee, "full_name") or assignee

                elif context.is_student:
                    if assignee != frappe.session.user:
                        frappe.throw("Students can only assign ToDos to themselves.")
                    assignee_user = frappe.session.user
                    assignee_name = frappe.get_value("User", assignee, "full_name") or assignee


                if assignee_user == frappe.session.user:
                    frappe.throw("Cannot assign ToDo to yourself.")


                todo.description = description
                todo.status = status
                todo.owner = assignee_user
                if due_date:
                    todo.date = due_date
                else:

                    todo.date = None
                todo.priority = priority

                    todo.date = None  
                


                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        todo.save(ignore_permissions=True)

                        break
                    except frappe.TimestampMismatchError:
                        if attempt == max_retries - 1:
                            raise
                        todo = frappe.get_doc("ToDo", todo_name, for_update=True)

                        break  # If save succeeds, exit the retry loop
                    except frappe.TimestampMismatchError:
                        if attempt == max_retries - 1:
                            raise  # If max retries reached, re-raise the error

                        todo = frappe.get_doc("ToDo", todo_name, for_update=True)


                        todo.description = description
                        todo.status = status
                        todo.owner = assignee_user
                        if due_date:
                            todo.date = due_date
                        else:
                            todo.date = None

                        todo.priority = priority




                updated_todo = frappe.get_doc("ToDo", todo_name)
                if updated_todo.owner != assignee_user:
                    frappe.db.set_value("ToDo", todo_name, "owner", assignee_user)
                    frappe.db.commit()

                needs_force_update = False
                if updated_todo.description != description or (due_date and updated_todo.date != due_date) or (not due_date and updated_todo.date):
                    needs_force_update = True
                    update_dict = {"description": description, "date": due_date if due_date else None}
                    frappe.db.set_value("ToDo", todo_name, update_dict, update_modified=False)
                    frappe.db.commit()

                if assignee_user != original_assignee:
                    frappe.sendmail(
                        recipients=[assignee_user],
                        subject="ToDo Reassigned to You",

                        message=f"Dear {assignee_name},\n\nA ToDo has been reassigned to you by {frappe.session.user}:\n\n{description}\n\nCreated: {todo.creation}\nDue Date: {due_date or 'Not Set'}\nStatus: {status}\nPriority: {priority}\n\nRegards,\n{'Principal' if context.is_principal else 'HOD' if context.is_hod else 'Instructor' if context.is_instructor else 'Student'}",
                    )
                context.message = "ToDo updated successfully!"
                context.message_type = "success"
            elif "assignees" in frappe.form_dict:
                assignees_json = frappe.form_dict.get("assignees")
                if not assignees_json:
                    frappe.throw("Please select at least one assignee.")
                try:
                    assignees = json.loads(assignees_json)
                except json.JSONDecodeError:
                    frappe.throw("Invalid assignee data format.")
                if not assignees:
                    frappe.throw("Please select at least one assignee.")
                description = frappe.form_dict.get("description")
                status = frappe.form_dict.get("status", "Open")
                due_date = frappe.form_dict.get("due_date")
                priority = frappe.form_dict.get("priority", "Medium")

                        message=f"Dear {assignee_name},\n\nA ToDo has been reassigned to you by {frappe.session.user}:\n\n{description}\n\nCreated: {todo.creation}\nDue Date: {due_date or 'Not Set'}\nStatus: {status}\n\nRegards,\n{'Principal' if context.is_principal else 'HOD' if context.is_hod else 'Instructor'}",
                    )

                context.message = "ToDo updated successfully!"
                context.message_type = "success"

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

                for assignee in assignees:
                    if assignee == frappe.session.user:
                        assignee_user = frappe.session.user
                        assignee_name = frappe.get_value("User", frappe.session.user, "full_name") or frappe.session.user
                    elif context.is_principal:
                        assignee_employee = frappe.get_value("Employee", {"user_id": assignee}, ["name", "employee_name", "user_id"])
                        if not assignee_employee or "HOD" not in frappe.get_roles(assignee_employee[2]):
                            frappe.throw(f"{assignee} is not a valid HOD.")
                        assignee_user = assignee_employee[2]
                        assignee_name = assignee_employee[1]
                    elif context.is_hod:
                        assignee_employee = frappe.get_value("Employee", {"user_id": assignee}, ["name", "employee_name", "user_id"])
                        if not assignee_employee:
                            frappe.throw(f"No Employee record found for {assignee}")
                        assignee_user = assignee_employee[2]
                        assignee_name = assignee_employee[1]
                        valid_instructor_ids = [instr.user_id for instr in context.instructors]
                        if assignee not in valid_instructor_ids:
                            frappe.throw(f"{assignee_name} is not a valid Instructor in your department ({context.department}).")
                    elif context.is_instructor:
                        valid_student_emails = [student.name for student in context.students]
                        if assignee not in valid_student_emails:
                            frappe.throw(f"{assignee} is not a valid Student in your group.")
                        assignee_user = assignee
                        assignee_name = frappe.get_value("User", assignee, "full_name") or assignee
                    elif context.is_student:
                        if assignee != frappe.session.user:
                            frappe.throw("Students can only create ToDos for themselves.")
                        assignee_user = frappe.session.user
                        assignee_name = frappe.get_value("User", assignee, "full_name") or assignee
                    if not assignee_user:
                        frappe.throw(f"No user found for {assignee}")
                    todo = frappe.new_doc("ToDo")
                    todo.owner = assignee_user
                    todo.assigned_by = frappe.session.user
                    todo.description = description
                    todo.status = status
                    if due_date:
                        todo.date = due_date
                    todo.priority = priority
                    todo.insert(ignore_permissions=True)
                    frappe.db.commit()
                    saved_todo = frappe.get_doc("ToDo", todo.name)
                    if saved_todo.owner != assignee_user or (due_date and saved_todo.date != due_date):
                        update_dict = {"owner": assignee_user}
                        if due_date:
                            update_dict["date"] = due_date
                        frappe.db.set_value("ToDo", todo.name, update_dict)
                        frappe.db.commit()
                    if assignee_user != frappe.session.user:  # Only send email if assigned to someone else
                        frappe.sendmail(
                            recipients=[assignee_user],
                            subject="New ToDo Assigned",
                            message=f"Dear {assignee_name},\n\nA new ToDo has been assigned to you by {frappe.session.user}:\n\n{description}\n\nCreated: {todo.creation}\nDue Date: {due_date or 'Not Set'}\nStatus: {status}\nPriority: {priority}\n\nRegards,\n{'Principal' if context.is_principal else 'HOD' if context.is_hod else 'Instructor' if context.is_instructor else 'Student'}",
                        )
                context.message = f"ToDo created successfully for {len(assignees)} user(s)!"
                context.message_type = "success"
        except Exception as e:
            error_message = str(e)[:100] + "..." if len(str(e)) > 100 else str(e)
            frappe.log_error(f"Error: {error_message}", "ToDo Error")
            context.error_message = f"Error: {str(e)}"
            frappe.local.response["type"] = "redirect"
            frappe.local.response["location"] = f"/todo?message={frappe.utils.escape(str(e))}&message_type=danger"
            return None
    context.show_principal_todos = frappe.form_dict.get("show_principal_todos", "0") == "1" and context.is_hod
    context.show_hod_todos = frappe.form_dict.get("show_hod_todos", "0") == "1" and context.is_instructor
    context.show_personal_todos = frappe.form_dict.get("show_personal_todos", "0") == "1" and (context.is_principal or context.is_hod or context.is_instructor or context.is_student)


                if context.is_principal:
                    assignee_employee = frappe.get_value("Employee", {"user_id": assignee}, ["name", "employee_name", "user_id"])
                    if not assignee_employee or "HOD" not in frappe.get_roles(assignee_employee[2]):
                        frappe.throw(f"{assignee} is not a valid HOD.")
                    assignee_user = assignee_employee[2]
                    assignee_name = assignee_employee[1]
                elif context.is_hod:
                    assignee_employee = frappe.get_value("Employee", {"user_id": assignee}, ["name", "employee_name", "user_id"])
                    if not assignee_employee:
                        frappe.throw(f"No Employee record found for {assignee}")
                    assignee_user = assignee_employee[2]
                    assignee_name = assignee_employee[1]
                    valid_instructor_ids = [instr.user_id for instr in context.instructors]
                    if assignee not in valid_instructor_ids:
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

                frappe.sendmail(
                    recipients=[assignee_user],
                    subject="New ToDo Assigned",
                    message=f"Dear {assignee_name},\n\nA new ToDo has been assigned to you by {frappe.session.user}:\n\n{description}\n\nCreated: {todo.creation}\nDue Date: {due_date or 'Not Set'}\nStatus: {status}\n\nRegards,\n{'Principal' if context.is_principal else 'HOD' if context.is_hod else 'Instructor'}",
                )

                context.message = "ToDo created successfully!"
                context.message_type = "success"

        except Exception as e:

            error_message = str(e)[:100] + "..." if len(str(e)) > 100 else str(e)
            frappe.log_error(f"Error: {error_message}", "ToDo Error")
            context.error_message = f"Error: {str(e)}"
            frappe.redirect("/todo")
            return None

    context.show_principal_todos = frappe.form_dict.get("show_principal_todos", "0") == "1" and context.is_hod
    context.show_hod_todos = frappe.form_dict.get("show_hod_todos", "0") == "1" and context.is_instructor

    context.sort_order = frappe.form_dict.get("sort_order", "desc")
    context.search = frappe.form_dict.get("search", "").strip()
    context.page_length = int(frappe.form_dict.get("page_length", 10))
    context.no_cache = 1
    return context

@frappe.whitelist(allow_guest=False)

def get_todo_list(start=0, page_length=10, search="", sort_field="creation", sort_order="desc", filters=None, show_principal_todos="0", show_hod_todos="0", show_personal_todos="0"):

def get_todo_list(start=0, page_length=10, search="", sort_field="creation", sort_order="desc", filters=None, show_principal_todos="0", show_hod_todos="0"):

    start = int(start)
    page_length = int(page_length)
    filters = frappe.parse_json(filters) if filters else {}

    user_roles = frappe.get_roles(frappe.session.user)
    is_principal = "Principal" in user_roles
    is_hod = "HOD" in user_roles
    is_instructor = "Instructor" in user_roles
    is_student = "Student" in user_roles

    if is_principal:

        if show_personal_todos == "1":
            filters["assigned_by"] = frappe.session.user
            filters["owner"] = frappe.session.user
        else:
            filters["assigned_by"] = frappe.session.user
    elif is_hod:
        if show_personal_todos == "1":
            filters["assigned_by"] = frappe.session.user
            filters["owner"] = frappe.session.user
        elif show_principal_todos == "1":

        filters["assigned_by"] = frappe.session.user
    elif is_hod:
        if show_principal_todos == "1":
          
            principal_users = [u.name for u in frappe.get_all("User", filters={"enabled": 1}, fields=["name"]) if "Principal" in frappe.get_roles(u.name)]
            filters["owner"] = frappe.session.user
            filters["assigned_by"] = ["in", principal_users]
        else:
            filters["assigned_by"] = frappe.session.user
    elif is_instructor:

        if show_personal_todos == "1":
            filters["assigned_by"] = frappe.session.user
            filters["owner"] = frappe.session.user
        elif show_hod_todos == "1":

        if show_hod_todos == "1":

            hod_users = [u.name for u in frappe.get_all("User", filters={"enabled": 1}, fields=["name"]) if "HOD" in frappe.get_roles(u.name)]
            filters["owner"] = frappe.session.user
            filters["assigned_by"] = ["in", hod_users]
        else:
            filters["assigned_by"] = frappe.session.user
    elif is_student:

        if show_personal_todos == "1":
            filters["assigned_by"] = frappe.session.user
            filters["owner"] = frappe.session.user
        else:
            filters["owner"] = frappe.session.user

        filters["owner"] = frappe.session.user

    else:
        filters = {}

    if search:
        filters["description"] = ["like", f"%{search}%"]

    todos = frappe.get_list(
        "ToDo",
        filters=filters,

        fields=["name", "owner", "description", "status", "creation", "assigned_by", "date", "custom_response", "modified", "priority"],

        fields=["name", "owner", "description", "status", "creation", "assigned_by", "date", "custom_response", "modified"],

        order_by=f"{sort_field} {sort_order}",
        start=start,
        page_length=page_length + 1
    )
    total_count = frappe.db.count("ToDo", filters)

    user_names = {user.name: user.full_name for user in frappe.get_all("User", fields=["name", "full_name"]) if user.full_name}
    result = []
    has_more = len(todos) > page_length
    if has_more:
        todos.pop()

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
            "due_date": todo.date.strftime("%Y-%m-%d") if todo.date else "",
            "custom_response": todo.custom_response or "Not Set",

            "last_updated": frappe.utils.format_datetime(todo.modified, "yyyy-MM-dd HH:mm:ss"),
            "priority": todo.priority or "Medium"

            "last_updated": frappe.utils.format_datetime(todo.modified, "yyyy-MM-dd HH:mm:ss")

        }
        result.append(todo_dict)

    return {
        "data": result,
        "total_count": total_count,
        "has_more": has_more,
        "start": start,
        "page_length": page_length
    }

@frappe.whitelist(allow_guest=False)
def bulk_update_todos(todo_names, action, value=None):
    todo_names = frappe.parse_json(todo_names) if isinstance(todo_names, str) else todo_names
    if not todo_names:
        frappe.throw("No ToDos selected.")

    user_roles = frappe.get_roles(frappe.session.user)
    is_principal = "Principal" in user_roles
    is_hod = "HOD" in user_roles
    is_instructor = "Instructor" in user_roles

    is_student = "Student" in user_roles

    if not (is_principal or is_hod or is_instructor or is_student):


    if not (is_principal or is_hod or is_instructor):

        frappe.throw("You do not have permission to perform bulk actions on ToDos.")

    for todo_name in todo_names:
        todo = frappe.get_doc("ToDo", todo_name)
        if todo.assigned_by != frappe.session.user:
            frappe.throw(f"You can only perform actions on ToDos you assigned (e.g., {todo_name}).")

        if action == "delete":
            todo.delete()
        elif action == "update_status":
            if value not in ["Open", "Closed", "Cancelled"]:
                frappe.throw("Invalid status value.")
            todo.status = value
            todo.save(ignore_permissions=True)
        elif action == "update_response":
            if value not in ["Pending", "Completed", ""]:
                frappe.throw("Invalid response value.")
            if todo.owner != frappe.session.user:
                frappe.throw(f"You can only update the response of ToDos assigned to you (e.g., {todo_name}).")
            todo.custom_response = value or None
            todo.save(ignore_permissions=True)

    frappe.db.commit()
    return {"message": f"Bulk {action} completed successfully!"}

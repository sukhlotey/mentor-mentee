import frappe

def get_context(context):

    search_query = frappe.form_dict.get("search", "").strip().lower()
    page = int(frappe.form_dict.get("page", 1))
    items_per_page = int(frappe.form_dict.get("items_per_page", 10)) 
    offset = (page - 1) * items_per_page

    instructor_filters = {}
    student_filters = {}

    if search_query:
        instructor_filters["name"] = ["like", f"%{search_query}%"]
        student_filters["student_name"] = ["like", f"%{search_query}%"]

    all_instructors = frappe.get_all("Instructor", fields=["name"], filters=instructor_filters)
    all_students = frappe.get_all("Student", fields=["name", "student_name", "student_email_id", "image"], filters=student_filters)

    for student in all_students:
        guardians = frappe.get_all(
            "Student Guardian",
            filters={"parent": student["name"]},
            fields=["guardian"]
        )
        guardian_names = [
            frappe.get_value("Guardian", g["guardian"], "guardian_name")
            for g in guardians
        ]
        student["guardian_names"] = ", ".join([n for n in guardian_names if n]) if guardian_names else ""
        if student["image"]:
            student["image"] = frappe.utils.get_url(student["image"])
        else:
            student["image"] = ""

    # Fetch email for instructors via Employee and User doctypes
    for instructor in all_instructors:
        employee = frappe.get_value("Instructor", instructor["name"], "employee")  # Assuming 'employee' field
        if employee:
            user_id = frappe.get_value("Employee", employee, "user_id")
            if user_id:
                instructor["instructor_email"] = frappe.get_value("User", user_id, "email") or ""
            else:
                instructor["instructor_email"] = ""
        else:
            instructor["instructor_email"] = ""

    instructors = all_instructors[offset: offset + items_per_page]
    students = all_students[offset: offset + items_per_page]

    total_instructor_records = len(all_instructors)
    total_student_records = len(all_students)
    total_records = max(total_instructor_records, total_student_records)
    total_pages = (total_records + items_per_page - 1) 

    instructor_groups = {}
    for instructor in instructors:
        group_links = frappe.get_all(
            "Student Group Instructor",
            filters={"instructor": instructor["name"]},
            fields=["parent"]
        )
        groups = []
        for link in group_links:
            group_name = link["parent"]
            group = frappe.get_value("Student Group", group_name, ["name", "student_group_name"])
            if group:
                student_names = [
                    frappe.get_value("Student", s["student"], "student_name")
                    for s in frappe.get_all("Student Group Student", filters={"parent": group_name}, fields=["student"])
                ]
                groups.append({"name": group[0], "student_group_name": group[1], "students": student_names})
        instructor_groups[instructor["name"]] = groups

    student_instructors = {}
    for student in students:
        instructors_list = set(
            inst["instructor"]
            for group in frappe.get_all("Student Group Student", filters={"student": student["name"]}, fields=["parent"])
            for inst in frappe.get_all("Student Group Instructor", filters={"parent": group["parent"]}, fields=["instructor"])
        )
        student_instructors[student["name"]] = list(instructors_list)

    context.update({
        "instructors": instructors,
        "students": students,
        "instructor_groups": instructor_groups,
        "student_instructors": student_instructors,
        "current_page": page,
        "total_pages": total_pages,
        "total_records": total_records,
        "search_query": search_query,
        "title": "Mentor Mentee System"
    })

@frappe.whitelist(allow_guest=False)
def search_mentor_mentee(search_query, start=0, items_per_page=10):
    start = int(start)
    items_per_page = int(items_per_page)
    offset = start

    instructor_filters = {}
    student_filters = {}

    if search_query:
        instructor_filters["name"] = ["like", f"%{search_query}%"]
        student_filters["student_name"] = ["like", f"%{search_query}%"]

    all_instructors = frappe.get_all("Instructor", fields=["name"], filters=instructor_filters)
    all_students = frappe.get_all("Student", fields=["name", "student_name", "student_email_id", "image"], filters=student_filters)

    for student in all_students:
        guardians = frappe.get_all(
            "Student Guardian",
            filters={"parent": student["name"]},
            fields=["guardian"]
        )
        guardian_names = [
            frappe.get_value("Guardian", g["guardian"], "guardian_name")
            for g in guardians
        ]
        student["guardian_names"] = ", ".join([n for n in guardian_names if n]) if guardian_names else ""
        if student["image"]:
            student["image"] = frappe.utils.get_url(student["image"])
        else:
            student["image"] = ""

    # Fetch email for instructors via Employee and User doctypes
    for instructor in all_instructors:
        employee = frappe.get_value("Instructor", instructor["name"], "employee")  # Assuming 'employee' field
        if employee:
            user_id = frappe.get_value("Employee", employee, "user_id")
            if user_id:
                instructor["instructor_email"] = frappe.get_value("User", user_id, "email") or ""
            else:
                instructor["instructor_email"] = ""
        else:
            instructor["instructor_email"] = ""

    instructors = all_instructors[offset: offset + items_per_page + 1] 
    students = all_students[offset: offset + items_per_page + 1]

    total_instructor_records = len(all_instructors)
    total_student_records = len(all_students)
    total_records = max(total_instructor_records, total_student_records)

    has_more = len(instructors) > items_per_page or len(students) > items_per_page
    if has_more:
        instructors = instructors[:items_per_page]
        students = students[:items_per_page]

    instructor_groups = {}
    for instructor in instructors:
        group_links = frappe.get_all(
            "Student Group Instructor",
            filters={"instructor": instructor["name"]},
            fields=["parent"]
        )
        groups = []
        for link in group_links:
            group_name = link["parent"]
            group = frappe.get_value("Student Group", group_name, ["name", "student_group_name"])
            if group:
                student_names = [
                    frappe.get_value("Student", s["student"], "student_name")
                    for s in frappe.get_all("Student Group Student", filters={"parent": group_name}, fields=["student"])
                ]
                groups.append({"name": group[0], "student_group_name": group[1], "students": student_names})
        instructor_groups[instructor["name"]] = groups

    student_instructors = {}
    for student in students:
        instructors_list = set(
            inst["instructor"]
            for group in frappe.get_all("Student Group Student", filters={"student": student["name"]}, fields=["parent"])
            for inst in frappe.get_all("Student Group Instructor", filters={"parent": group["parent"]}, fields=["instructor"])
        )
        student_instructors[student["name"]] = list(instructors_list)

    return {
        "instructors": instructors,
        "students": students,
        "instructor_groups": instructor_groups,
        "student_instructors": student_instructors,
        "total_records": total_records,
        "has_more": has_more,
        "start": start,
        "items_per_page": items_per_page,
        "search_query": search_query
    }

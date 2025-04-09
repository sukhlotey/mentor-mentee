import frappe

def get_context(context):
    search_query = frappe.form_dict.get("search", "").strip().lower()
    page = int(frappe.form_dict.get("page", 1))

    items_per_page = 10
    offset = (page - 1) * items_per_page

    instructor_filters = {}
    student_filters = {}

    if search_query:
        instructor_filters["name"] = ["like", f"%{search_query}%"]
        student_filters["student_name"] = ["like", f"%{search_query}%"]

    all_instructors = frappe.get_all("Instructor", fields=["name"], filters=instructor_filters)
    all_students = frappe.get_all("Student", fields=["name", "student_name"], filters=student_filters)

    instructors = all_instructors[offset: offset + items_per_page]
    students = all_students[offset: offset + items_per_page]

    total_records = max(len(all_instructors), len(all_students))
    total_pages = (total_records + items_per_page - 1) // items_per_page

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
        "search_query": search_query,
        "title": "Mentor Mentee System"
    })


@frappe.whitelist(allow_guest=False)
def search_mentor_mentee(search_query, page=1):
    items_per_page = 10
    offset = (int(page) - 1) * items_per_page

    instructor_filters = {}
    student_filters = {}

    if search_query:
        instructor_filters["name"] = ["like", f"%{search_query}%"]
        student_filters["student_name"] = ["like", f"%{search_query}%"]

    all_instructors = frappe.get_all("Instructor", fields=["name"], filters=instructor_filters)
    all_students = frappe.get_all("Student", fields=["name", "student_name"], filters=student_filters)

    instructors = all_instructors[offset: offset + items_per_page]
    students = all_students[offset: offset + items_per_page]

    total_records = max(len(all_instructors), len(all_students))
    total_pages = (total_records + items_per_page - 1) // items_per_page

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
        "current_page": page,
        "total_pages": total_pages,
        "search_query": search_query
    }


import frappe

def get_context(context):

    instructors = frappe.get_all("Instructor", fields=["name"])


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
            

            group = frappe.get_value(
                "Student Group",
                group_name,
                ["name", "student_group_name"]
            )

            if group:

                students = frappe.get_all(
                    "Student Group Student",
                    filters={"parent": group_name},
                    fields=["student"]
                )


                student_names = [
                    frappe.get_value("Student", s["student"], "student_name")
                    for s in students
                ]


                group_data = {
                    "name": group[0],
                    "student_group_name": group[1],
                    "students": student_names
                }
                groups.append(group_data)

        instructor_groups[instructor["name"]] = groups


    context.instructors = instructors
    context.instructor_groups = instructor_groups
    context.title = "Mentor Mentee System"

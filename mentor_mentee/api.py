import frappe

@frappe.whitelist()
def get_instructors():
    instructors = frappe.get_all("Instructor", fields=["name"])
    return instructors

@frappe.whitelist()
def get_student_groups(instructor):
   
    groups = frappe.get_all(
        "Student Group Instructor",
        filters={"instructor_name": instructor},
        fields=["parent"]
    )

   
    group_names = [group["parent"] for group in groups]

   
    if not group_names:
        return {"message": "No student groups assigned to this instructor."}

   
    student_groups = frappe.get_all(
        "Student Group",
        filters={"name": ["in", group_names]},
        fields=["name", "student_group_name"]
    )

   
    for group in student_groups:
        students = frappe.get_all(
            "Student Group Student",
            filters={"parent": group["name"]}, 
            fields=["student", "student_name"]
        )
        group["students"] = students if students else []

    return student_groups

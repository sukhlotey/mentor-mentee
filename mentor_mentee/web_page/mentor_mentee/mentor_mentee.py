import frappe

def get_context(context):
    context.title = "Mentor Mentee Page"
    context.route = "mentor_mentee"
    context.instructors = frappe.get_all("Instructor", fields=["name", "instructor_name"])

@frappe.whitelist()
def get_student_groups(instructor_name):
    groups = frappe.get_all("Student Group", filters={"instructors": {"instructor_name": instructor_name}}, fields=["name", "student_group_name", "instructors", "students"], as_list=True)
    
    result = []
    for group in groups:
        group_doc = frappe.get_doc("Student Group", group[0])
        student_details = []
        
        if group_doc.students:
            for student in group_doc.students:
                student_details.append({
                    "student_name": frappe.get_doc("Student", student.student).student_name
                })

        instructor_name = "No Instructor"
        if group_doc.instructors and len(group_doc.instructors) > 0:
            instructor_name = group_doc.instructors[0].instructor_name.instructor_name

        result.append({
            "student_group_name": group[1],
            "students": student_details,
            "instructor_name": instructor_name
        })

    return result

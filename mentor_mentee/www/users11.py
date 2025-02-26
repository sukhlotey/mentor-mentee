import frappe

def get_context(context):
    # Fetch all enabled users
    users = frappe.get_all(
        "User",
        filters={"enabled": 1},
        fields=["name as full_name", "email", "role_profile_name as role"]
    )

    # Pass data to the template
    context.users = users
    context.title = "User List"

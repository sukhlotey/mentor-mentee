frappe.ready(function() {
  $(".instructor-item").click(function () {
    let instructorName = $(this).data("instructor");
    $("#groups-list").html("");

    frappe.call({
      method: "mentor_mentee.web_page.mentor_mentee.get_student_groups",
      args: { instructor_name: instructorName },
      callback: function(r) {
        if (r.message && r.message.length > 0) {
          r.message.forEach(group => {
            let studentNames = group.students.map(s => s.student_name).join(", ");
            $("#groups-list").append(`
              <div class="card mt-3">
                <div class="card-header bg-primary text-white">${group.student_group_name}</div>
                <div class="card-body">
                  <p><strong>Instructor:</strong> ${group.instructor_name}</p>
                  <p><strong>Students:</strong> ${studentNames || "No student assigned."}</p>
                </div>
              </div>
            `);
          });
        } else {
          $("#groups-list").html("<div class='alert alert-warning mt-3'>No student groups available.</div>");
        }
      }
    });
  });
});

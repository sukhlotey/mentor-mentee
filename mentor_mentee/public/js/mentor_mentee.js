$(document).ready(function () {

    $(document).on("click", ".instructor-item", function () {
        let instructorName = $(this).data("instructor") || "Unknown Instructor";
        console.log("Instructor clicked:", instructorName);

        $("#groups-list").html("<div class='alert alert-info'>Loading student groups...</div>");

        $.get(`${BASE_URL}/api/resource/Student Group`, function (groupData) {
            console.log("Student Groups API Response:", groupData);

            $("#groups-list").empty();

            if (!groupData.message || !Array.isArray(groupData.message) || groupData.message.length === 0) {
                $("#groups-list").html("<div class='alert alert-warning mt-3'>No student groups assigned.</div>");
                return;
            }

            groupData.message.forEach(group => {
                $.get(`${BASE_URL}/api/resource/Student Group/${group.name}`, function (groupDetail) {
                    console.log("Student Group Details:", groupDetail);

                    let instructor = groupDetail.message?.instructors?.[0]?.instructor_name || "No Instructor";
                    console.log(`Instructor for ${groupDetail.message.student_group_name}:`, instructor);

                    if (instructor === instructorName) {
                        let studentFetchCount = 0;
                        let studentNames = [];
                        if (groupDetail.message.students.length === 0) {
                            $("#groups-list").append(`
                                <div class="card mt-3">
                                    <div class="card-header bg-primary text-white">${groupDetail.message.student_group_name}</div>
                                    <div class="card-body">
                                        <p><strong>Instructor:</strong> ${instructor}</p>
                                        <p><strong>Students:</strong> No students assigned.</p>
                                    </div>
                                </div>
                            `);
                        } else {
                            // Fetch student details and store names
                            Promise.all(groupDetail.message.students.map(s =>
                                $.get(`${BASE_URL}/api/resource/Student/${s.student}`)
                                    .then(studentData => {
                                        console.log("Student Data Response:", studentData);
                                        if (studentData.message && studentData.message.student_name) {
                                            return studentData.message.student_name;
                                        } else {
                                            return "Unknown Student";
                                        }
                                    })
                                    .catch(err => {
                                        console.error("Error fetching student details:", err);
                                        return "Error Fetching Student";
                                    })
                            )).then(studentNames => {
                               
                                $("#groups-list").append(`
                                    <div class="card mt-3">
                                        <div class="card-header bg-primary text-white">${groupDetail.message.student_group_name}</div>
                                        <div class="card-body">
                                            <p><strong>Instructor:</strong> ${instructor}</p>
                                            <p><strong>Students:</strong> ${studentNames.join(", ")}</p>
                                        </div>
                                    </div>
                                `);
                            });
                        }
                    }
                }).fail(function (err) {
                    console.error(" Error fetching group details:", err);
                });
            });
        }).fail(function (err) {
            console.error("Error fetching student groups:", err);
            $("#groups-list").html("<div class='alert alert-danger'>Failed to load student groups.</div>");
        });
    });
});

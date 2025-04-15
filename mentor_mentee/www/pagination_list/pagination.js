let currentPage = 1;
let pageSize = 20;  // Default

function fetchToDos() {
    frappe.call({
        method: "your_app.www.paginated_list.get_paginated_data",
        args: {
            start: (currentPage - 1) * pageSize,
            page_length: pageSize
        },
        callback: function(response) {
            let todos = response.message || [];
            let todoList = document.getElementById("todo-list");
            todoList.innerHTML = todos.map(todo => `<p>${todo.name} - ${todo.title}</p>`).join("");
            document.getElementById("page-info").innerText = `Page ${currentPage}`;
        }
    });
}

// Handle pagination buttons
document.getElementById("prev-btn").addEventListener("click", function() {
    if (currentPage > 1) {
        currentPage--;
        fetchToDos();
    }
});
document.getElementById("next-btn").addEventListener("click", function() {
    currentPage++;
    fetchToDos();
});

// Handle page size selection
document.querySelectorAll(".page-size-btn").forEach(button => {
    button.addEventListener("click", function() {
        pageSize = parseInt(this.getAttribute("data-size"));
        currentPage = 1;  // Reset to first page
        fetchToDos();
    });
});

// Initial Load
fetchToDos();

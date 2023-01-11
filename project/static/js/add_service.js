$(document).ready(function () {
    date_to_search = $("#date_to_search");

    today = new Date().toISOString().substr(0, 10);
    date_to_search.value = today;

    warning_area = $("#warning_area");
    success_area = $("#success_area");

    $("#async-form").submit(function (event) {
        event.preventDefault();

        warning_area.hide();
        success_area.html("<div>Service ajouté :</div>");
        success_area.hide();
        $("#submit_button").addClass("is-loading");

        $.post(
            //url
            "/request_service/",
            //data
            {
                date_to_search: date_to_search.val(),
            },
        )
        .done(
            //callback function
            function (response) {

                console.log(response);  // You can use the console to look at the response object

                if (response.created_service.length > 0) {
                    success_area.show();
                    div_el = $(document.createElement("div"));
                    div_el.append(response.created_service);
                    success_area.append(div_el);
                }
                else {
                    warning_area.show();
                    warning_area.text(
                        `Pas de service à cette date !`
                    );
                }
            }
        )
        .fail(
            // Error handling
            function (xhr, status, error) {
                console.log(xhr);
                warning_area.show();
                warning_area.html(xhr.responseText)
            }
        )
        .always(
            // Cleanup process
            function () {
                $("#submit_button").removeClass("is-loading");
            }
        )
    });
});

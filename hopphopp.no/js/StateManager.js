/*
STATES:

0: Default:. "Home view". Shows select stuff + welcome info.
1: Pick-country: User needs to pick a country. Shows "cards".
2: Month-view: "Calendar view". Shows prices for a month, for specific location.
3: (TODO) Details-view: Show LIVE prices for specific to/from date
*/


function setState(new_state, data) {

    // If new_state and current_state are same, do NOTHING!
    if (new_state == current_state) {
        return "New state same as current state. Did NOTHING!"
    }

    // Disable current state.
    if (current_state == '0') {
        // Hide elements.
        $("#card-spinner").hide();
        $("#select-container").hide();
        $("#welcome-container").hide();
    }
    if (current_state == '1') {
        // Hide elements.
        $("#card-spinner").hide();
        $("#mini-select-container").hide();
        $("#mini-month-div").hide();
        $("#nano-container").hide();
        $("#card-container").hide();
    }
    if (current_state == '2') {
        // Hide elements.
        $("#mini-select-container").hide();
        $("#mini-to-div").hide();
        $("#calendar-container").hide();

    }
    if (current_state == '3') {
        // Not implemented/required...
    }

    // Enable new state.
    if (new_state == '0') {
        // Init variables and elements.
        var prev_to = "Anywhere";
        $("#alt_to").val("Anywhere");
        var dp = $("#datepicker1").datepicker(dp_opts);
        // Show elements.
        $("#select-container").show();
        $("#welcome-container").show();
        $("#text_from").easyAutocomplete(opt_from);
        $("#text_to").easyAutocomplete(opt_to);

        current_state = '0';
        return "Set state 0."
    }
    if (new_state == '1') {
        // Init variables and elements.
        $("#mini-from").html(data['from']);
        $("#mini-month").html(data['date']);
        // Show elements.
        $("#mini-select-container").show();
        $("#mini-month-div").show();
        $("#nano-container").show();
        $("#card-container").show();

        $(".nano").nanoScroller();
        current_state = '1';
        return "Set state 1."
    }
    if (new_state == '2') {
        // Init variables and elements.
        $("#mini-from").html(data['from']);
        $("#mini-to").show().html(data['to']);
        // Show elements.
        $("#mini-select-container").show();
        $("#mini-to-div").show();
        $("#calendar-container").show();
        $('#calendar').fullCalendar(calopts);
        $('#calendar').fullCalendar('gotoDate', data['date']);

        current_state = '2';
        return "Set state 2."
    }
    if (new_state == '3') {
        // Init variables and elements.
        // Show elements.

        current_state = '3';
        return "Set state 3."
    }

}

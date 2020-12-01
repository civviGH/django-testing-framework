$(document).ready(function() {

    $("input[name='filter_status']").change(function () {
        var status_type = this.value;
        var checked = this.checked;
        $('table > tbody > tr > td > span').each(function(index, elem) {
            if (elem.textContent != status_type){
                return;
            }
            if (checked) {
                elem.parentElement.parentElement.style.display = "table-row";
            }
            else {
                elem.parentElement.parentElement.style.display = "none";
            }
        });
    });

    $(".tablesorter").tablesorter();
});
$(document).ready(function() {
    $(".tablesorter").tablesorter();
});
    
    // sorting functionality used:
    // https://stackoverflow.com/questions/3160277/jquery-table-sort

    
/*     $('th').click(function(){
        var table = $(this).parents('table').eq(0)
        var rows = table.find('tr:gt(0)').toArray().sort(comparer($(this).index()))
        this.asc = !this.asc
        // remove the sorting icon from all th, so its clear which one is current
        $("i").each(function(){
            $(this).removeClass("fa-sort-desc");
            $(this).removeClass("fa-sort-asc");
        });
        // at this point we know wether we are sorting ascending or descending
        // so we can add the correct icon class to the i element in the th
        var sort_icon = $(this).children("i");
        if (this.asc) {
            sort_icon.addClass("fa-sort-asc");
            sort_icon.removeClass("fa-sort-desc");
        } else {
            sort_icon.removeClass("fa-sort-asc");
            sort_icon.addClass("fa-sort-desc");
        }
        if (!this.asc){rows = rows.reverse()}
        for (var i = 0; i < rows.length; i++){table.append(rows[i])}
    })

});

function comparer(index) {
    return function(a, b) {
        var valA = getCellValue(a, index), valB = getCellValue(b, index)
        return $.isNumeric(valA) && $.isNumeric(valB) ? valA - valB : valA.toString().localeCompare(valB)
    }
}

function getCellValue(row, index){ return $(row).children('td').eq(index).text() } */

function renderTestResultValueData(value) {
    if(value === undefined || value === null) {
        return "N/A";
    }
    if(value.type === 'string') {
        return value.data;
    }
    else if(value.type === 'integer') {
        return value.data;
    }
    else if(value.type === 'float') {
        return value.data;
    }
    else if(value.type === 'duration') {
        return printISO8601Duration(parseISO8601Duration(value.data));
    }
    else if(value.type === 'list') {
        // backward-compatibility. New data should use 'ndarray'
        // TODO: implement this
        return value.data;
    }
    else if(value.type === 'ndarray') {
        const shape = value.data.shape;
        const entries = value.data.entries.map(entry => renderTestResultValueData(entry));

        const tensorOrder = shape.length;
        const totalCount = shape.reduce((accumulator, currentValue) => accumulator + currentValue);

        const inconsistent = totalCount != entries.length;

        var out = [];

        if(inconsistent || tensorOrder > 3) {
            // Just print a 1D list of all available values
            var size0 = len(entries)
            var size1 = 1
            var size2 = 1
            const shapeStr = shape.join(',');
            out.push(`Tensor-${tensorOrder} [${shapeStr}]:`);
        }
        else {
            var size0 = tensorOrder >= 1 ? shape[0] : 1;
            var size1 = tensorOrder >= 2 ? shape[1] : 1;
            var size2 = tensorOrder >= 3 ? shape[2] : 1;
        }

        for(let k = 0; k < size2; k++) {
            var currentTable = $('<table>').addClass('ndarray-value');
            for(let i = 0; i < size0; i++) {
                var currentRow = $('<tr>');
                for(let j = 0; j < size1; j++) {
                    const index = k*(size0*size1)+i*size1+j;
                    currentRow.append($('<td>').append(entries[index]))
                }
                currentTable.append(currentRow)
            }
            out.push(currentTable);
        }
        return out;
    }
    else if(value.type === 'image') {
        return $('<img>')
            .attr('src', `data:image/png;base64, ${value.data}`)
    }
    else {
        return value.data;
    }
}

function renderTestResultValue(project_slug, value, source) {
    valueHtml = renderTestResultValueData(value)

    if(source === undefined || source === null) {
        return valueHtml;
    }
    else {
        return $('<a>')
            .attr('href', `/${project_slug}/tests/${source}`)
            .append(valueHtml);
    }
}

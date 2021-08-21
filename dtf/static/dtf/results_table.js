
function buildResultsTable(projectSlug, testId, results, references, canUpdate) {
    let tableBody = $("#resultsTable").find('tbody');

    results.forEach(function (result, resultIndex) {

        let reference = references[result['name']];
        if(reference === undefined || reference === null) {
            reference = {value: null, source: null};
        }

        let row = $('<tr>')
            .attr('class', 'filtered-row')
            .attr('test-result-index', resultIndex)
            .append($('<td>')
                .attr('class', 'filter-status')
                .append(renderStatusBadge(result['status']))
            )
            .append($('<td>')
                .append($('<div>')
                    .attr('class', 'd-flex')
                    .append($('<span>')
                        .text(result['name'])
                    )
                    .append($('<div>')
                        .attr('class', 'ms-auto')
                        .append($('<a>')
                            .attr('class', 'btn btn-outline-dark dtf-btn-xs me-1')
                            .attr('href', `/${projectSlug}/tests/${testId}/history?measurement_name=${result['name']}`)
                            .append($('<i>')
                                .attr('class', 'bi bi-graph-up')
                            )
                        )
                    )
                )
            )
            .append($('<td>')
                .attr('id', 'tableDataValue')
                .append(renderTestResultValue(projectSlug, result['value'], null))
            )
            .append($('<td>')
                .attr('id', 'tableDataReferenceOnSubmission')
                .append(renderTestResultValue(projectSlug, result['reference'], result['reference_source']))
            )
            .append($('<td>')
                .attr('id', 'tableDataGlobalReference')
                .append(renderTestResultValue(projectSlug, reference['value'], reference['source']))
            )
        if(canUpdate) {
            row.append($('<td>')
                .append($('<input>')
                    .attr('id', 'updateReferenceCheckbox')
                    .attr('class', 'form-check-input ms-2 me-2')
                    .attr('type', 'checkbox')
                    .attr('autocomplete', 'off')
                )
            )
        }
        tableBody.append(row);
    });
}

function updateResultsTableReferences(projectSlug, testResults, references) {
    let resultsRows = $('#resultsTable > tbody > tr');

    resultsRows.each(function(index, tr) {
        const testResultIndex = tr.getAttribute('test-result-index');
        const testResult = testResults[testResultIndex];
        let reference = references[testResult['name']];
        if(reference === undefined || reference === null) {
            reference = {value: null, source: null};
        }

        let globalReferenceData = $(tr).find('#tableDataGlobalReference').first();

        globalReferenceData.empty();
        globalReferenceData.append(renderTestResultValue(projectSlug, reference['value'], reference['source']));
    });
}

function toggleAllBoxes(){
    let toggleAllBox = $('#toggleAllReferencesCheckbox')[0];
    let allBoxes = $('[id=updateReferenceCheckbox]');
    for (var i = 0; i < allBoxes.length; i++) {
        if (allBoxes[i].parentElement.parentElement.style.display == "none") {
            continue;
        }
        allBoxes[i].checked = toggleAllBox.checked;
    }
}

function uncheckAllBoxes(){
    let toggleAllBox = $('#toggleAllReferencesCheckbox')[0];
    toggleAllBox.checked = false;
    let allBoxes = $('[id=updateReferenceCheckbox]');
    for (var i = 0; i < allBoxes.length; i++) {
        allBoxes[i].checked = false;
    }
}

function postReferenceUpdate(csrfToken, testName, testId, testResults, referenceSetId, testReferenceId, projectSlug){
    let data = {
        "test_name": testName,
        "default_source": testId,
        "references": {
        }
    }

    let resultsRows = $('#resultsTable > tbody > tr');

    resultsRows.each(function(index, tr) {
        let checkBox = $(tr).find('#updateReferenceCheckbox')[0];
        if(checkBox.checked) {
            const testResultIndex = tr.getAttribute('test-result-index');
            const testResult = testResults[testResultIndex];
            data["references"][testResult['name']]= {
                "value": testResult['value']
            };
        }
    });

    if (testReferenceId === null) {
        var url = `/api/projects/${projectSlug}/references/${referenceSetId}/tests`;
        var method = "POST";
    }
    else {
        var url = `/api/projects/${projectSlug}/references/${referenceSetId}/tests/${testReferenceId}`;
        var method = "PATCH";
    }
    
    let updatedCount = Object.keys(data["references"]).length;

    $.ajax({
        beforeSend: function(xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", csrfToken);
        },
        type: method,
        contentType: "application/json; charset=utf-8",
        url: url,
        data: JSON.stringify(data),
        success: function(result) {
            $.toast({
                type: 'success',
                content: `Successfully updated ${updatedCount} references.`
            });
            updateResultsTableReferences(projectSlug, testResults, result['references']);
            uncheckAllBoxes();
        },
        error: function(result) {
            $.toast({
                type: 'danger',
                content: `Failed to update ${updatedCount} references.`
            });
            console.log(result);
        }
    });
}

function updateReferences(csrfToken, testName, testId, testResults, propertyValues, referenceSetId, testReferenceId, projectSlug) {
    if(referenceSetId === null) {
        var data = {
            "property_values" : propertyValues
        };
        $.ajax({
            beforeSend: function(xhr, settings) {
                xhr.setRequestHeader("X-CSRFToken", csrfToken);
            },
            type: 'POST',
            contentType: "application/json; charset=utf-8",
            url: `/api/projects/${projectSlug}/references`,
            data: JSON.stringify(data),
            success: function(result) {
                postReferenceUpdate(csrfToken, testName, testId, testResults, result.id, null, projectSlug);
            },
            error: function(result) {
                $.toast({
                    type: 'danger',
                    content: `Failed to create reference set.`
                });
                console.log(result);
            }
        });
    }
    else {
        postReferenceUpdate(csrfToken, testName, testId, testResults, referenceSetId, testReferenceId, projectSlug)
    }
}

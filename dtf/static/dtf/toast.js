(function ($) {
    let nextToastId = 1;

    $.toast = function (options) {
        let container = $('.toast-container');
        if(container.Length == 0) {
            return;
        }

        const type    = options.type;
        const content = options.content;

        let id = `toast-${nextToastId}`;
        nextToastId++;

        let html = '';
        html = `<div id="${id}" class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">`;
        html += `<div class="d-flex">
                    <div class="toast-body">
                        ${content}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>`;
        html += `</div>`;

        container.append(html);
        let toast = container.find('.toast:last')

        toast.toast('show');
        container.on('hidden.bs.toast', '.toast', function () {
            $(this).remove();
        });
    }
}(jQuery));
(function() {
    var opts = {
        formsetPrefix: "id_{{ self.formset.prefix }}",
        emptyChildFormPrefix: "{{ self.empty_child.form.prefix }}",
        canOrder: {% if can_order %}true{% else %}false{% endif %},
        maxForms: {{ self.formset.max_num }}
    };
    var panel = InlinePanel(opts);

    {% for child in self.children %}
        panel.initChildControls("{{ child.form.prefix }}");
    {% endfor %}
    panel.updateAddButtonState = function() {
        if (opts.maxForms) {
            var forms = panel.formsUl.children('li:visible');
            var addButton = $('#' + opts.formsetPrefix + '-ADD');

            if (forms.length >= opts.maxForms) {
                addButton.hide();
            } else {
                addButton.show();
            }
        }
    };
    panel.setHasContent();
    panel.updateMoveButtonDisabledStates();
    panel.updateAddButtonState();
})();

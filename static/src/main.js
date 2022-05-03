/** Add extra data to a form before it's submitted */
function addDataToForm(formId, data) {
    // From https://stackoverflow.com/a/53366001
    const form = document.getElementById(formId);

    for (const name in data) {
        // Delete previous elements with same id
        for (const prevInput of form.elements) {
            if (prevInput.name == name) {
                prevInput.parentNode.removeChild(prevInput);
            }
        }

        const input = document.createElement("input");
        input.setAttribute("id", name);
        input.setAttribute("name", name);
        input.setAttribute("value", data[name]);
        input.setAttribute("type", "hidden");
        form.appendChild(input);
    }

    return form;
}

/** Send a post request */
function postRequest(url, data) {
    return fetch(url, {
        method: "POST",
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    })
}

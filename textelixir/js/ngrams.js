// copy to clipboard
const copy = (text) => {
    navigator.clipboard.writeText(text);
}

// copy All
let contents = []
let copyBtn = document.querySelector('#copy_btn');
copyBtn.addEventListener('click', function () {
    window.getSelection().removeAllRanges();
    let urlField = document.querySelector('table');
        
    // create a Range object
    let range = document.createRange();  
    // set the Node to select the "range"
    range.selectNode(urlField);
    // add the Range to the set of window selections
    window.getSelection().addRange(range);
        
    // execute 'copy', can't 'cut' in this case
    document.execCommand('copy');
}, false);

